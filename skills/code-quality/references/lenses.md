# Lenses: what to flag, what to leave alone

Each analyzer agent gets exactly one lens. Read only your lens section plus "Shared rules".

## Shared rules

- Evidence is verbatim code with line numbers, copied from the file. Never paraphrase, never invent.
- One finding per root cause. A god class is one SOLID/SRP finding, not one finding per method.
- Before claiming "unused" or "duplicated elsewhere", grep the whole repository, not only your chunk.
- Report at most 25 findings per chunk. If you have more, keep the highest severity and mention the omitted count in `notes`.
- Prefer fewer, well-evidenced findings. A finding you cannot show in code does not exist.
- When a fix for your lens would violate another lens (an interface for one implementation, a helper for two lines), downgrade to LOW or drop it and say why in `notes`.

### Severity

| Level | Meaning |
|-------|---------|
| HIGH | Already causing or about to cause bugs: diverged copies of business logic, god object every change touches, dead feature flag guarding live code paths |
| MEDIUM | Clear violation with a contained blast radius; fix is a bounded refactor |
| LOW | Real but minor; style-adjacent; fix is optional |

### Confidence

| Level | Meaning |
|-------|---------|
| HIGH | Verified by reading both sides / grepping the whole repo |
| MEDIUM | Likely, but dynamic usage, reflection, or framework magic could change the picture |
| LOW | Judgment call; reviewer should decide |

### Effort

S: under an hour, single file. M: a few files, tests need updating. L: cross-cutting, needs design.

## DRY

Flag:
- Same algorithm or business rule in two or more places, including copies with renamed variables.
- Near-identical functions (same body, different name).
- Parallel `if/elif/switch` chains on the same discriminator in different files.
- Repeated magic values (URLs, thresholds, format strings) that must change together.
- Duplicated validation, mapping, serialization, or error-response formatting.
- Test setup copy-pasted across many test files: LOW.

Do not flag:
- Incidental similarity: code that looks alike but changes for different reasons.
- Idioms of two or three lines.
- Copies across bounded contexts where sharing would couple unrelated modules. If you mention it, LOW with that rationale.
- Generated or vendored code.

Severity guide: HIGH when the copies have already diverged or business logic lives in three or more places. MEDIUM for two nontrivial copies. LOW for small helpers.

Evidence must show both locations. Put the second location in `related` as `path:start-end`.

## KISS

Flag, with the metric in `evidence`:
- Nesting depth of four or more.
- Functions over roughly 60 lines or with more than roughly ten branches.
- Five or more parameters, or boolean flag parameters that switch behavior.
- Abstractions with a single implementation and no test seam or plugin need.
- Indirection layers that only forward calls.
- Clever one-liners, metaprogramming, or reflection where plain code would do.
- Hand-rolled mini-frameworks, DSLs, or configuration systems for one use.

Do not flag:
- Inherent domain complexity that is still readable.
- Long but flat, linear functions: LOW at most.
- Framework-mandated boilerplate.

Severity guide: HIGH when the complexity hides a bug or blocks testing. MEDIUM for deep nesting or flag parameters in core logic. LOW elsewhere.

## YAGNI

Flag:
- Functions, classes, methods, parameters, or exports with zero references outside their definition and tests. Verify with a repository-wide grep first.
- Feature flags or parameters that are never set to the non-default value.
- Abstract methods or interface members that no implementation fulfills.
- Speculative configuration options, extension points, or "for future use" code.
- Dead branches, commented-out code, unreachable code.
- Dependencies declared in the package manifest but never imported.

Do not flag:
- Public API of a library package that is meant to be consumed externally.
- Entry points invoked by reflection, decorators, or frameworks (routes, CLI commands, signal handlers, fixtures, plugins). If unsure, confidence MEDIUM.
- Explicitly documented backward-compatibility shims.

Severity guide: HIGH when dead code guards or duplicates live behavior. MEDIUM for unused public surface that misleads readers. LOW for small unused helpers.

## SOLID

Flag:
- SRP: a class or module with several reasons to change (IO plus business rules plus presentation); functions that validate, persist, and notify in one body.
- OCP: type-tag `if/elif/switch` chains that recur in several places or have four or more branches that clearly grow with new variants.
- LSP: subclasses that override to raise, no-op, tighten preconditions, or change return types.
- ISP: fat base classes or interfaces whose implementors stub methods with `NotImplementedError`, `pass`, or `throw`.
- DIP: high-level modules constructing concrete infrastructure inside (`FileStorage(...)` inside a service, static calls to a global client) when it blocks substitution or testing.

Put the sub-principle in `rule`: SRP, OCP, LSP, ISP, or DIP.

Do not flag:
- Scripts, CLI glue, and small apps where an interface would be ceremony. KISS wins.
- Duck-typed languages: propose constructor injection, not new interfaces, unless several implementations exist.
- A single `switch` in one place. That is fine.

Severity guide: HIGH for god objects on hot paths or DIP violations that make the core untestable. MEDIUM for clear SRP or ISP breaks. LOW for OCP hints.
