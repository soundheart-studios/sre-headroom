# Kubernetes version notes

Verify on the target cluster: `kubectl version` and `kubectl api-resources`. Check the official
deprecation guide for anything not listed; do not recall.

| Version | Change | Action |
| --- | --- | --- |
| 1.25 | PodSecurityPolicy removed; `batch/v1beta1` CronJob removed | Pod Security Admission labels; `batch/v1` |
| 1.26 | `autoscaling/v2beta2` HPA removed | `autoscaling/v2` |
| 1.29 | `flowcontrol.apiserver.k8s.io/v1beta2` removed | `v1` (1.29+) |
| 1.32 | `flowcontrol.apiserver.k8s.io/v1beta3` removed | `v1` |
| 1.33 | Sidecar containers GA (`initContainers` with `restartPolicy: Always`); core `v1` Endpoints deprecated | Use native sidecars; read EndpointSlices |
| 1.33 | In-place pod resize beta | `kubectl patch --subresource resize` |
| EKS | Standard support ~14 months per minor; extended support costs extra | `aws eks describe-cluster --query cluster.version` |

Removed APIs in manifests: `kubectl convert` is not bundled; use `pluto detect-files -d .` or `kubent`.
