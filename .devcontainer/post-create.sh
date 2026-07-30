#!/usr/bin/env bash
#
# Idempotent devcontainer bootstrap. Safe to re-run at any time.
set -euo pipefail

UV_VERSION="0.11.32"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

# 1. Install the pinned uv release if it is not already available.
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv ${UV_VERSION}..."
  curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh
fi
export PATH="${HOME}/.local/bin:${PATH}"

# 2. Copy the standard VS Code configuration into place if it is not already present.
mkdir -p .vscode
for config in settings.json launch.json; do
  if [[ ! -f ".vscode/${config}" ]]; then
    echo "Provisioning .vscode/${config}..."
    cp ".devcontainer/vscode/${config}" ".vscode/${config}"
  fi
done

# 3. Install dependencies and git hooks.
make bootstrap

echo "Devcontainer bootstrap complete."
