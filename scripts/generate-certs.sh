#!/usr/bin/env bash
# Generates this install's own Wazuh TLS certificates. They are never committed.
# Safe to re-run: existing certificates are kept.
set -euo pipefail
cd "$(dirname "$0")/.."

CERT_DIR=wazuh/config/wazuh_indexer_ssl_certs
COMPOSE_FILE=wazuh/generate-indexer-certs.yml
EXPECTED="root-ca.pem root-ca.key root-ca-manager.pem root-ca-manager.key admin.pem admin-key.pem
wazuh.indexer.pem wazuh.indexer-key.pem wazuh.manager.pem wazuh.manager-key.pem
wazuh.dashboard.pem wazuh.dashboard-key.pem"

missing() {
  for f in $EXPECTED; do
    [ -e "$CERT_DIR/$f" ] || return 0
  done
  return 1
}

if ! missing; then
  echo "==> Wazuh certificates already exist in $CERT_DIR"
  exit 0
fi

echo "==> Generating Wazuh certificates in $CERT_DIR"
docker compose -f "$COMPOSE_FILE" run --rm generator

# The generator leaves everything readable by uid 1000 only. Graylog (another uid)
# and this script need the public certificates; private keys stay locked down.
docker compose -f "$COMPOSE_FILE" run --rm --entrypoint sh generator -c \
  'chmod 755 /certificates; chmod 444 /certificates/*.pem; chmod 400 /certificates/*-key.pem /certificates/*.key'

if missing; then
  echo "==> Certificate generation did not produce every expected file" >&2
  exit 1
fi
