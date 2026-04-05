#!/usr/bin/env npx tsx
/**
 * build-index.ts
 *
 * Builds a simple inverted index from chaucer.json for fast full-text search.
 * Run: npx tsx scripts/build-index.ts
 *
 * Output: data/index.json
 */

import * as fs from "fs";
import * as path from "path";

const DATA_DIR = path.join(__dirname, "..", "data");
const INPUT_PATH = path.join(DATA_DIR, "chaucer.json");
const OUTPUT_PATH = path.join(DATA_DIR, "index.json");

interface ChaucerLine {
  lineNumber: number;
  text: string;
  page: number;
}

interface ChaucerSection {
  id: string;
  title: string;
  fragment?: string;
  book?: string;
  tale?: string;
  startPage: number;
  lines: ChaucerLine[];
}

interface ChaucerWork {
  id: string;
  title: string;
  abbreviation: string;
  sections: ChaucerSection[];
}

interface IndexEntry {
  workId: string;
  sectionId: string;
  lineNumber: number;
}

type InvertedIndex = Record<string, IndexEntry[]>;

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s'-]/g, "")
    .split(/\s+/)
    .filter((t) => t.length > 1);
}

function buildIndex(): void {
  if (!fs.existsSync(INPUT_PATH)) {
    console.error(`chaucer.json not found at ${INPUT_PATH}`);
    console.error("Run 'npm run parse' first to generate the data.");
    process.exit(1);
  }

  console.log("Loading chaucer.json...");
  const works: ChaucerWork[] = JSON.parse(fs.readFileSync(INPUT_PATH, "utf-8"));

  const index: InvertedIndex = {};
  let totalLines = 0;
  let totalTokens = 0;

  for (const work of works) {
    for (const section of work.sections) {
      for (const line of section.lines) {
        totalLines++;
        const tokens = tokenize(line.text);

        for (const token of tokens) {
          totalTokens++;
          if (!index[token]) {
            index[token] = [];
          }
          index[token].push({
            workId: work.id,
            sectionId: section.id,
            lineNumber: line.lineNumber,
          });
        }
      }
    }
  }

  // Deduplicate entries per token
  for (const token of Object.keys(index)) {
    const seen = new Set<string>();
    index[token] = index[token].filter((entry) => {
      const key = `${entry.workId}:${entry.sectionId}:${entry.lineNumber}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  const output = JSON.stringify(index);
  fs.writeFileSync(OUTPUT_PATH, output, "utf-8");

  const sizeMB = (Buffer.byteLength(output) / 1024 / 1024).toFixed(2);
  const uniqueTokens = Object.keys(index).length;
  console.log(`\nIndex built successfully:`);
  console.log(`  Lines indexed: ${totalLines}`);
  console.log(`  Total token occurrences: ${totalTokens}`);
  console.log(`  Unique tokens: ${uniqueTokens}`);
  console.log(`  Output: ${OUTPUT_PATH} (${sizeMB} MB)`);
}

buildIndex();
