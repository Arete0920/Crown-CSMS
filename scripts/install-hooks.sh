#!/usr/bin/env bash
# install-hooks.sh
# Installs Git hooks from scripts/hooks/ into .git/hooks/
# Run once after cloning the repo (Linux/Mac)

set -euo pipefail

echo ""
echo "🔧 Installing Git hooks..."

# Check if we're in the repo root
if [ ! -d ".git/hooks" ]; then
    echo "❌ Error: .git/hooks not found. Are you in the repo root?"
    exit 1
fi

# Check if hook source exists
if [ ! -f "scripts/hooks/pre-commit" ]; then
    echo "❌ Error: scripts/hooks/pre-commit not found"
    exit 1
fi

# Create hooks directory if needed
mkdir -p .git/hooks

# Copy pre-commit hook
cp -f scripts/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "✓ Installed pre-commit hook"

# Make hook executable
chmod +x .git/hooks/pre-commit
echo "✓ Made hook executable"

echo ""
echo "✅ Git hooks installed successfully!"
echo "   Hooks will run automatically on commit."
echo "   To bypass (NOT RECOMMENDED): git commit --no-verify"
