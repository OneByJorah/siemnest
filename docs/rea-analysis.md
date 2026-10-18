# REA Static-Analysis Notes

Packaging decisions in this repository were grounded in REA (Reverse Engineer
Anything, `rea-agents@6.7.0`) static-analysis passes plus source-level
deployment-contract review.

## graylog2-server — `graylog2-web-interface/src/`

| Field | Value |
| ----- | ----- |
| Input | JavaScript/TypeScript tree of Graylog2/graylog2-server @ main |
| Files | 4,147 relevant, 4,096 parsed, 0 parse failures |
| AST nodes | 1,361,454 |
| Findings | 27,070 |
| Evidence ID | `ev_1c8758904d0a201f4b11ae310689322cc4011b2446d303f` |

**Packaging consequence:** Graylog is a large JVM application (server modules
`graylog-storage-opensearch2/3` in the same tree, shaded OpenSearch 2.19) with
a standalone React/TypeScript web interface. Its storage layer accepts OpenSearch
2.x backends — which is the technical basis for pointing
`GRAYLOG_ELASTICSEARCH_HOSTS` at the Wazuh indexer and sharing one data plane.

## wazuh — native core

| Field | Value |
| ----- | ----- |
| Input | Wazuh/wazuh @ main (C/C++ manager + Python framework/API) |
| REA route | Not applicable to the native core without analysis engines (Ghidra/IDA); the JavaScript analyzer does not cover C/Python |

**Packaging consequence (source-level review):** the manager ships events to
its indexer via Filebeat with credentials from `INDEXER_URL` /
`INDEXER_USERNAME` / `INDEXER_PASSWORD`; the dashboard binds the indexer with
`DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD`. The compose wires exactly those
contracts, and the indexer image (OpenSearch 2.x with Wazuh plugins) doubles as
Graylog's backend.

## kumaalert push pattern (sibling project)

The ntfy push-notification integration pattern (outbound-only, self-hosted) is
documented in the twinops project: `OneByJorah/twinops`.

## Limitations

Static analysis parses source as inert text and does not prove runtime
behavior. REA's JavaScript route covers the web/UI trees; the native Wazuh core
was packaged from its documented deployment contracts instead.
