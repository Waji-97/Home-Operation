# agent_docs

Task-specific playbooks for AI agents (e.g. Claude Code) working in this repo.
Each file describes **what to do when** for a given recurring task. `CLAUDE.md` at
the repo root is the entry point and should link here.

## Index

_(scaffold — fill in as playbooks are added)_

| Doc | When to use |
|-----|-------------|
| _add a new app_ | TODO: steps to onboard a workload into the app-of-apps structure |
| _upgrade an app_ | TODO: how to bump a Helm chart / image and verify |
| _secrets_ | TODO: encrypting app secrets with SOPS/age |

## Conventions

- Keep each playbook focused on a single task.
- Reference the canonical structure docs rather than duplicating them:
  [kubernetes/docs/gitops-structure.md](../kubernetes/docs/gitops-structure.md).
