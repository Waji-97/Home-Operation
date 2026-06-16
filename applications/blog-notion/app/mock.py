"""Built-in sample content so the site renders before Notion creds are wired up.

Shapes mirror what notion.py produces, so templates/renderer behave identically.
"""
from datetime import datetime, timezone


def _rt(text: str) -> dict:
    """Minimal Notion-style rich_text fragment."""
    return {
        "type": "text",
        "plain_text": text,
        "annotations": {
            "bold": False, "italic": False, "strikethrough": False,
            "underline": False, "code": False, "color": "default",
        },
        "href": None,
    }


def _post(id, title, slug, type_, tags, updated):
    return {
        "id": id, "title": title, "slug": slug, "status": "Public",
        "type": type_, "tags": tags, "updated": updated, "cover_url": None,
    }


# 11 public posts so pagination (9 per page) is visible in mock mode.
MOCK_POSTS = [
    _post("mock-gpu", "GPU operations on k3s", "gpu", "Post", ["Kubernetes"], "2026-05-23T10:00:00.000Z"),
    _post("mock-exporter", "Custom Prometheus Exporter", "exporter", "Post", ["Monitoring"], "2026-01-06T10:00:00.000Z"),
    _post("mock-k6", "K6 to Grafana", "k6", "Post", ["Kubernetes", "Monitoring"], "2025-11-18T10:00:00.000Z"),
    _post("mock-bash", "Bash History Logging (Fluent-bit + Opensearch)", "bash_history", "Post", ["Kubernetes", "logging"], "2025-11-02T10:00:00.000Z"),
    _post("mock-clusterapi", "Cluster API on Kubevirt", "cluster_api", "Post", ["Kubernetes"], "2025-08-14T10:00:00.000Z"),
    _post("mock-kspray", "Kubespray Offline Notes", "kspray-off", "Note", ["Kubernetes", "Kubespray"], "2025-05-22T10:00:00.000Z"),
    _post("mock-ansible", "Ansible Notes", "ansible", "Note", ["Automation"], "2025-05-15T10:00:00.000Z"),
    _post("mock-argo", "Taming ArgoCD App-of-Apps", "argocd", "Post", ["Kubernetes", "GitOps"], "2026-03-09T10:00:00.000Z"),
    _post("mock-cilium", "Cilium eBPF Notes", "cilium", "Note", ["Networking"], "2026-02-20T10:00:00.000Z"),
    _post("mock-velero", "Velero Backups to MinIO", "velero", "Post", ["Backup"], "2026-04-11T10:00:00.000Z"),
    _post("mock-vault", "Vault + External Secrets", "vault", "Post", ["Security"], "2026-06-01T10:00:00.000Z"),
]

MOCK_BLOCKS = {
    "mock-gpu": [
        {"type": "paragraph", "id": "b1", "has_children": False,
         "paragraph": {"rich_text": [_rt("Running GPU workloads on a lightweight k3s cluster, "
                                          "from device plugin to a working CUDA pod.")]}},
        {"type": "heading_2", "id": "b2", "has_children": False,
         "heading_2": {"rich_text": [_rt("Installing the NVIDIA device plugin")]}},
        {"type": "code", "id": "b3", "has_children": False,
         "code": {"language": "bash",
                  "rich_text": [_rt("kubectl create -f https://raw.githubusercontent.com/"
                                    "NVIDIA/k8s-device-plugin/v0.15.0/deployments/static/"
                                    "nvidia-device-plugin.yml")]}},
        {"type": "paragraph", "id": "b4", "has_children": False,
         "paragraph": {"rich_text": [_rt("This is mock content — wire up your Notion token "
                                         "to see the real post.")]}},
    ],
    "mock-exporter": [
        {"type": "paragraph", "id": "c1", "has_children": False,
         "paragraph": {"rich_text": [_rt("Writing a small Prometheus exporter in Python and "
                                         "scraping it with a ServiceMonitor.")]}},
    ],
    "mock-ansible": [
        {"type": "paragraph", "id": "d1", "has_children": False,
         "paragraph": {"rich_text": [_rt("Loose notes on idempotent Ansible roles for the homelab.")]}},
        {"type": "bulleted_list_item", "id": "d2", "has_children": False,
         "bulleted_list_item": {"rich_text": [_rt("Prefer modules over command/shell.")]}},
        {"type": "bulleted_list_item", "id": "d3", "has_children": False,
         "bulleted_list_item": {"rich_text": [_rt("Tag everything so you can run slices.")]}},
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
