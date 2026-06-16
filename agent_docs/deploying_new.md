# Deploying a new app

The only supported pattern. For a **first-party app you built + Dockerized**, create
`kubernetes/apps/<name>/` with the files below, then wire it into the app-of-apps.

## 1. App manifests — `kubernetes/apps/<name>/`

### `kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
# Only if the app has secrets (see secrets.md):
generators:
  - ./secret-generator.yaml
```

### `namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <name>
```

### `deployment.yaml` — hardened template (passes kube-linter by default)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <name>
  namespace: <name>
  labels:
    app: <name>
spec:
  replicas: 1                 # homelab: single replica is fine
  selector:
    matchLabels:
      app: <name>
  template:
    metadata:
      labels:
        app: <name>
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: <name>
          image: docker.io/waji97/<name>:<pinned-tag>   # Docker Hub; pin a real tag, never :latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 25m
              memory: 64Mi
            limits:
              memory: 128Mi            # set memory limit; omit CPU limit on purpose
          # If the app must write, mount an emptyDir instead of a writable rootfs:
          # volumeMounts: [{ name: tmp, mountPath: /tmp }]
      # volumes: [{ name: tmp, emptyDir: {} }]
```
> If a check legitimately can't be met, add a **per-resource** annotation
> `ignore-check.kube-linter.io/<check>: "reason"` (see the tailscale Deployment) —
> never disable a check repo-wide. See [ci_policy.md](ci_policy.md).

### `service.yaml` (selector MUST match the pod labels)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <name>
  namespace: <name>
spec:
  selector:
    app: <name>
  ports:
    - port: 80
      targetPort: 8080
# type: ClusterIP by default. There is NO ingress controller yet — for external
# access use type: NodePort (reachable on a node IP, incl. over Tailscale).
```

### Need PVCs?
Use the default StorageClass `longhorn` (omit `storageClassName` or set it explicitly).

### Upstream Helm chart instead of a custom app
Use the Helm-via-Kustomize form (see [kubernetes/apps/longhorn](../kubernetes/apps/longhorn/)):
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
helmCharts:
  - name: <chart>
    repo: https://charts.example.com
    version: <pinned>
    releaseName: <name>
    namespace: <name>
    valuesFile: values.yaml
```

Add a short `README.md` in the app dir (purpose, image, notes).

## 2. Wire into the app-of-apps

### `kubernetes/clusters/in-cluster/apps/<name>.yaml`
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <name>
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/Waji-97/Home-Operation
    targetRevision: main
    path: kubernetes/apps/<name>
  destination:
    server: https://kubernetes.default.svc
    namespace: <name>
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
# Add ONLY for charts with very large CRDs or schema gaps (like longhorn):
#   syncOptions: [ServerSideApply=true]
#   metadata.annotations: argocd.argoproj.io/compare-options: ServerSideDiff=true
```

### Then add it to `kubernetes/clusters/in-cluster/kustomization.yaml`
```yaml
resources:
  - apps/<existing>.yaml
  - apps/<name>.yaml      # <- add this line
```

## 3. Validate, then commit
```bash
./scripts/validate-manifests.sh
./scripts/policy-check.sh
```
Push to `main` only when the user asks. ArgoCD's `homelab-root` picks up the new
child app automatically and deploys it.
