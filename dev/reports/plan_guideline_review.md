# Plan vs. Guidelines Review
## Feature: Persistent Server Instance Catalog

Review of [feature_implementation_plan_server_instance_persistence_2026-03-14.md](file:///x:/engine_cli/dev/plans/feature_implementation_plan_server_instance_persistence_2026-03-14.md) against the three guidelines in `dev/guideline/`.

---

## Summary Verdict

> [!TIP]
> The plan is **well-aligned** with all three guidelines overall. There are a few areas worth tightening, but no fundamental violations. The notes below are organized by guideline, with a compliance rating for each section.

---

## 1. Architecture Guideline ([architecture.md](file:///x:/engine_cli/dev/guideline/architecture.md))

### 1.1 Commit to One Delivery Path — ✅ Pass

The plan commits to a single delivery path: replace `InMemoryServerCatalog` with a `ServerInstanceRepository` contract backed by `SqliteServerInstanceRepository`. There is no ambiguity about parallel approaches.

The in-memory catalog is kept **only** as a test implementation of the same contract — this is the right kind of "keep both" (shared interface, not parallel features).

### 1.2 Prefer Intentional Simplification — ✅ Pass

- The plan explicitly scopes out full config-resolution, task persistence, session persistence, and agent persistence.
- `AppPaths` is introduced as a minimal foundation, not a large framework.
- The old `InMemoryServerCatalog` is refitted to implement the contract rather than deleted or kept as a second path.

### 2.1 Keep Behavior in Its Owner — ✅ Pass

| Concern | Owner in Plan | Correct? |
|:--------|:-------------|:--------:|
| Persistence contract | `application/server_instances/repository.py` | ✅ |
| SQLite implementation | `infrastructure/persistence/sqlite/` | ✅ |
| Path resolution | `infrastructure/persistence/paths.py` | ✅ |
| Lifecycle-state normalization on load | Row mapper in `infrastructure/persistence/sqlite/server_instances.py` | ⚠️ See note |
| Manager orchestration | `application/server_instances/manager.py` | ✅ |

> [!NOTE]
> **Minor concern — lifecycle-state validation ownership.**
> The plan places transient-state rejection in the *row mapper* (infrastructure). The [lifecycle guideline §3.1](#lifecycle-31) says application services should accept state changes. Since this is *read-time validation* (rejecting bad persisted data) rather than a transition decision, placing it in infrastructure is defensible — but the plan should **explicitly state** that this is data-integrity validation, not policy, to avoid future confusion. Consider also having the repository contract's docstring note the invariant ("only durable lifecycle states are returned").

### 2.2 Model State Explicitly — ✅ Pass

- Lifecycle states are a named finite set: `draft`, `configured`, `stopped`, `failed`.
- Transient states (`starting`, `running`, `stopping`) are explicitly excluded from persistence.
- `AppPaths` is a frozen dataclass with named fields — explicit shape.

### 3.1 Treat Shared as a Last Resort — ✅ Pass

No new code is placed in `shared`. `AppPaths` goes to `infrastructure/persistence/`, and the repository contract lives in `application/server_instances/`.

---

## 2. Lifecycle Design Guideline ([lifecycle.md](file:///x:/engine_cli/dev/guideline/lifecycle.md))

### 1.1 Name the Stable States — ✅ Pass

The plan names four durable lifecycle states explicitly and lists the three transient states that must not be persisted.

### 1.2 Define Transition Contracts Up Front — ⚠️ Partial

The plan defines a **persistence policy** (which states may be saved/loaded), but it does **not** describe the transition that occurs on load. Specifically:

- What lifecycle state does a server get when it is *loaded from storage*? The plan says persisted `stopped` → `stopped`, persisted `failed` → `failed`, etc., but it doesn't explicitly address whether a freshly loaded server should be set to a canonical "restored" or "idle" state.
- What happens if the *application* tries to start a server whose persisted state was `failed`? Is that transition allowed?

> [!IMPORTANT]
> **Recommendation:** Add a short "Load-Time Lifecycle Normalization" paragraph to §3.4 that explicitly states:
> - Loaded servers retain their persisted durable state as-is (no normalization needed because only durable states are persisted).
> - The existing lifecycle service's transition rules govern what can happen next (e.g., `failed` → `configured` via re-import, `stopped` → `starting` via start).
>
> This satisfies guideline §1.2 ("define transition contracts up front") for the persistence boundary.

### 2.1 Separate Desired, Runtime, and Observed State — ✅ Pass

The plan explicitly separates:
- **Durable/desired state**: what is persisted (`draft`, `configured`, `stopped`, `failed`)
- **Runtime state**: transient states (`starting`, `running`, `stopping`) that exist only in-memory

This is exactly the separation the guideline recommends.

### 2.2 Persist Only Recovery-Relevant State — ✅ Pass

The plan explicitly persists only identity/spec metadata and stable lifecycle values. Transient runtime states are excluded. This directly matches the guideline.

### 3.1 Let Application Services Accept State Changes — ⚠️ Worth Noting

As mentioned above, the row mapper rejects invalid lifecycle states on load. This is infrastructure-level validation, not application-level acceptance. The guideline says "route lifecycle acceptance through application services."

> [!NOTE]
> **Mitigation already in the plan:** The `ServerInstanceManager` remains the orchestrator for all state changes. The row mapper only performs data-integrity checks (not policy decisions). This is consistent with the guideline's "deviate" clause ("self-contained domain validation can reject impossible states locally"). Still, adding a one-liner to the plan acknowledging this distinction would be clean.

### 3.2 Introduce Events Only for Real Fan-Out — ✅ Pass

The plan uses direct orchestration (manager → repository calls). No event system is introduced. Correct per the guideline.

---

## 3. Module Boundaries Guideline ([module_boundaries.md](file:///x:/engine_cli/dev/guideline/module_boundaries.md))

### 1.1 Place Code by Primary Responsibility — ✅ Pass

| New Component | Placed In | Primary Responsibility Match? |
|:-------------|:----------|:----------------------------:|
| `ServerInstanceRepository` (contract) | `application/server_instances/` | ✅ Application-facing contract |
| `SqliteServerInstanceRepository` | `infrastructure/persistence/sqlite/` | ✅ Infrastructure adapter |
| `AppPaths` | `infrastructure/persistence/` | ✅ Infrastructure concern |
| `StorageBootstrap` | `infrastructure/persistence/sqlite/` | ✅ Infrastructure setup |

### 1.2 Split Mixed-Responsibility Files Early — ✅ Pass

- The repository contract is a separate file from the manager.
- The row mapper lives with the SQLite repository (same concern).
- Bootstrap is its own file.

No mixed-responsibility files are introduced.

### 2.1 Keep Dependencies Pointing Inward — ✅ Pass

```
interfaces/tui (outer)
    → application/server_instances (middle)
        → domain/server (inner)
infrastructure/persistence (outer, implementing application contracts)
    → application/server_instances (contract definition)
```

Dependencies flow inward. Infrastructure implements application-defined contracts. The application layer never imports from infrastructure.

### 2.2 Preserve a Single Cross-Module Flow — ✅ Pass

The plan maintains one flow:
1. **Interface** (`EngineCli`) constructs and injects dependencies
2. **Application** (`ServerInstanceManager`) orchestrates via the repository contract
3. **Infrastructure** (`SqliteServerInstanceRepository`) performs I/O

No duplicate orchestration paths are created.

### 3.1 Require a Strong Case for Shared Utilities — ✅ Pass

Nothing is added to `shared`.

### 3.2 Keep Presentation and Adapters Out of Policy Decisions — ⚠️ Worth Noting

The plan has `EngineCli` (TUI/interface layer) constructing `AppPaths` and the SQLite repository. This is **construction/wiring**, not policy — which is acceptable. However:

> [!NOTE]
> **Suggestion:** If the wiring logic in `EngineCli.__init__` grows beyond a few lines (path creation → bootstrap → repo construction → manager injection), consider battery extracting a small factory or `create_app()` builder function in the application layer. This keeps the TUI layer as a thin shell and the construction logic testable independently. This isn't a violation today, but it's a pressure point to watch.

---

## Checklist Summary

| Guideline Check | Status | Notes |
|:----------------|:------:|:------|
| **Architecture** | | |
| One delivery path | ✅ | Single repository contract path |
| Intentional simplification | ✅ | Minimal scope, no over-engineering |
| Behavior in its owner | ✅ | Minor note on lifecycle validation placement |
| Explicit state modeling | ✅ | Named states, frozen dataclass |
| Shared as last resort | ✅ | Nothing added to shared |
| **Lifecycle** | | |
| Named stable states | ✅ | Four durable states defined |
| Transition contracts up front | ⚠️ | **Add load-time normalization paragraph** |
| Separate desired/runtime/observed | ✅ | Clean separation |
| Persist only recovery-relevant state | ✅ | Transient states excluded |
| App services accept state changes | ⚠️ | Infra validates data integrity — acceptable but worth documenting |
| Events only for real fan-out | ✅ | Direct orchestration |
| **Module Boundaries** | | |
| Place code by primary responsibility | ✅ | All placements correct |
| Split mixed-responsibility files early | ✅ | Clean file separation |
| Dependencies point inward | ✅ | Correct dependency flow |
| Single cross-module flow | ✅ | No duplicate paths |
| Strong case for shared | ✅ | Nothing in shared |
| Presentation out of policy | ✅ | Construction-only, watch for growth |

---

## Recommended Actions

> [!IMPORTANT]
> These are suggestions for tightening the plan, not blockers.

1. **Add a "Load-Time Lifecycle Normalization" note to §3.4** — Explicitly state that loaded servers retain their persisted durable state and that the existing lifecycle transition rules govern subsequent operations. This closes the gap with lifecycle guideline §1.2.

2. **Clarify that row-mapper rejection is data-integrity validation, not policy** — A one-sentence note in §3.2 or §3.4 would make it clear that the infrastructure rejects corrupt data (not lifecycle transitions), keeping the plan aligned with lifecycle guideline §3.1.

3. **Watch the `EngineCli.__init__` wiring complexity** — Not an issue yet, but if Phase 3 wiring grows beyond ~10 lines, consider extracting an `app_factory` or `create_app()` function in the application layer to keep the interface thin.
