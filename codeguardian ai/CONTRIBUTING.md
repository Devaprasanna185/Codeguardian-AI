# Contributing to CodeGuardian AI

Thanks for helping! This project is beginner-friendly and Hacktoberfest-friendly.

## Good first contributions
- Add a new JavaScript rule in `backend/app/analyzers/js_rules.py` (one tuple = one rule).
- Add a labelled example to `backend/eval/cases.py` (a snippet + the issue it contains).
- Improve a beginner explanation in `backend/app/analyzers/explanations.py`.
- Add a TypeScript or Go analyzer behind the same `Finding` schema.

## Workflow
1. Fork and create a branch: `git checkout -b feat/my-change`
2. `cd backend && pip install -r requirements.txt && pytest -q`
3. If you changed detection logic run `python -m eval.run_eval --no-ai` and include the numbers in your PR.
4. Keep PRs small, one idea each. Add or update tests.

## Principles
- **Static tools first.** Security claims should be verified by Bandit/Ruff/pattern rules; the AI explains and suggests, it doesn't get the final word.
- **Beginner-friendly language.** Explain *why* it's a problem, not just *what*.
- **Never execute user code.**

## Code of conduct
Be kind. Assume good intent. Review code, not people.
