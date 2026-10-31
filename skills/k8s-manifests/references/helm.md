# Helm

| Item | Standard |
| --- | --- |
| Chart layout | `Chart.yaml` (apiVersion v2), `values.yaml`, `values-<env>.yaml`, `templates/`, `templates/_helpers.tpl` |
| Versioning | Bump `version` on any template change; `appVersion` = image tag |
| Values | Image `repository`/`tag`/`digest` separate; resources/probes in values, not hard-coded |
| Labels | `app.kubernetes.io/*` via a `_helpers.tpl` named template |
| Checksums | `checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . \| sha256sum }}` to roll on config change |
| Lint | `helm lint . -f values-<env>.yaml`; `helm template . -f values-<env>.yaml \| kubeconform -strict -summary` |
| Diff | `helm diff upgrade REL . -f values-<env>.yaml -n NS` (helm-diff plugin) |
| Upgrade | `helm upgrade --install REL . -f values-<env>.yaml -n NS --atomic --timeout 5m` (user runs; asks permission) |
| Rollback | `helm rollback REL <rev> -n NS` |
| Secrets | Never in values; External Secrets / Secrets Store CSI |
| Helm 4 | Server-side apply by default; verify plugins (`helm-diff`) support your Helm major |
