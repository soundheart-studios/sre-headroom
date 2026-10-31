# Kubernetes failures

Symptom -> check -> fix. Always pass `-n <ns>`.

| Symptom | Check | Fix |
| --- | --- | --- |
| CrashLoopBackOff, exit 1 / app error | `kubectl -n NS logs POD --previous --tail=100` | Fix config/env; `rollout undo` if introduced by deploy |
| CrashLoopBackOff, `OOMKilled` (exit 137) | `kubectl -n NS get pod POD -o jsonpath='{..lastState.terminated.reason}'`; `kubectl top pod` | Raise memory limit to p99 RSS + 25%; fix leak |
| Exit 137 not OOM | events for `Liveness probe failed` | Raise `initialDelaySeconds`/`failureThreshold` or add `startupProbe` |
| Exit 143 on deploy | terminationGracePeriodSeconds vs shutdown time | Handle SIGTERM; add `preStop` sleep; raise grace period |
| `CreateContainerConfigError` | `describe pod` -> missing ConfigMap/Secret key | Create key or fix `valueFrom` ref |
| `ImagePullBackOff` / `ErrImagePull` | `describe pod` event text: 401/403/not found | Fix tag/digest, `imagePullSecrets`, ECR policy, node role pull perms |
| `Pending`, `Insufficient cpu/memory` | `describe pod` events; `kubectl describe nodes \| grep -A5 Allocated` | Lower requests, scale node group, check Karpenter/CA logs |
| `Pending`, `didn't match node affinity/selector`, taints | `describe pod` | Fix selector/tolerations |
| `Pending`, `unbound PersistentVolumeClaim` | `kubectl -n NS get pvc`; StorageClass `volumeBindingMode` | Fix SC, AZ mismatch (EBS is single-AZ) |
| Ready 0/1, `Readiness probe failed` | probe path/port vs app; `kubectl -n NS exec POD -- wget -qO- localhost:PORT/PATH` | Fix probe or dependency the probe checks |
| Rollout stuck `progressDeadlineExceeded` | `rollout status`; new RS pod state | `rollout undo`; fix the new pods first |
| `Evicted` | `describe pod` -> ephemeral-storage / memory pressure | Set ephemeral-storage requests; log rotation |
| Pods restart together on one node | `kubectl get events --field-selector involvedObject.kind=Node` | Node NotReady: check kubelet, disk, ENI/IP exhaustion |
| HPA not scaling | `kubectl -n NS describe hpa` -> `unknown` metrics | metrics-server/adapter down; missing requests |
| `Too many pods` / IP exhaustion (EKS) | `aws ec2 describe-subnets` free IPs; aws-node logs | Prefix delegation, bigger subnets |
| 503 from Service, no endpoints | `kubectl -n NS get endpointslices -l kubernetes.io/service-name=SVC` | Selector/labels mismatch, pods not Ready |
