# Week 4 Homework Submission

## Link to LangSmith Traces
https://smith.langchain.com/o/2a2dba2b-244d-4ed7-9b5b-9a35b469bcde/datasets/8c21cee5-7cc5-4608-84f9-d1fcba3521dc/compare?selectedSessions=087f8c23-dd4d-44aa-b774-2de7be332721

## Notes
- Hardened agent lives in `solution/src/openclaw_agent/`.
- `fixed_openclaw_agent.py` is a thin entrypoint shim that re-exports the package and runs against the original starter inbox.
- See `fix-report.md` for the full issue-by-issue analysis and `tests.md` for the seven-scenario walkthrough.
- LLM calls are routed through the DataExpert proxy (`base_url=https://www.dataexpert.io/api/v1/anthropic`, `x-session-id` header). `.env.example` documents the required environment.
