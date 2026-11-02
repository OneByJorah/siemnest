#!/usr/bin/env bash
# siemnest bootstrap
set -euo pipefail
cd "$(dirname "$0")"

./scripts/generate-secrets.sh
./scripts/generate-certs.sh

echo "==> Secrets are in .env. Optionally set LLM_BASE_URL / LLM_MODEL there for AI correlation."
echo "==> Starting Graylog + Wazuh + shared OpenSearch + AI analyst + portal..."
echo "==> (first boot is heavy: image pulls + indexer bootstrap; give it 5-10 min)"
docker compose up -d --build
echo ""
echo "==> Portal            : http://127.0.0.1:8082"
echo "==> Graylog           : http://127.0.0.1:9091"
echo "==> Wazuh Dashboard   : https://127.0.0.1:443   (accept the self-signed cert)"
echo "==> AI findings       : http://127.0.0.1:8091/api/findings"
