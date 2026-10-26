"""
Self-RAG reflection critics (Asai et al., 2023), implemented as a prompted critic.

The paper's four reflection tokens and how they map here (chosen for latency):
  Retrieve -> always "yes": a diet blueprint always needs guideline evidence, so no LLM call.
  IsRel    -> decided during retrieval from dense / cross-encoder scores, so no LLM call.
  IsSup    -> LLM critic: are the blueprint's cited claims supported by the excerpts?
  IsUse    -> LLM critic: is the blueprint useful and safe for this user's profile?
IsSup and IsUse are judged in ONE batched call on a small, fast model with a hard timeout.
Beam search over multiple generations is not used: it would multiply generation latency.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

from .config import CRITIC_MODEL, CRITIC_TIMEOUT_S, MIN_USEFULNESS

logger = logging.getLogger(__name__)

SUPPORT_LEVELS = ("fully", "partially", "no")
MAX_EXCERPT_CHARS = 500


def _critic_prompt(blueprint: Dict, passages: List[Dict], user_profile: Dict) -> str:
    excerpts = "\n\n".join(
        f"[{i}] {p['text'][:MAX_EXCERPT_CHARS]}" for i, p in enumerate(passages, start=1)
    ) or "(no excerpts were retrieved)"
    plan = {k: v for k, v in blueprint.items() if k not in ("sources", "rag_grounded", "self_rag")}
    return f"""You are a strict reviewer of a diet blueprint produced from guideline excerpts.

Judge two things:
1. IsSup - are the claims that carry citations [n] actually supported by excerpt [n]?
   "fully" = all cited claims supported, "partially" = some unsupported or mis-cited, "no" = mostly unsupported/fabricated.
2. IsUse - how useful and appropriate is the plan for THIS user (1-5)? Penalise advice that conflicts with
   their condition (e.g. high-sodium foods for high blood pressure), unrealistic calories, or missing essentials.

Output ONLY JSON:
{{"is_supported": "fully|partially|no",
  "is_useful": 1-5,
  "unsupported_claims": ["short quote of each unsupported or mis-cited claim"],
  "feedback": "one or two sentences on what must be fixed, empty if nothing"}}

=== USER PROFILE ===
{json.dumps(user_profile)}

=== EXCERPTS ===
{excerpts}

=== BLUEPRINT ===
{json.dumps(plan, ensure_ascii=False)}
"""


def _normalize(raw: Dict) -> Dict:
    support = str(raw.get("is_supported", "")).lower()
    if support not in SUPPORT_LEVELS:
        support = "partially"
    try:
        usefulness = max(1, min(5, int(raw.get("is_useful", 3))))
    except (TypeError, ValueError):
        usefulness = 3
    claims = raw.get("unsupported_claims") or []
    return {
        "is_supported": support,
        "is_useful": usefulness,
        "unsupported_claims": [str(c) for c in claims][:10] if isinstance(claims, list) else [],
        "feedback": str(raw.get("feedback") or ""),
    }


async def critique(groq_client, blueprint: Dict, passages: List[Dict], user_profile: Dict) -> Optional[Dict]:
    """Return the IsSup/IsUse verdict, or None if the critic failed or timed out (never blocks the answer)."""
    try:
        completion = await asyncio.wait_for(
            # No SDK retries: a rate-limited critic should skip verification, not delay the answer
            groq_client.with_options(max_retries=0).chat.completions.create(
                model=CRITIC_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise evaluator that only outputs valid JSON."},
                    {"role": "user", "content": _critic_prompt(blueprint, passages, user_profile)},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                reasoning_effort="low",
            ),
            timeout=CRITIC_TIMEOUT_S,
        )
        return _normalize(json.loads(completion.choices[0].message.content))
    except asyncio.TimeoutError:
        logger.warning(f"Self-RAG critic timed out after {CRITIC_TIMEOUT_S}s — returning unverified blueprint")
    except Exception as e:
        logger.warning(f"Self-RAG critic failed — returning unverified blueprint: {e}")
    return None


def needs_regeneration(verdict: Optional[Dict]) -> bool:
    """Only serious failures trigger the (expensive) corrective regeneration."""
    if verdict is None:
        return False
    return verdict["is_supported"] == "no" or verdict["is_useful"] < MIN_USEFULNESS
