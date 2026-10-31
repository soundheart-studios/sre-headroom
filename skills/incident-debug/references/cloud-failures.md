# Cloud (AWS) failures

| Symptom | Check | Fix |
| --- | --- | --- |
| `AccessDenied` / `UnauthorizedOperation` | `aws sts get-caller-identity`; CloudTrail event `errorCode` | Correct role/IRSA annotation; add the one missing action (no wildcards) |
| IRSA pod uses node role | `kubectl -n NS get sa SA -o yaml` annotation; pod env `AWS_ROLE_ARN` | Annotate SA, restart pods; trust policy `sub` matches `system:serviceaccount:NS:SA` |
| `ThrottlingException` / `Rate exceeded` | CloudWatch `ThrottledRequests`; SDK retry config | Exponential backoff + jitter; request quota increase |
| Quota exceeded (vCPU, ENI, EIP) | `aws service-quotas get-service-quota` | Request increase; clean leaked resources |
| ALB 502 | target group health; app keep-alive < ALB idle timeout | App keep-alive > 60s; fix health check path |
| ALB 503 | no healthy targets | Fix health checks / registration (TargetGroupBinding) |
| ALB 504 | target latency > idle timeout | Raise idle timeout or fix slow path |
| RDS connection exhaustion | `DatabaseConnections` vs `max_connections` | RDS Proxy / pool sizing; kill leaked sessions |
| RDS high latency | Performance Insights top SQL; `ReadIOPS`, burst balance | Index; gp3 IOPS; instance class |
| MSK consumer lag growing | `kafka-consumer-groups --describe`; `MaxOffsetLag` | Scale consumers up to partitions; fix poison message; check rebalances |
| SQS messages in DLQ | `ApproximateNumberOfMessagesVisible` on DLQ; sample message | Fix handler, then redrive with `start-message-move-task` |
| Lambda timeouts | Duration p99 vs timeout; VPC cold start | Raise timeout; fix downstream; provisioned concurrency |
| KMS `AccessDeniedException` on decrypt | key policy + grants; encryption context | Add role to key policy |
