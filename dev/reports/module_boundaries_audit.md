# Codebase Review: Module Boundaries
## Evaluation against [module_boundaries.md](file:///x:/engine_cli/dev/guideline/module_boundaries.md)

Audit conducted on the current `src/engine_cli` structure.

---

## Executive Summary

> [!WARNING]
> The codebase has a solid high-level structure but suffers from **layer leakage** between `application` and `infrastructure`. Application services are currently importing and instantiating infrastructure classes directly, which violates the "Dependencies Pointing Inward" principle.

---

## Detailed Compliance Audit

### 1. Module Ownership Map — ⚠️ Partial Pass

| Guideline | Status | Observation |
|:----------|:------:|:------------|
| 1.1 Place Code by Primary Responsibility | ✅ Pass | Files are generally well-placed. `domain`, `application`, `infrastructure`, and `interfaces` have clear scopes. |
| 1.2 Split Mixed-Responsibility Files Early | ✅ Pass | No "god files" found. Process management, server management, and lifecycle are separated. |

### 2. Dependency Flow — ❌ Fail

| Guideline | Status | Observation |
|:----------|:------:|:------------|
| 2.1 Keep Dependencies Pointing Inward | ❌ Fail | **Critical Leakage:** `application` services import directly from `infrastructure`. |
| 2.2 Preserve a Single Cross-Module Flow | ⚠️ Partial | Infrastructure is making domain policy decisions (creating domain objects). |

#### Specific Leakage Examples:
1.  **`ServerInstanceManager`** ([manager.py](file:///x:/engine_cli/src/engine_cli/application/server_instances/manager.py)):
    - Imports `MinecraftServerInspector` from infrastructure.
    - Instantiates it directly in `__init__`.
2.  **`ServerInstanceLifecycleService`** ([server_instance.py](file:///x:/engine_cli/src/engine_cli/application/lifecycle/server_instance.py)):
    - Imports `LocalProcessManager` and `ProcessLogStreamer` from infrastructure.
    - Instantiates them directly in `__init__`.
3.  **`AddServerModalScreen`** ([add_server.py](file:///x:/engine_cli/src/engine_cli/interfaces/tui/modals/add_server.py)):
    - Imports error/result types directly from `infrastructure.minecraft.inspection`.

### 3. Boundary Pressure Checks — ✅ Pass

| Guideline | Status | Observation |
|:----------|:------:|:------------|
| 3.1 Strong Case for Shared Utilities | ✅ Pass | `shared` is currently empty. No "helper clutter" has accumulated yet. |
| 3.2 Presentation/Adapters out of Policy | ⚠️ Partial | **Policy Leak:** `MinecraftServerInspector` (infra) decides the initial lifecycle state (`DRAFT`) and creates the `ServerInstance` object. |

---

## Critical Issues & Remediation Plan

### Issue 1: Application depends on Infrastructure Implementation
Application services are hardcoded to use specific infrastructure adapters (e.g. `LocalProcessManager`). This prevents swapping implementations (e.g. for testing or remote servers) without modifying application code.

> [!IMPORTANT]
> **Priority 1 Remediation:**
> 1. Define `Protocol` classes (interfaces) within the `application` layer (e.g., `ProcessManager` protocol).
> 2. Update Application services to use these Protocols in their type hints.
> 3. remove the hardcoded instantiation in `__init__` and require injection, or move construction to a factory in the `interfaces` or `bootstrap` layer.

### Issue 2: Infrastructure knows about Domain Policy
The `MinecraftServerInspector` is responsible for manufacturing a `ServerInstance` and assigning it the `DRAFT` state.

> [!IMPORTANT]
> **Priority 2 Remediation:**
> 1. The inspector should return a simple "Inspection Result" (data-only).
> 2. The `ServerInstanceManager` (Application) should take that result and call a factory or constructor to create the `ServerInstance` with the correct domain policy (`DRAFT` state).

---

## Compliance Checklist Summary

- [x] Does one module clearly own this responsibility?
- [ ] Are mixed concerns split instead of accumulated? (Mostly yes, but policy is leaking into infra).
- [ ] Does dependency direction still support inward flow? **(No: App → Infra)**
- [ ] Is there only one intended state-changing path across modules? (Yes).
- [x] Is `shared` being used for a truly neutral abstraction? (Yes, empty).

---

## Recommendations for the Persistence Feature
As you implement the **Persistent Server Instance Catalog**, there is a high risk of repeating these mistakes. 

1. **DO NOT** have `ServerInstanceManager` import `SqliteServerInstanceRepository`.
2. **DO** define a `ServerInstanceRepository` Protocol in `application`.
3. **DO** have the interface layer (`EngineCli`) construct the SQLite repository and inject it into the manager. (This is already suggested in the implementation plan review!).
