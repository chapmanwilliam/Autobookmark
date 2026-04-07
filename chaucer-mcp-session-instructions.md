# Chaucer MCP — New Session Instructions

You are working in the `chapmanwilliam/Chaucer-MCP` repo. A branch `claude/port-chaucer-mcp-W7...` already exists with the Phase 1 & 2 code ported from `chapmanwilliam/Autobookmark`. The Riverside Chaucer PDF is already committed at the repo root as `The Riverside Chaucer.pdf`.

## Goal

Continue building the Chaucer MCP server. Deploy to Cloudflare Workers at `chaucer-mcp.wchapman10.workers.dev`, freely available to anyone with the URL (no auth — this is Cloudflare Workers default behavior, just don't add auth middleware).

## 1. Check out the existing branch

```bash
git fetch origin
git checkout claude/port-chaucer-mcp-W7...   # use the actual full branch name
npm install
```

Verify the project builds:
```bash
npx wrangler deploy --dry-run
```

## 2. Fix the PDF path

The parse script (`scripts/parse-chaucer.ts`) currently expects the PDF at `riverside-chaucer.pdf`. Update it to point at `The Riverside Chaucer.pdf` at the repo root. Also update `.gitignore` if needed — the PDF IS committed to the repo and should stay that way.

## 3. Inspect PDF text quality

```bash
npm run parse -- --inspect
```

This runs the first 20 pages through `pdfjs-dist` and writes `data/pdf-inspection.txt`. **Report what you find** — character counts per page, whether line numbers are detectable, OCR artifacts, etc. This determines feasibility of the remaining phases.

If text quality is poor, document in CLAUDE.md and consider alternatives:
- [Corpus of Middle English Prose and Verse](https://quod.lib.umich.edu/c/cme/)
- [The Canterbury Tales Project](https://www.canterburytalesproject.org/)
- Project Gutenberg plain text

## 4. Phase 3: Full parse

Run `npm run parse` to extract all works. The script:
- Detects work boundaries from headings (`THE CANTERBURY TALES`, `TROILUS AND CRISEYDE`, etc.)
- Extracts line numbers from margins (printed every 5 lines in Riverside)
- Interpolates line numbers between known points
- Maps PDF pages to Riverside printed page numbers
- Splits CT into fragments and tales using hardcoded line ranges in `CT_FRAGMENTS`
- Outputs `data/chaucer.json`

Then `npm run build-index` to build the inverted index at `data/index.json`.

Expect the generated files to be large (~10-20 MB). If they exceed the Worker bundle size limit (~10 MB gzipped), split per-work JSON files or move to KV.

## 5. Phase 4: Wire up the tools

Currently `list_works` returns live metadata, but `search_chaucer`, `get_passage`, `get_work`, and `get_context` return placeholder text. Update them to read from `data/chaucer.json` and `data/index.json`:

- **`search_chaucer`**: tokenize query, look up in inverted index, return matches with 2 lines of context before/after and canonical reference strings
- **`get_passage`**: use `parseReference()` from `src/parser/reference-parser.ts`, then look up lines by work+section+line range
- **`get_work`**: return all lines for a work/tale, paginated (100 lines per page)
- **`get_context`**: already partially works via metadata; enhance with actual narrative position if possible

## 6. Phase 5: Harden the reference parser

The parser in `src/parser/reference-parser.ts` handles the main formats but may need more edge cases: lowercase abbreviations, "book" vs "Book", comma/period separators, ranges with en-dashes, etc. Add unit tests if practical.

## 7. Deploy

```bash
npm run deploy
```

Should land at `chaucer-mcp.wchapman10.workers.dev`. Test the MCP endpoint at `/sse` with an MCP client.

## Key context

- **Tech:** Cloudflare Workers + Durable Objects, `McpAgent` from `agents/mcp`, `@modelcontextprotocol/sdk`, TypeScript
- **Reference system:** Canterbury Tales = Fragment (I-X) + line; Troilus = Book (I-V) + line; other works = simple line number
- **Tale abbreviations:** All 26 (GP, KnT, MilT, RvT, CkT, MLT, WBP, WBT, FrT, SumT, ClT, MerT, SqT, FranT, PardT, ShT, PrT, Thop, Mel, MkT, NPT, SNT, CYT, ManT, ParsT, Ret) are in `data/works-metadata.json` with line ranges
- **No auth:** Worker is publicly accessible by default. Don't add any auth — user wants it freely available.
- **PDF is committed:** Unlike the original plan, the PDF is in the repo, so the parse step is reproducible without external downloads.

## Quick start for the new session

```bash
git fetch origin
git checkout claude/port-chaucer-mcp-W7...
npm install
# Fix PDF filename in scripts/parse-chaucer.ts
npm run parse -- --inspect
# Report findings, then proceed with full parse and tool wire-up
```
