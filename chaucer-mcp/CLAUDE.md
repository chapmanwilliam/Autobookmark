# CLAUDE.md – Chaucer MCP Server

## Overview

A Cloudflare Workers MCP (Model Context Protocol) server that serves the complete text of Geoffrey Chaucer's works from the Riverside Chaucer. Lets an LLM search, retrieve, and cite Chaucer accurately by line number.

## Architecture

```
chaucer-mcp/
  src/
    index.ts                 # Worker entry + MCP server (Durable Object)
    tools/
      search.ts              # search_chaucer tool
      passage.ts             # get_passage tool
      works.ts               # list_works, get_work tools
      context.ts             # get_context tool
    parser/
      reference-parser.ts    # Flexible reference string parser
    types.ts                 # TypeScript interfaces
  scripts/
    parse-chaucer.ts         # PDF → JSON extraction (run locally)
    build-index.ts           # Build inverted search index
  data/
    works-metadata.json      # Static metadata (checked in)
    chaucer.json             # Generated parsed text (gitignored)
    index.json               # Generated search index (gitignored)
  wrangler.toml
```

## Chaucer's Line Numbering System

**Canterbury Tales:** Referenced by Fragment (Roman numeral I–X), then line number within fragment. Each Fragment contains one or more Tales identified by teller abbreviation.
- Example: "CT I.43" = Fragment I, line 43 (General Prologue)
- Example: "KnT 1500" = Knight's Tale, which is Fragment I, line 1500

**Troilus and Criseyde:** Referenced by Book (I–V) and line within book.
- Example: "Tr II.456" = Book II, line 456

**Other works (BD, HF, PF, LGW):** Simple line number from start of work.
- Example: "BD 123" = Book of the Duchess, line 123

**Prose works (Boece, Astrolabe, Melibee, Parson's Tale):** Section/chapter reference.

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_works` | List all available works with sections and line ranges |
| `search_chaucer` | Full-text search with context lines and canonical references |
| `get_passage` | Retrieve specific passage by reference (flexible format parsing) |
| `get_work` | Retrieve entire work/tale text (paginated) |
| `get_context` | Scholarly context: work, tale, fragment, narrative position |

## Canterbury Tales Abbreviations

| Abbrev | Tale | Fragment | Lines |
|--------|------|----------|-------|
| GP | General Prologue | I | 1-858 |
| KnT | Knight's Tale | I | 859-2482 |
| MilT | Miller's Tale | I | 3187-3854 |
| RvT | Reeve's Tale | I | 3921-4324 |
| CkT | Cook's Tale | I | 4365-4422 |
| MLT | Man of Law's Tale | II | 1-1190 |
| WBP | Wife of Bath's Prologue | III | 1-856 |
| WBT | Wife of Bath's Tale | III | 857-1264 |
| FrT | Friar's Tale | III | 1265-1664 |
| SumT | Summoner's Tale | III | 1665-2294 |
| ClT | Clerk's Tale | IV | 1-1212 |
| MerT | Merchant's Tale | IV | 1213-2418 |
| SqT | Squire's Tale | V | 1-672 |
| FranT | Franklin's Tale | V | 673-1624 |
| PardT | Pardoner's Tale | VI | 287-968 |
| ShT | Shipman's Tale | VII | 1-434 |
| PrT | Prioress's Tale | VII | 435-690 |
| Thop | Sir Thopas | VII | 691-918 |
| Mel | Melibee | VII | 967-1888 |
| MkT | Monk's Tale | VII | 1889-2766 |
| NPT | Nun's Priest's Tale | VII | 2767-3446 |
| SNT | Second Nun's Tale | VIII | 1-434 |
| CYT | Canon's Yeoman's Tale | VIII | 554-1481 |
| ManT | Manciple's Tale | IX | 1-362 |
| ParsT | Parson's Tale | X | 1-1080 |
| Ret | Retraction | X | 1081-1092 |

## Regenerating Data

The PDF is **not** checked into the repo. To regenerate the parsed data:

1. Download the Riverside Chaucer PDF and place it at `riverside-chaucer.pdf`
2. Run `npm run parse` — this extracts text and writes `data/chaucer.json`
3. Run `npm run build-index` — this builds `data/index.json` for search

The parse script uses `pdfjs-dist` for text extraction. If the PDF's text layer is poor quality, consider alternative sources from digital humanities projects.

## PDF Text Quality Note

The Riverside Chaucer PDF may have variable text layer quality. The parse script includes inspection mode (`npm run parse -- --inspect`) to check the first 20 pages. If OCR quality is poor, alternatives include:
- The [Corpus of Middle English Prose and Verse](https://quod.lib.umich.edu/c/cme/)
- [The Canterbury Tales Project](https://www.canterburytalesproject.org/)
- Plain text editions from Project Gutenberg

## Development

```bash
npm install           # Install dependencies
npm run dev           # Local dev server
npm run deploy        # Deploy to Cloudflare Workers
```

## Deployment

Deployed to: `chaucer-mcp.wchapman10.workers.dev`
MCP endpoint: `/sse` or `/mcp`
