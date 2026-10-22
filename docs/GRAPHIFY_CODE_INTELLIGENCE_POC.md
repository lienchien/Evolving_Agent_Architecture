# Graphify Code Intelligence — Phase 1.5 Parallel PoC

**Status:** opt-in developer tooling / PoC, **not** integrated with CEAA runtime; no phase exit gate depends on it.

**Architecture baseline:** `Capability-Evolving Agent Architecture — System Design v1.9.md`

## Objective and scope

Build a **local repository code graph** during early Phase 1.5 development, in parallel with telemetry/database hardening and the future Pi/OpenCode Builder work. Use it for repository understanding, dependency/impact discovery, and later controlled Builder context retrieval. Do not confuse Graphify's *code graph* with CEAA's Agent/Capability ownership graph, routing history, or execution experience.

```text
CEAA Repository (source code)
  -> Graphify local AST/code-only extraction
  -> graphify-out/graph.json (local and untracked)
  -> graphify query / explain / path
  -> developer / future Pi or OpenCode Builder (candidate context)
  -> CEAA-owned sandbox, validation, Main/Audit, and policy
```

This does **not** introduce Graphify into `requirements.txt`, startup, API service, database migrations, agent orchestration, or mandatory test pipelines. The phase 1 telemetry instrumentation and PostgreSQL work remain independent.

## Setup: local and code-only first

Prerequisite: Python 3.10+ and `uv` or `pipx`. On Windows PowerShell in the CEAA repository root:

```powershell
uv tool install graphifyy
graphify --help
graphify extract . --code-only
graphify explain "MainAgent"
graphify query "Which modules call the capability registry?"
```

Or run the checked-in proof-of-concept runner after installing the CLI:

```powershell
py -3 scripts/graphify_poc.py --repo .
py -3 scripts/graphify_poc.py --repo . --skip-extract --query "What depends on CapabilityRegistry?"
```

The script explicitly sets `GRAPHIFY_BACKEND=none` and uses `--code-only` for extraction. It writes a local smoke-test summary to `graphify-out/ceaa-graphify-poc.json`.

Optional interactive assistant use:

```powershell
graphify install
# Then run /graphify . inside a compatible coding assistant
```

For local MCP, install the `mcp` extra and connect the local graph, **not** Graphify Cloud by default:

```powershell
uv tool install "graphifyy[mcp]"
graphify extract . --code-only
# Configure your MCP client's stdio command as:
# python -m graphify.serve graphify-out/graph.json
```

When using `uv tool install`, the MCP module must be invoked in the tool's Python environment (for example via `uvx --from "graphifyy[mcp]" python -m graphify.serve` if supported by your environment), rather than assuming your project `.venv` contains it. Follow the official client-specific setup guide and pin a tested version before CI/automation.

**Expected artifacts** under `graphify-out/` (ignored by Git): `graph.json`, optionally `graph.html` and `GRAPH_REPORT.md`. Headless code-only extraction may not produce every visualization/report that assistant mode produces.

## Candidate CEAA boundary (later, not implemented)

```text
CodeKnowledgeInterface
  |- GraphifyCodeKnowledgeAdapter [candidate]
  |- NativeRepositorySearch      [baseline]
  |- FutureAlternativeAdapter

Inputs:
  repo_revision, task_id, query, max_nodes, max_tokens,
  allowed_paths, allowed_labels, freshness_requirement

Outputs:
  selected_subgraph, source file/line, edge provenance,
  graph_schema_version, graphify_version, indexed_revision,
  missing_or_ambiguous_matches, elapsed_ms
```

Graphify reports `EXTRACTED` and `INFERRED` relationships. They are **context evidence, not verified runtime truth**. All edges must be treated as potentially incomplete/stale, especially dynamic imports, reflection, generated code, and runtime-only dependencies. Never use graph output to authorize credentials, decide security PASS, or bypass regression tests.

Refresh/rebuild when `git` branch, worktree, source revision, ignore rules, or relevant dependencies change. For self-generated Skills, the Builder should index its **disposable candidate workspace**, not confuse the developer's baseline graph with modified code.

## Nonblocking PoC acceptance checks

1. `graphify extract . --code-only` completes without a model API key; Graphify-generated output stays local and untracked.
2. `graph.json` parses as JSON and its schema/version metadata can be inspected.
3. Verify `explain`, `query` and `path` on 5–10 known relationships; manually check original file/line evidence and record false / missed links.
4. Rebuild after changing a file and confirm no stale graph is passed to Builder.
5. Compare a small fixed task set **without Graphify (grep/read)** vs **with Graphify** using identical model, context budget and repo revision. Measure repository exploration latency, extractions, token spend, first-pass success, path/impact recall and false-positive relation rate.
6. Retain a fallback to normal repository search when Graphify is missing, times out, or returns ambiguous/stale evidence.

**No claims of lower tokens, greater accuracy, or completed Pi/OpenCode integration until benchmark results exist.**

## Privacy, security, and lifecycle

- Code-only local AST extraction avoids external LLM calls. Document/media semantic extraction may send content to configured AI providers: do not enable it by default for sensitive CEAA material.
- Inspect generated knowledge graphs before sharing: graph metadata, file paths and symbol names may reveal proprietary implementation detail.
- Do not commit graph snapshots, access tokens, corpus content, or detailed local query logs.
- Keep Graphify's optional MCP tool **read-only** from the perspective of CEAA authority: it can supply context, not execute privileged CEAA actions.
- Pi / OpenCode construction and Main/Audit reviewer sessions remain independent; Secure Evolution Gate is **Main PASS AND Audit PASS**, with mandatory human escalation for any failure/unknown/disagreement.
- Prefer version-pinned releases and check command/JSON schema compatibility before promoting to a runtime adapter.

## References

- Open source: https://github.com/Graphify-Labs/graphify
- Headless extraction: https://github.com/Graphify-Labs/docs/blob/main/guides/headless-extraction.mdx
- MCP: https://graphify.com/mcp
