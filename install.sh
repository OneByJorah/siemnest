#!/usr/bin/env bash
# siemnest bootstrap
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "==> Created .env - REQUIRED before starting:"
  echo "==>   INDEXER_ADMIN_PASSWORD / DASHBOARD_PASSWORD (openssl rand -hex 16)"
  echo "==>   GRAYLOG_PASSWORD_SECRET (openssl rand -hex 32)"
  echo "==>   GRAYLOG_ROOT_PASSWORD_SHA2 (echo -n 'pw' | sha256sum)"
  echo "==>   Optionally LLM_BASE_URL / LLM_MODEL for AI correlation."
  exit 0
fi

echo "==> Starting Graylog + Wazuh + shared OpenSearch + AI analyst + portal..."
echo "==> (first boot is heavy: image pulls + indexer bootstrap; give it 5-10 min)"
docker compose up -d --build
echo ""
echo "==> Portal            : http://127.0.0.1:8080"
echo "==> Graylog           : http://127.0.0.1:9000"
echo "==> Wazuh Dashboard   : https://127.0.0.1:443   (accept the self-signed cert)"
echo "==> AI findings       : http://127.0.0.1:8090/api/findings"
