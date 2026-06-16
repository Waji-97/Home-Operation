# agent_docs

Detailed, task-specific playbooks for AI agents (e.g. Claude Code) working in this
repo. [`CLAUDE.md`](../CLAUDE.md) at the repo root holds the hard rules and links
here for the full detail of each topic.

## Index

| Doc | Use it for |
|-----|------------|
| [repo_layout.md](repo_layout.md) | Directory layout + how app-of-apps fans out |
| [deploying_new.md](deploying_new.md) | Adding a new app — every manifest template |
| [secrets.md](secrets.md) | Encrypting & wiring secrets (SOPS / age / KSOPS) |
| [images.md](images.md) | Container image conventions + (future) delivery pipeline |
| [ci_policy.md](ci_policy.md) | What CI enforces, kube-linter policy, Renovate |
| [cluster_facts.md](cluster_facts.md) | Cluster specs & constraints that shape manifests |

## Conventions

- Keep each playbook focused on a single topic.
- One-line rules live in `CLAUDE.md`; deep detail lives here.
- Human-facing architecture docs are under
  [kubernetes/docs/](../kubernetes/docs/) — don't duplicate; link instead.
