#!/usr/bin/env bash
# ============================================================
# Crown2026 — Azure VM Self-Hosted Runner Setup
# Target:  Ubuntu 22.04 LTS, Standard_D2as_v5 (2 vCPU / 8GB minimum)
#          Recommended: Standard_D4as_v5 (4 vCPU / 16GB)
# Runner:  crown-ubuntu-01  labels: crown-runner
#
# ⚠️  Run as a sudo-capable user (NOT as root directly).
# ⚠️  phase3-runtime-proof AND proof-ceremony use postgres
#     service containers → Docker is MANDATORY.
# ⚠️  Runner version MUST be >= 2.329.0 (GitHub min enforcement Mar 16 2026).
#
# Usage:
#   1. Copy this file to the VM (scp or paste into nano).
#   2. chmod +x setup_crown_runner.sh
#   3. sudo ./setup_crown_runner.sh
#   4. Follow the "RUNNER REGISTRATION" section manually (needs a token).
# ============================================================
set -euo pipefail

RUNNER_NAME="crown-ubuntu-01"
RUNNER_USER="actions"
RUNNER_DIR="/home/${RUNNER_USER}/actions-runner"
REPO_URL="https://github.com/Arete0920/Crown-CSMS"
MINIMUM_RUNNER_VER="2.329.0"

# Override: RUNNER_VER=2.329.0 ./setup_crown_runner.sh
# If unset, script auto-fetches latest from GitHub API.
RUNNER_VER="${RUNNER_VER:-}"

echo "=== [1/7] System update ==="
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y \
  curl jq git ca-certificates gnupg \
  build-essential \
  python3 python3-venv python3-pip \
  unzip

echo "=== [2/7] Python 3.12 (deadsnakes PPA) ==="
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
python3 --version

echo "=== [3/7] Node 20 LTS ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version && npm --version

echo "=== [4/7] Docker — official install (required for postgres service containers) ==="
# Using get.docker.com (official), NOT docker.io (Ubuntu package is older)
# phase3-runtime-proof and proof-ceremony both use services.postgres
# Idempotent: skip if docker is already installed
if command -v docker &>/dev/null; then
  echo "Docker already installed: $(docker --version) — skipping"
else
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo systemctl enable --now docker
sudo systemctl status docker --no-pager
docker --version

echo "=== [5/7] Dedicated runner user: ${RUNNER_USER} ==="
# Idempotent: only create if user does not exist
id -u "${RUNNER_USER}" >/dev/null 2>&1 || sudo adduser --disabled-password --gecos "" "${RUNNER_USER}"

# Ensure docker group exists (get.docker.com creates it, but guard for re-runs)
getent group docker >/dev/null 2>&1 || sudo groupadd docker

# Docker group membership is REQUIRED for service containers
sudo usermod -aG sudo "${RUNNER_USER}"
sudo usermod -aG docker "${RUNNER_USER}"
echo "Groups for ${RUNNER_USER}: $(id ${RUNNER_USER})"

# Verify Docker access as the runner user — hard fail if not working.
# Group membership requires a fresh login session to apply; sudo su - provides that.
echo "--- verifying docker access as ${RUNNER_USER} ---"
sudo su - "${RUNNER_USER}" -c "id | grep -q '\bdocker\b' && docker ps" || {
  echo "ERROR: ${RUNNER_USER} cannot access Docker. Re-login session needed."
  echo "Fix: sudo -iu ${RUNNER_USER}; id && docker ps"
  exit 1
}

echo "=== [6/7] Download GitHub Actions runner (>= ${MINIMUM_RUNNER_VER} required) ==="
sudo -u "${RUNNER_USER}" bash <<RUNNER_SETUP
set -euo pipefail
RUNNER_DIR="${RUNNER_DIR}"
MINIMUM_RUNNER_VER="${MINIMUM_RUNNER_VER}"
RUNNER_VER_OVERRIDE="${RUNNER_VER}"
mkdir -p "\${RUNNER_DIR}"
cd "\${RUNNER_DIR}"

# Idempotent: skip download if runner config.sh already present
if [ -f "\${RUNNER_DIR}/config.sh" ]; then
  echo "Runner already downloaded at \${RUNNER_DIR} — skipping download"
  RUNNER_SETUP_DONE=1
else
  RUNNER_SETUP_DONE=0
fi

if [ "\${RUNNER_SETUP_DONE}" = "0" ]; then
  # Resolve version: use override if set, else fetch latest from GitHub API
  if [ -n "\${RUNNER_VER_OVERRIDE}" ]; then
    VER="\${RUNNER_VER_OVERRIDE}"
    echo "Using override runner version: \${VER}"
  else
    API_RESPONSE=\$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest 2>/dev/null || true)
    VER=\$(echo "\${API_RESPONSE}" | jq -r .tag_name 2>/dev/null | sed 's/^v//' || true)
    if [ -z "\${VER}" ] || [ "\${VER}" = "null" ]; then
      echo "ERROR: GitHub API returned empty version. Set RUNNER_VER=x.y.z and re-run."
      exit 1
    fi
    echo "Auto-fetched runner version: \${VER}"
  fi

  # Enforce minimum version
  python3 -c "
import sys
v = tuple(int(x) for x in '\${VER}'.split('.'))
m = tuple(int(x) for x in '\${MINIMUM_RUNNER_VER}'.split('.'))
if v < m:
    print(f'ERROR: Runner {v} is below minimum {m}. Set RUNNER_VER to a compliant version.')
    sys.exit(1)
print(f'Version check OK: {v} >= {m}')
"

  curl -fsSL -o actions-runner.tar.gz \
    "https://github.com/actions/runner/releases/download/v\${VER}/actions-runner-linux-x64-\${VER}.tar.gz"
  tar xzf actions-runner.tar.gz
  rm actions-runner.tar.gz
  echo "Runner binaries extracted to \${RUNNER_DIR}"
fi
RUNNER_SETUP

echo "=== [7/7] Hardening ==="

# A) Prevent needrestart from restarting the runner service mid-job
if dpkg -l needrestart &>/dev/null 2>&1; then
  echo '$nrconf{override_rc}{qr(^actions\.runner\..+\.service$)} = 0;' \
    | sudo tee /etc/needrestart/conf.d/actions_runner_services.conf
  echo "needrestart: runner service protected"
fi

# B) Disable SSH password auth (already using keys)
sudo sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
echo "SSH password auth disabled"

# C) Add 4GB swap (guards against OOM on npm/pytest build spikes)
if [ ! -f /swapfile ]; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo "Swap: $(free -h | grep Swap)"
else
  echo "Swap already configured — skipping"
fi

echo ""
echo "============================================================"
echo "  RUNNER REGISTRATION — manual step required"
echo "============================================================"
echo ""
echo "1. Get a registration token (expires in 1 hour — run this LOCALLY):"
echo "   gh api repos/Arete0920/Crown-CSMS/actions/runners/registration-token --method POST --jq .token"
echo ""
echo "2. Register the runner (run as ${RUNNER_USER}):"
echo ""
echo "   sudo -iu ${RUNNER_USER}"
echo "   id && docker ps          # must show docker group + no errors"
echo "   cd ~/actions-runner"
echo "   ./config.sh \\"
echo "     --url ${REPO_URL} \\"
echo "     --token <PASTE_TOKEN_HERE> \\"
echo "     --name ${RUNNER_NAME} \\"
echo "     --labels crown-runner \\"
echo "     --work _work \\"
echo "     --unattended"
echo ""
echo "3. Install and start the systemd service (exit back to azureuser first):"
echo ""
echo "   exit   # back to azureuser"
echo "   cd ${RUNNER_DIR}"
echo "   sudo ./svc.sh install ${RUNNER_USER}"
echo "   sudo ./svc.sh start"
echo "   sudo ./svc.sh status"
echo ""
echo "4. Hardening — prevent needrestart killing runner mid-job (already done above if needrestart is installed)"
echo ""
echo "5. GO checks (all 4 must pass before merging the workflow branch):"
echo "   sudo systemctl status docker --no-pager"
echo "   sudo su - ${RUNNER_USER} -c \"id && docker ps\""
echo "   # Runner service status (deterministic unit name discovery):"
echo "   UNIT=\$(systemctl list-unit-files | awk '/actions\.runner\..+\.service/ {print \$1; exit}')"
echo "   [ -n \"\${UNIT:-}\" ] && sudo systemctl status \"\$UNIT\" --no-pager || echo 'runner service not found'"
echo "   # locally: gh api repos/Arete0920/Crown-CSMS/actions/runners --jq '.runners[] | {name:.name,status:.status,labels:[.labels[].name]}'"
echo "   # → must show status:online + label crown-runner"
echo ""
echo "6. Merge the workflow branch ONLY after runner is online:"
echo "   Branch: ci/self-hosted-crown-runner"
echo "   PR URL: https://github.com/Arete0920/Crown-CSMS/pull/new/ci/self-hosted-crown-runner"
echo ""
echo "=== Setup complete ==="
