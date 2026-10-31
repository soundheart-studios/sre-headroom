# Baseline workload

Copy, then trim only with a reason. Satisfies ADR G-0003.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: APP
  namespace: NS
  labels: {app.kubernetes.io/name: APP, app.kubernetes.io/part-of: SYSTEM}
spec:
  replicas: 2
  revisionHistoryLimit: 5
  strategy: {type: RollingUpdate, rollingUpdate: {maxSurge: 25%, maxUnavailable: 0}}
  selector: {matchLabels: {app.kubernetes.io/name: APP}}
  template:
    metadata:
      labels: {app.kubernetes.io/name: APP}
    spec:
      serviceAccountName: APP
      automountServiceAccountToken: false
      securityContext: {runAsNonRoot: true, seccompProfile: {type: RuntimeDefault}}
      topologySpreadConstraints:
        - {maxSkew: 1, topologyKey: topology.kubernetes.io/zone, whenUnsatisfiable: ScheduleAnyway,
           labelSelector: {matchLabels: {app.kubernetes.io/name: APP}}}
      terminationGracePeriodSeconds: 30
      containers:
        - name: APP
          image: REGISTRY/APP:1.2.3@sha256:DIGEST
          ports: [{name: http, containerPort: 8080}]
          resources:
            requests: {cpu: 100m, memory: 128Mi}
            limits: {memory: 256Mi}
          readinessProbe: {httpGet: {path: /readyz, port: http}, periodSeconds: 5}
          livenessProbe: {httpGet: {path: /livez, port: http}, initialDelaySeconds: 10, periodSeconds: 10}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: [ALL]}
          volumeMounts: [{name: tmp, mountPath: /tmp}]
      volumes: [{name: tmp, emptyDir: {}}]
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: {name: APP, namespace: NS}
spec:
  minAvailable: 1
  selector: {matchLabels: {app.kubernetes.io/name: APP}}
```

| Field | Rule |
| --- | --- |
| CPU limit | Omit by default (throttling); set only if the namespace LimitRange requires it |
| Memory limit | Always; >= request |
| `startupProbe` | Add when boot > 10s instead of a long liveness delay |
| HPA | Set `replicas` only on first create; remove it when an HPA owns scaling |
| ServiceAccount | One per app; IRSA/Pod Identity annotation for AWS access (G-0007) |
