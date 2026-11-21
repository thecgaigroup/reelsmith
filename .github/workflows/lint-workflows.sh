#!/bin/bash
set -euo pipefail

echo "=== Linting GitHub Actions workflows ==="

for workflow in .github/workflows/*.yml; do
  echo "Checking $workflow..."
  python3 -c "import yaml, sys; yaml.safe_load(open('$workflow'))" || {
    echo "✗ $workflow has invalid YAML"
    exit 1
  }
done

echo "✓ All workflows are valid YAML"
