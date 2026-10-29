"""
RAG diet pipeline: user health input -> retrieval queries -> guideline passages -> Groq LLM -> diet blueprint.
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

from groq import BadRequestError, RateLimitError

from .config import SELF_RAG_CRITIC, SELF_RAG_MAX_RETRIES
from .critic import SUPPORT_LEVELS, critique, needs_regeneration
from .retriever import get_retriever

logger = logging.getLogger(__name__)

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = os.environ.get("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
MAX_CONTEXT_CHARS = 9000


# =========================
# QUERY CONSTRUCTION
# =========================
def _bmi_category(bmi: Optional[float]) -> Optional[str]:
    # Asian-Indian cut-offs used by ICMR-NIN
    if not bmi:
        return None
    if bmi < 18.5:
        return "underweight"
    if bmi < 23:
        return "normal weight"
    if bmi < 25:
        return "overweight"
    return "obese"


def _parse_bp(bp: Optional[str]):
    try:
        systolic, diastolic = str(bp).split("/")
        return int(float(systolic)), int(float(diastolic))
    except (ValueError, AttributeError):
        return None, None


def build_queries(health_data: Dict, prediction: Optional[Dict] = None) -> List[str]:
    """Turn the user's profile into several focused retrieval queries."""
    prediction = prediction or {}
    age = health_data.get("age")
    gender = str(health_data.get("gender") or "").lower()
    activity = str(health_data.get("physicalActivity") or "").lower()
    smoking = str(health_data.get("smokingHabit") or "").lower() in ("yes", "true", "1")
    bmi_cat = _bmi_category(health_data.get("bmi"))
    systolic, diastolic = _parse_bp(health_data.get("bloodPressure"))
    risk = str(prediction.get("risk_level") or "").lower()

    queries = [
        f"balanced diet and daily food groups for an adult {gender} aged {age} with {activity or 'moderate'} physical activity",
        f"recommended energy and protein requirement for {activity or 'moderate'} activity {gender}",
    ]

    if risk in ("intermediate", "high") or (systolic and systolic >= 130) or (diastolic and diastolic >= 85):
        queries += [
            "diet to prevent and control hypertension high blood pressure",
            "limit salt sodium intake and increase potassium rich foods",
        ]
    if bmi_cat in ("overweight", "obese"):
        queries.append("diet and lifestyle for weight loss and preventing obesity, abdominal obesity")
    elif bmi_cat == "underweight":
        queries.append("nutrient dense diet to gain healthy weight for undernourished adults")
    if smoking:
        queries.append("antioxidant rich fruits and vegetables, avoid tobacco and alcohol")
    if age and age >= 60:
        queries.append("nutrition and diet for elderly older adults")
    if gender.startswith("f") and age and 15 <= age <= 49:
        queries.append("iron and folate requirements for women of reproductive age")
    if activity in ("sedentary", "low", "none"):
        queries.append("physical activity recommendations for sedentary adults")

    queries += [
        "heart healthy fats, oils and avoiding trans fats and ultra processed foods",
        "foods high in fat sugar and salt to avoid",
    ]
    return queries


# =========================
# CONTEXT FORMATTING
# =========================
def _fit_context(passages: List[Dict]) -> List[Dict]:
    """Keep the passages that fit the prompt budget, so `sources` matches what the LLM saw."""
    kept, total = [], 0
    for p in passages:
        total += len(p["text"]) + 40
        if total > MAX_CONTEXT_CHARS:
            break
        kept.append(p)
    return kept


def _format_context(passages: List[Dict]) -> str:
    blocks = []
    for i, p in enumerate(passages, start=1):
        location = f"{p['source']}, p.{p['page']}" if p.get("page") else p["source"]
        blocks.append(f"[{i}] ({location})\n{p['text']}")
    return "\n\n".join(blocks)


_CITATION_RE = re.compile(r"\[(\d+)\]")


def _strip_invalid_citations(value, n_sources: int):
    """Remove citation markers pointing at sources that don't exist (deterministic, no LLM call)."""
    if isinstance(value, str):
        return _CITATION_RE.sub(lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_sources else "", value)
    if isinstance(value, list):
        return [_strip_invalid_citations(v, n_sources) for v in value]
    if isinstance(value, dict):
        return {k: _strip_invalid_citations(v, n_sources) for k, v in value.items()}
    return value


def _sources(passages: List[Dict]) -> List[Dict]:
    return [
        {"ref": i, "source": p["source"], "page": p.get("page"), "score": p["score"], "excerpt": p["text"][:240]}
        for i, p in enumerate(passages, start=1)
    ]


def _user_profile(health_data: Dict) -> Dict:
    return {k: v for k, v in health_data.items() if k not in ("password", "email", "name")}


def _build_prompt(health_data: Dict, prediction: Dict, context: str, feedback: str = "") -> str:
    safe_health = _user_profile(health_data)
    revision = (
        f"\nA reviewer rejected your previous draft. Fix these problems:\n{feedback}\n" if feedback else ""
    )
    grounding = (
        f"""Use the following excerpts from official dietary guidelines as your primary evidence.
Base recommendations on them wherever possible and cite them using their [n] reference numbers
in "diet_reason", meal descriptions and "guideline_notes". If the excerpts do not cover something,
use standard nutrition science and do not invent citations.

=== GUIDELINE EXCERPTS ===
{context}
=== END EXCERPTS ===
"""
        if context
        else "No guideline excerpts are available; rely on standard evidence-based nutrition science.\n"
    )

    return f"""You are an expert clinical nutritionist. Create a personalised diet blueprint for the user below.
{grounding}
Output ONLY valid JSON matching this structure:
{{
  "diet_type": "DASH Diet",
  "diet_reason": "Why this diet suits the user, with citations like [1]",
  "macros": {{"protein": "70g", "carbs": "250g", "fat": "55g", "calories": "2000", "fiber": "35g"}},
  "meal_plan": [
    {{"meal": "Breakfast", "description": "..."}},
    {{"meal": "Mid-morning", "description": "..."}},
    {{"meal": "Lunch", "description": "..."}},
    {{"meal": "Evening snack", "description": "..."}},
    {{"meal": "Dinner", "description": "..."}}
  ],
  "foods_to_avoid": ["..."],
  "supplements": [
    {{"name": "Vitamin D", "dose": "...", "reason": "..."}}
  ],
  "guideline_notes": ["Key guideline-backed point with citation [2]"],
  "weekly_habit_tip": "..."
}}

Calories and macros must be computed for this user's age, gender, weight, height and activity level.
Prefer culturally appropriate, locally available foods. Only suggest supplements when justified.
{revision}
User Health Data:
{json.dumps(safe_health, indent=2)}

Cardiovascular Risk Assessment (Framingham 10-year CVD risk + ACC/AHA BP stage):
{json.dumps(prediction, indent=2)}
"""


# =========================
# PIPELINE
# =========================
async def retrieve_context(health_data: Dict, prediction: Optional[Dict] = None) -> List[Dict]:
    """Run retrieval in a worker thread (embedding is CPU-bound). Returns [] if the index is unavailable."""
    def _run():
        retriever = get_retriever()
        if retriever is None:
            return []
        return retriever.search(build_queries(health_data, prediction))

    try:
        return await asyncio.to_thread(_run)
    except Exception as e:
        logger.error(f"RAG retrieval failed, continuing without context: {e}")
        return []


async def _complete_json(groq_client, model: str, prompt: str) -> Dict:
    messages = [
        {"role": "system", "content": "You are a helpful expert nutritionist that only outputs valid JSON."},
        {"role": "user", "content": prompt},
    ]
    for attempt in range(2):
        try:
            completion = await groq_client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            return json.loads(completion.choices[0].message.content)
        except BadRequestError as e:
            # Groq rejects malformed JSON output (json_validate_failed); one retry usually succeeds
            if attempt == 0 and "json_validate_failed" in str(e):
                logger.warning("Generator returned invalid JSON — retrying once")
                continue
            raise


async def _generate(groq_client, prompt: str) -> Tuple[Dict, str]:
    """
    Primary model first without SDK retries. If it is rate-limited, switch to the fallback model
    immediately instead of sleeping until the token bucket refills; wait only if both are limited.
    """
    fast_fail = groq_client.with_options(max_retries=0)
    for model in filter(None, dict.fromkeys([GROQ_MODEL, GROQ_FALLBACK_MODEL])):
        try:
            return await _complete_json(fast_fail, model, prompt), model
        except RateLimitError:
            logger.warning(f"{model} is rate-limited — trying next model")
    return await _complete_json(groq_client, GROQ_MODEL, prompt), GROQ_MODEL


def _ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


def _rank(verdict: Optional[Dict]) -> tuple:
    if verdict is None:
        return (-1, -1)
    return (len(SUPPORT_LEVELS) - SUPPORT_LEVELS.index(verdict["is_supported"]), verdict["is_useful"])


def _decorate(blueprint: Dict, passages: List[Dict], verdict: Optional[Dict], retries: int,
              model_used: str, timings: Dict) -> Dict:
    """Attach sources and Self-RAG metadata; returns a new dict so drafts and the final answer stay separate."""
    result = _strip_invalid_citations(blueprint, len(passages))
    result["sources"] = _sources(passages)
    result["rag_grounded"] = bool(passages)
    result["self_rag"] = {
        "critic": verdict,
        "verified": verdict is not None,
        "regenerations": retries,
        "generator_model": model_used,
        "reranked_passages": sum(1 for p in passages if p.get("rerank_score") is not None),
        "timings_ms": dict(timings),
    }
    return result


async def _no_op(event: str, data: Dict) -> None:
    pass


async def generate_rag_diet_blueprint(
    groq_client, health_data: Dict, prediction: Dict,
    on_event: Callable[[str, Dict], Awaitable[None]] = _no_op,
) -> Dict:
    """
    Self-RAG flow:  retrieve (hybrid + conditional rerank, IsRel filter)
                 -> generate grounded blueprint
                 -> critique (IsSup + IsUse, one fast call, time-boxed)
                 -> regenerate once with critic feedback ONLY on serious failure.

    `on_event` receives progress for streaming clients: ("status", {"stage"}) at each step and
    ("draft", blueprint) as soon as the first draft exists, before the critic has checked it.
    """
    timings = {}
    await on_event("status", {"stage": "retrieving"})
    t = time.perf_counter()
    passages = _fit_context(await retrieve_context(health_data, prediction))
    timings["retrieval"] = _ms(t)

    context = _format_context(passages)
    await on_event("status", {"stage": "generating", "passages": len(passages)})
    t = time.perf_counter()
    blueprint, model_used = await _generate(groq_client, _build_prompt(health_data, prediction, context))
    timings["generation"] = _ms(t)

    verdict, retries = None, 0
    if SELF_RAG_CRITIC and passages:
        await on_event("draft", _decorate(blueprint, passages, None, 0, model_used, timings))
        await on_event("status", {"stage": "verifying"})
        profile = _user_profile(health_data)
        t = time.perf_counter()
        verdict = await critique(groq_client, blueprint, passages, profile)
        timings["critic"] = _ms(t)

        while needs_regeneration(verdict) and retries < SELF_RAG_MAX_RETRIES:
            retries += 1
            logger.info(f"Self-RAG critic rejected blueprint ({verdict}) — regenerating")
            await on_event("status", {"stage": "revising"})
            feedback = "\n".join(filter(None, [verdict["feedback"], *verdict["unsupported_claims"]]))
            t = time.perf_counter()
            try:
                candidate, candidate_model = await _generate(groq_client, _build_prompt(health_data, prediction, context, feedback))
            except Exception as e:
                logger.warning(f"Corrective regeneration failed, keeping first draft: {e}")
                break
            new_verdict = await critique(groq_client, candidate, passages, profile)
            timings[f"regeneration_{retries}"] = _ms(t)
            # Keep whichever draft the critic rates higher
            if new_verdict is None or _rank(new_verdict) >= _rank(verdict):
                blueprint, verdict, model_used = candidate, new_verdict, candidate_model

    return _decorate(blueprint, passages, verdict, retries, model_used, timings)
