# Template only. Bind this policy only to a short-lived GitHub OIDC identity.
# It is intentionally read-only and excludes root, recovery, policy, token,
# identity, audit, and secret mutation privileges.

path "secret/data/crown/environments/{{environment}}/{{service}}" {
  capabilities = ["read"]
}

path "secret/data/crown/environments/{{environment}}/deployment" {
  capabilities = ["read"]
}

path "secret/metadata/crown/environments/{{environment}}/*" {
  capabilities = []
}

path "auth/token/create*" {
  capabilities = []
}

path "sys/policies/*" {
  capabilities = []
}

path "sys/audit*" {
  capabilities = []
}

path "sys/mounts*" {
  capabilities = []
}

path "identity/*" {
  capabilities = []
}
