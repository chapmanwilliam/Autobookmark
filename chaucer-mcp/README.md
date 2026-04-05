# Chaucer MCP Server

An MCP (Model Context Protocol) server for Geoffrey Chaucer's complete works, built on Cloudflare Workers. Enables LLMs to search, retrieve, and accurately cite Chaucer by line number using the Riverside Chaucer as source text.

## Features

- **Full-text search** across all of Chaucer's works with context lines
- **Passage retrieval** by canonical reference (flexible format parsing)
- **Complete work/tale retrieval** with pagination
- **Scholarly context** — identifies work, tale, fragment, and narrative position
- **Standard abbreviations** for all Canterbury Tales (GP, KnT, MilT, etc.)

## Quick Start

```bash
cd chaucer-mcp
npm install

# Generate parsed data (requires Riverside Chaucer PDF)
# Place PDF at ./riverside-chaucer.pdf, then:
npm run parse
npm run build-index

# Local development
npm run dev

# Deploy
npm run deploy
```

## MCP Tools

### `list_works`
List all available works with their sections, tales, fragments, and line ranges.

### `search_chaucer`
Full-text search across all works.
```json
{ "query": "whan that Aprille", "work": "ct" }
```

### `get_passage`
Retrieve a specific passage by reference. Accepts flexible formats:
```
CT I.1-42          → Canterbury Tales, Fragment I, lines 1-42
KnT 1234-1300      → Knight's Tale, lines 1234-1300
Fragment I, lines 1-42
Tr II.456-500      → Troilus and Criseyde, Book II, lines 456-500
Troilus Book 2 lines 456-500
BD 1-50            → Book of the Duchess, lines 1-50
GP 1-18            → General Prologue, lines 1-18
```

### `get_work`
Retrieve an entire tale or work by ID or abbreviation.
```json
{ "id": "KnT", "page": 1 }
```

### `get_context`
Get scholarly context for a reference.
```json
{ "reference": "CT I.1500" }
```
Returns: work, tale (Knight's Tale), fragment (I), and approximate position (~64% through).

## Chaucer's Reference System

| Work | Format | Example |
|------|--------|---------|
| Canterbury Tales | Fragment.Line | CT I.43 |
| Canterbury Tales | Tale + Line | KnT 1500 |
| Troilus and Criseyde | Book.Line | Tr II.456 |
| Book of the Duchess | Line | BD 123 |
| House of Fame | Line | HF 500 |
| Parliament of Fowls | Line | PF 300 |

## Architecture

- **Runtime:** Cloudflare Workers with Durable Objects
- **Protocol:** MCP over SSE (Server-Sent Events)
- **Data:** Pre-parsed JSON embedded at build time
- **Search:** Inverted index built at preprocessing time

## Generating Data

The source text comes from a PDF of the Riverside Chaucer. The PDF is not included in the repository.

1. Obtain the Riverside Chaucer PDF
2. Place it at `./riverside-chaucer.pdf`
3. Run `npm run parse` to extract and structure the text
4. Run `npm run build-index` to build the search index
5. The generated files (`data/chaucer.json`, `data/index.json`) are gitignored

## Deployment

Deployed at: `chaucer-mcp.wchapman10.workers.dev`

Connect via MCP at endpoint `/sse` or `/mcp`.
