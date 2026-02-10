## Summary

<!-- Briefly describe what this PR does and why -->

## Changes

<!-- Bullet list of key changes -->

-

## Type

- [ ] `feat` — New feature
- [ ] `fix` — Bug fix
- [ ] `refactor` — Code restructuring (no behavior change)
- [ ] `test` — Adding or updating tests
- [ ] `docs` — Documentation only
- [ ] `ci` — CI/CD changes
- [ ] `chore` — Maintenance (deps, config, etc.)

## Workstream

- [ ] Voice Agent (`agent/`)
- [ ] Mobile App (`mobile/`)
- [ ] Supabase Backend (`supabase/`)
- [ ] Documentation (`docs/`)
- [ ] CI/CD (`.github/`)

## Checklist

### Code Quality
- [ ] Code compiles/runs without errors
- [ ] All existing tests pass
- [ ] New code has tests (unit at minimum)
- [ ] No hardcoded secrets, URLs, or API keys
- [ ] Error handling covers failure cases
- [ ] No `console.log` / `print` left in (use proper logging)

### Language-Specific
- [ ] **TypeScript**: No `any` types introduced
- [ ] **Python**: Passes `black` + `ruff` + `mypy`
- [ ] **SQL**: Uses parameterized queries, RLS enabled

### Other
- [ ] Database changes have a migration file
- [ ] Breaking changes documented below
- [ ] Commit messages follow Conventional Commits (`feat:`, `fix:`, etc.)

## Breaking Changes

<!-- List any breaking changes, or write "None" -->

None

## Testing

<!-- How did you test this? What should reviewers verify? -->

## Screenshots

<!-- If UI changes, add before/after screenshots -->
