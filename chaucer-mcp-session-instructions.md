# Chaucer MCP — New Session Instructions

The Chaucer MCP server code already exists on a branch in `chapmanwilliam/Autobookmark` at `claude/chaucer-mcp-server-VsQ5o`, inside the `chaucer-mcp/` subdirectory. Your job is to:

## 1. Port the code to this repo

Pull the files from `chapmanwilliam/Autobookmark` branch `claude/chaucer-mcp-server-VsQ5o`, subdirectory `chaucer-mcp/`. Move everything up to the root of this repo (so `src/`, `scripts/`, `data/`, `wrangler.toml`, etc. are at the top level, not nested).

You can fetch the files via the GitHub MCP tools (`get_file_contents`) or `git clone`.

Key files to port:
- `src/index.ts` — Worker entry + MCP server (Durable Object)
- `src/tools/{search,passage,works,context}.ts` — MCP tool implementations
- `src/parser/reference-parser.ts` — Flexible Chaucer reference parser
- `src/types.ts` — TypeScript interfaces
- `scripts/parse-chaucer.ts` — PDF→JSON extraction script
- `scripts/build-index.ts` — Inverted index builder
- `data/works-metadata.json` — Static metadata (all CT fragments/tales with line ranges)
- `package.json`, `package-lock.json`, `tsconfig.json`, `wrangler.toml`, `.gitignore`
- `CLAUDE.md`, `README.md`

## 2. Download and inspect the PDF

The source text is the Riverside Chaucer PDF:
https://www.dropbox.com/scl/fi/p28rgx75bkhclg8rifb2d/The-Riverside-Chaucer.pdf?rlkey=6nep2z77p6irgdvavirotjqu3&st=axnmk40q&dl=1

(Append `&dl=1` for direct download.)

Run `npm run parse -- --inspect` to check text quality on the first 20 pages. Report what you find — this determines feasibility of Phases 3-5.

## 3. Continue with Phase 3+

If PDF text quality is usable:
- **Phase 3:** Full text extraction and line number mapping for all works
- **Phase 4:** Wire up `search_chaucer`, `get_passage`, `get_work` tools to use the parsed data instead of placeholders
- **Phase 5:** Harden the reference parser to handle all flexible input formats

If PDF text quality is poor, document this in CLAUDE.md and consider using plain-text sources from digital humanities projects (Corpus of Middle English, Project Gutenberg, etc.).

## 4. Deploy

Deploy to Cloudflare Workers at `chaucer-mcp.wchapman10.workers.dev`. The `wrangler.toml` is already configured.

## Key context

- The MCP server uses `McpAgent` from `agents/mcp` (Cloudflare's agents framework) with Durable Objects
- Canterbury Tales are referenced by Fragment (I-X) + line number; Troilus by Book (I-V) + line; other works by simple line number
- All 26 tale abbreviations (GP, KnT, MilT, etc.) with line ranges are defined in `data/works-metadata.json`
- The `list_works` tool already returns live metadata; other tools return placeholders saying "run npm run parse"
- The project builds clean — verified with `wrangler deploy --dry-run` (1MB bundle)
