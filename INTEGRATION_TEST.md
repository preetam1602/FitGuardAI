// Integration Test for FitGuard AI Frontend-Backend
// This test verifies that the frontend and backend are properly integrated

description: 'Verify frontend-backend integration for FitGuard AI'

steps:
  - Check that API service is properly configured
  - Verify that auth service can handle login/register
  - Test health service endpoints
  - Ensure authentication state management works
  - Validate JWT token handling

expected_results:
  - API_BASE_URL is correctly set
  - Auth service endpoints are reachable
  - Health service endpoints are properly configured
  - Authentication state is managed correctly
  - JWT tokens are stored and retrieved properly

notes:
  - This test requires a running backend server
  - Tests should be run in a development environment
  - Mock data can be used for testing

commands:
  - npm run test:integration (if configured)
  - python -m pytest backend/tests/ (if backend tests exist)
  - curl http://localhost:3001/ (to verify backend is running)
