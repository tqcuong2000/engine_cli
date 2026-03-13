# engine-cli

`engine-cli` is an early-stage terminal control plane for Minecraft server environments and, over time, AI agents operating inside or alongside those environments.

The long-term goal is to provide a single operator console for:

- managing Minecraft server instances
- provisioning and supervising AI agents connected to servers
- handling common server operations
- assisting with datapack-oriented workflows and code generation

This project is at the very beginning of development. The current codebase is a Textual UI shell, not a production-ready management system.

## Status

Current state:

- very early prototype
- UI-first scaffold built with [Textual](https://textual.textualize.io/)
- package entrypoints are wired
- core Minecraft/server/agent logic is not implemented yet

Implications:

- expect breaking changes
- backward compatibility is not a priority during early development
- architecture, commands, and data models are still fluid

## Problem Framing

Minecraft automation tends to fragment into several disconnected layers:

- server process management
- world and instance configuration
- gameplay automation or bot runtimes
- datapack authoring and iteration
- operational scripting and observability

`engine-cli` is intended to converge those layers into one local operator-facing system. The core idea is not just "a CLI for servers", but a host-side orchestration surface that can reason about Minecraft instances, agent runtimes, and content workflows as one domain.

## Vision

The intended product direction is a local terminal control plane for Minecraft operations. Instead of treating server hosting, agent deployment, and datapack workflows as separate tools, `engine-cli` aims to unify them in one interface.

Planned capability areas include:

- server instance lifecycle management
- environment configuration and templating
- AI agent deployment and runtime supervision
- command execution and operational monitoring
- datapack generation, editing, and validation support
- future integration with model-driven automation workflows

## What Exists Today

The repository currently contains:

- a Python package under `src/engine_cli`
- a basic Textual TUI app layout with header, body, panel, and footer
- a custom dark theme
- minimal test coverage for app initialization

At this stage, the application is best understood as the initial interface scaffold for the larger platform.

## Architectural Direction

This project is intended to follow an object-oriented design approach centered on explicit domain objects.

The likely system shape is:

- `interface layer`: Textual TUI for operator workflows
- `application layer`: commands, orchestration, task execution, lifecycle coordination
- `domain layer`: server instances, agent runtimes, datapack workspaces, environment definitions
- `infrastructure layer`: filesystem operations, process execution, Minecraft server adapters, model providers, telemetry

Expected responsibilities:

- the domain model should be represented through explicit objects such as `ServerInstance`, `AgentRuntime`, `Workspace`, and `TaskRun`
- server management should model instance lifecycle explicitly rather than shelling out ad hoc from UI code
- AI agent deployment should be treated as a managed runtime with configuration, state, logs, and failure handling
- datapack tooling should behave like a workspace-oriented build/edit/validate pipeline, not just prompt-to-file generation
- the TUI should remain a thin interaction surface over application services

This separation is not fully implemented yet, but it is the most likely direction if the project grows beyond a prototype.

## Domain Scope

The project is currently aimed at these domain entities:

- `server instance`: a managed Minecraft server runtime plus config, files, and process state
- `agent`: an AI-driven or automation-driven runtime associated with a server or workspace
- `workspace`: a local project boundary for datapacks, configs, prompts, and generated artifacts
- `task`: a unit of execution such as provision, start, stop, inspect, sync, validate, or generate
- `environment`: host-side dependencies, paths, credentials, and runtime constraints needed to execute tasks

## Design Principles

- object-oriented domain modeling over script-first orchestration
- modular monolith over premature service decomposition
- local-first orchestration over remote-control-first design
- explicit lifecycle management over hidden background behavior
- typed application state over stringly-typed shell glue
- fast iteration over backward compatibility during early development
- composable primitives over large monolithic command handlers

## Non-Goals For Now

- stable external APIs
- plugin compatibility guarantees
- multi-tenant hosting concerns
- broad provider abstraction before core workflows exist
- production-grade security hardening claims

## Getting Started

### Requirements

- Python `3.13.7` or newer

### Install

```bash
pip install -e .
```

### Run

```bash
engine
```

You can also run:

```bash
python -m engine_cli
```

### Test

```bash
python -m unittest
```

## Project Structure

```text
src/engine_cli/
  __main__.py                  Package entrypoint
  interfaces/tui/              Textual application code
  resources/                   TUI styling resources
tests/
  test_app.py                  Minimal app bootstrap test
```

## Development Direction

Near-term work will likely focus on:

1. defining the core domain model for server instances, agents, and workspaces
2. designing the command and task execution flow
3. connecting the TUI to real application state
4. implementing Minecraft server management primitives
5. adding agent orchestration and datapack tooling

## Suggested Near-Term Milestones

1. Define the core domain objects and state transitions.
2. Build a task runner abstraction for process, filesystem, and validation jobs.
3. Add persistent project/workspace configuration.
4. Implement a first real vertical slice:
   server instance create -> configure -> launch -> inspect -> stop
5. Add an agent runtime contract:
   config, startup, health, logs, shutdown, restart semantics
6. Add datapack workspace support with generation and validation hooks.

## Contributing

Because the project is still forming:

- prefer simple, direct designs over premature abstraction
- expect interfaces to change quickly
- avoid optimizing for backward compatibility unless there is a clear need

## License

No license has been declared yet.
