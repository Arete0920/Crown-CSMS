# RELEASE ENV MATRIX

| Area | Dev | Staging | Prod |
|---|---|---|---|
| Base URL | local or sandbox | pre-prod verified host | production verified host |
| Auth tokens | demo/local | staging secrets only | prod secrets only |
| School header | demo-school allowed | real staging tenant only | production tenant only |
| OpenAPI export | yes | yes | yes |
| Health/Integrity | required | required | required |
| Release-closeout status | required | required | required |
| PDF report routes | required | required | required |
| CompuWerx sandbox proof | optional | required | required before go-live |
| Playwright smoke | required | required | optional post-deploy |
| A11y smoke | required | required | required on RC |
| Mock/seed scan | required clean | required clean | required clean |