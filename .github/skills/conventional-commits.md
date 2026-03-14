# Skill: Conventional Commits

Use the **Conventional Commits 1.0** specification for every commit message in this repository.

## Format

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

- The **header** (first line) is mandatory and must not exceed **72 characters** (git tooling convention for commit subjects).
- The **body** is optional; wrap at **100 characters** per line.
- The **footer** is optional; use it for breaking-change notices or issue references.

---

## Types

| Type | When to use |
|------|-------------|
| `feat` | A new feature visible to users |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, whitespace — no logic change |
| `refactor` | Code restructure without feature or fix |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates, tooling |
| `ci` | Changes to CI/CD configuration files |
| `revert` | Reverts a previous commit |

---

## Scope (optional)

Use a short noun describing the part of the codebase affected, e.g.:

- `fetch` — HTTP fetching logic
- `parse` — HTML parsing logic
- `csv` — CSV output logic
- `cli` — command-line argument handling
- `deps` — dependency management

---

## Rules

1. Use the **imperative mood** in the summary: *"add retry logic"*, not *"added"* or *"adds"*.
2. Do **not** capitalize the first letter of the summary (the type is already a prefix).
3. Do **not** end the summary with a period.
4. Separate the header from the body with a **blank line**.
5. Reference GitHub issues in footers: `Closes #<number>` or `Refs #<number>`.
6. Mark breaking changes with `BREAKING CHANGE:` in the footer **and/or** by appending `!` after the type/scope: `feat(cli)!: rename --sep flag`.

---

## Examples

```
feat(fetch): add configurable connection semaphore limit
```

```
fix(parse): guard against missing daily-index span

BeautifulSoup's find() can return None when the page structure
changes. Added a defensive check before accessing .text to prevent
an AttributeError at runtime.

Closes #12
```

```
chore(deps): upgrade aiohttp to 3.10.5
```

```
docs: update README with --sep option usage
```

```
refactor(csv): extract _fmt helper into module-level function
```

```
feat(cli)!: rename --sep flag to --decimal-sep

BREAKING CHANGE: scripts that passed `-s` must be updated to use
`--decimal-sep` or its new short form `-d`.
```
