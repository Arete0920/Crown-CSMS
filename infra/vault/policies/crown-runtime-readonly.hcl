# Template only. Replace environment and service placeholders before external deployment.
# This policy intentionally excludes list, create, update, patch, delete, sudo,
# identity administration, token creation, policy administration, and audit control.

path "secret/data/crown/environments/{{environment}}/{{service}}" {
  capabilities = ["read"]
}

path "secret/data/crown/environments/{{environment}}/tenants/{{tenant_id}}" {
  capabilities = ["read"]
}

path "secret/metadata/crown/environments/{{environment}}/{{service}}" {
  capabilities = []
}

path "secret/metadata/crown/environments/{{environment}}/tenants/{{tenant_id}}" {
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

path "identity/*" {
  capabilities = []
}
