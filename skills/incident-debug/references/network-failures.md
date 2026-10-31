# Network failures

| Symptom | Check | Fix |
| --- | --- | --- |
| `NXDOMAIN` / `no such host` in cluster | `kubectl -n NS exec POD -- nslookup SVC.NS.svc.cluster.local`; CoreDNS logs | Fix name/namespace; scale CoreDNS; check `ndots` |
| Intermittent DNS 5s delays | conntrack races; `ndots:5` | NodeLocal DNSCache; FQDN with trailing dot |
| `connection refused` | target listening? `ss -lntp` in pod; Service targetPort | Fix port/targetPort; app bind 0.0.0.0 not 127.0.0.1 |
| `connection timed out` | SG/NACL, NetworkPolicy, route tables | Open the specific port/source; check default-deny policy |
| `connection reset by peer` | idle timeouts (NAT 350s, ALB 60s), keep-alive mismatch | TCP keep-alive below upstream idle timeout |
| TLS `x509: certificate signed by unknown authority` | `openssl s_client -connect HOST:443 -showcerts` | Mount CA bundle; fix chain |
| TLS `certificate has expired` | `openssl x509 -enddate`; cert-manager `Certificate` status | Renew; fix issuer/ACME challenge |
| Large responses hang, small OK | MTU / PMTUD blackhole (VPN, TGW 8500) | Clamp MSS; allow ICMP frag-needed |
| Cross-AZ latency / cost spike | topology-aware routing; pod spread | `trafficDistribution: PreferClose` |
| NAT gateway port exhaustion | `ErrorPortAllocation` metric | More NAT GWs / IPs; VPC endpoints for AWS APIs |
| NetworkPolicy blocks after deploy | `kubectl -n NS get networkpolicy`; labels | Add ingress/egress rule for the new label or DNS (UDP/TCP 53) |
