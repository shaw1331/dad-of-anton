# Agent Instructions

**⚠️ IMPORTANT: You MUST read this file before ANY git operation. Do not assume — check here first.**

## Git Workflow

- **Never push directly to `main`.** Always create a feature branch, commit there, and open a PR for review.
- Branch naming: `feat/<description>`, `fix/<description>`, or `chore/<description>`
- Keep commits focused and use conventional commit messages (`feat:`, `fix:`, `refactor:`, `chore:`, etc.)
- **Always create feature branches from the latest `main`**, not from other feature branches. Use `git fetch origin main` then `git checkout -b feat/<description> origin/main`.
