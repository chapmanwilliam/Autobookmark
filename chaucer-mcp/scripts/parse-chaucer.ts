#!/usr/bin/env npx tsx
/**
 * parse-chaucer.ts
 *
 * Downloads and parses the Riverside Chaucer PDF into structured JSON.
 * Run: npx tsx scripts/parse-chaucer.ts
 *
 * This script:
 * 1. Downloads the PDF from Dropbox (if not already present)
 * 2. Extracts text page-by-page using pdfjs-dist
 * 3. Identifies work/section boundaries from headings
 * 4. Extracts and interpolates line numbers
 * 5. Outputs structured JSON to data/chaucer.json
 */

import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

const PDF_URL =
  "https://www.dropbox.com/scl/fi/p28rgx75bkhclg8rifb2d/The-Riverside-Chaucer.pdf?rlkey=6nep2z77p6irgdvavirotjqu3&st=axnmk40q&dl=1";
const PDF_PATH = path.join(__dirname, "..", "riverside-chaucer.pdf");
const OUTPUT_DIR = path.join(__dirname, "..", "data");
const OUTPUT_PATH = path.join(OUTPUT_DIR, "chaucer.json");
const INSPECT_PATH = path.join(OUTPUT_DIR, "pdf-inspection.txt");

// ── Interfaces ──────────────────────────────────────────────────────

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

// ── Canterbury Tales Fragment/Tale definitions ──────────────────────

interface TaleDef {
  tale: string;
  title: string;
  lineStart: number;
  lineEnd: number;
}

interface FragmentDef {
  fragment: string;
  tales: TaleDef[];
}

const CT_FRAGMENTS: FragmentDef[] = [
  {
    fragment: "I",
    tales: [
      { tale: "GP", title: "General Prologue", lineStart: 1, lineEnd: 858 },
      { tale: "KnT", title: "The Knight's Tale", lineStart: 859, lineEnd: 2482 },
      { tale: "MilT", title: "The Miller's Tale", lineStart: 3187, lineEnd: 3854 },
      { tale: "RvT", title: "The Reeve's Tale", lineStart: 3921, lineEnd: 4324 },
      { tale: "CkT", title: "The Cook's Tale", lineStart: 4365, lineEnd: 4422 },
    ],
  },
  {
    fragment: "II",
    tales: [
      { tale: "MLT", title: "The Man of Law's Tale", lineStart: 1, lineEnd: 1190 },
    ],
  },
  {
    fragment: "III",
    tales: [
      { tale: "WBP", title: "Wife of Bath's Prologue", lineStart: 1, lineEnd: 856 },
      { tale: "WBT", title: "The Wife of Bath's Tale", lineStart: 857, lineEnd: 1264 },
      { tale: "FrT", title: "The Friar's Tale", lineStart: 1265, lineEnd: 1664 },
      { tale: "SumT", title: "The Summoner's Tale", lineStart: 1665, lineEnd: 2294 },
    ],
  },
  {
    fragment: "IV",
    tales: [
      { tale: "ClT", title: "The Clerk's Tale", lineStart: 1, lineEnd: 1212 },
      { tale: "MerT", title: "The Merchant's Tale", lineStart: 1213, lineEnd: 2418 },
    ],
  },
  {
    fragment: "V",
    tales: [
      { tale: "SqT", title: "The Squire's Tale", lineStart: 1, lineEnd: 672 },
      { tale: "FranT", title: "The Franklin's Tale", lineStart: 673, lineEnd: 1624 },
    ],
  },
  {
    fragment: "VI",
    tales: [
      { tale: "PardT", title: "The Pardoner's Tale", lineStart: 287, lineEnd: 968 },
    ],
  },
  {
    fragment: "VII",
    tales: [
      { tale: "ShT", title: "The Shipman's Tale", lineStart: 1, lineEnd: 434 },
      { tale: "PrT", title: "The Prioress's Tale", lineStart: 435, lineEnd: 690 },
      { tale: "Thop", title: "Sir Thopas", lineStart: 691, lineEnd: 918 },
      { tale: "Mel", title: "The Tale of Melibee", lineStart: 967, lineEnd: 1888 },
      { tale: "MkT", title: "The Monk's Tale", lineStart: 1889, lineEnd: 2766 },
      { tale: "NPT", title: "The Nun's Priest's Tale", lineStart: 2767, lineEnd: 3446 },
    ],
  },
  {
    fragment: "VIII",
    tales: [
      { tale: "SNT", title: "The Second Nun's Tale", lineStart: 1, lineEnd: 434 },
      { tale: "CYT", title: "The Canon's Yeoman's Tale", lineStart: 554, lineEnd: 1481 },
    ],
  },
  {
    fragment: "IX",
    tales: [
      { tale: "ManT", title: "The Manciple's Tale", lineStart: 1, lineEnd: 362 },
    ],
  },
  {
    fragment: "X",
    tales: [
      { tale: "ParsT", title: "The Parson's Tale", lineStart: 1, lineEnd: 1080 },
      { tale: "Ret", title: "Chaucer's Retraction", lineStart: 1081, lineEnd: 1092 },
    ],
  },
];

// ── PDF Download ────────────────────────────────────────────────────

async function downloadPdf(): Promise<void> {
  if (fs.existsSync(PDF_PATH)) {
    console.log(`PDF already exists at ${PDF_PATH}`);
    return;
  }

  console.log("Downloading Riverside Chaucer PDF...");
  console.log("(This is a large file and may take several minutes)");

  try {
    execSync(`curl -L -o "${PDF_PATH}" "${PDF_URL}"`, {
      stdio: "inherit",
      timeout: 600_000,
    });
    console.log("Download complete.");
  } catch (e) {
    console.error("Failed to download PDF via curl. Please download manually:");
    console.error(`  URL: ${PDF_URL}`);
    console.error(`  Save to: ${PDF_PATH}`);
    process.exit(1);
  }
}

// ── PDF Text Extraction ─────────────────────────────────────────────

interface PageText {
  pageNum: number; // 1-indexed PDF page number
  text: string;
}

async function extractPdfText(): Promise<PageText[]> {
  // Dynamic import for pdfjs-dist (ES module)
  const pdfjsLib = await import("pdfjs-dist/legacy/build/pdf.mjs");

  console.log(`Loading PDF from ${PDF_PATH}...`);
  const data = new Uint8Array(fs.readFileSync(PDF_PATH));
  const doc = await pdfjsLib.getDocument({ data }).promise;
  const numPages = doc.numPages;
  console.log(`PDF has ${numPages} pages.`);

  const pages: PageText[] = [];

  for (let i = 1; i <= numPages; i++) {
    if (i % 100 === 0) console.log(`  Extracting page ${i}/${numPages}...`);
    const page = await doc.getPage(i);
    const content = await page.getTextContent();
    const text = content.items
      .map((item: any) => ("str" in item ? item.str : ""))
      .join(" ");
    pages.push({ pageNum: i, text });
  }

  return pages;
}

// ── Text Quality Inspection ─────────────────────────────────────────

function inspectPages(pages: PageText[]): void {
  console.log("\n=== PDF TEXT INSPECTION (first 20 pages) ===\n");

  const inspectionLines: string[] = [];

  for (let i = 0; i < Math.min(20, pages.length); i++) {
    const p = pages[i];
    const header = `--- Page ${p.pageNum} ---`;
    const preview = p.text.substring(0, 500);
    const charCount = p.text.length;
    const hasText = charCount > 50;

    console.log(header);
    console.log(`  Characters: ${charCount}, Has meaningful text: ${hasText}`);
    console.log(`  Preview: ${preview.substring(0, 200)}...\n`);

    inspectionLines.push(header);
    inspectionLines.push(`Characters: ${charCount}`);
    inspectionLines.push(`Has text: ${hasText}`);
    inspectionLines.push(`Full preview:\n${preview}\n`);
  }

  // Check for line numbers in the text
  const lineNumPattern = /\b\d{1,4}\b/g;
  let pagesWithLineNums = 0;
  for (const p of pages.slice(0, 50)) {
    const matches = p.text.match(lineNumPattern);
    if (matches && matches.length > 3) pagesWithLineNums++;
  }

  const summary = [
    "\n=== SUMMARY ===",
    `Total pages: ${pages.length}`,
    `Pages with potential line numbers (first 50): ${pagesWithLineNums}/50`,
    `Average chars per page: ${Math.round(pages.reduce((s, p) => s + p.text.length, 0) / pages.length)}`,
    `Empty pages: ${pages.filter((p) => p.text.length < 50).length}`,
  ].join("\n");

  console.log(summary);
  inspectionLines.push(summary);

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(INSPECT_PATH, inspectionLines.join("\n"), "utf-8");
  console.log(`\nInspection saved to ${INSPECT_PATH}`);
}

// ── Line Number Detection & Parsing ─────────────────────────────────

/**
 * Detect line numbers in margin text. Riverside Chaucer typically prints
 * line numbers every 5 lines in the left or right margin.
 */
function extractLineNumbers(text: string): Map<number, number> {
  // Pattern: standalone numbers that look like line numbers (typically 1-9999)
  // They appear at line boundaries, often preceded/followed by whitespace
  const lineNums = new Map<number, number>();

  const lines = text.split(/\n/);
  let currentLineNum = 0;

  for (let i = 0; i < lines.length; i++) {
    // Look for margin line numbers: a number at the start or end of a line
    const startMatch = lines[i].match(/^\s*(\d{1,4})\s+\S/);
    const endMatch = lines[i].match(/\S\s+(\d{1,4})\s*$/);

    const num = startMatch
      ? parseInt(startMatch[1])
      : endMatch
        ? parseInt(endMatch[1])
        : null;

    if (num !== null && num > currentLineNum && num < 10000) {
      lineNums.set(i, num);
      currentLineNum = num;
    }
  }

  return lineNums;
}

/**
 * Interpolate line numbers for lines between explicitly numbered ones.
 * Chaucer typically numbers every 5th line.
 */
function interpolateLineNumbers(
  textLines: string[],
  knownLineNums: Map<number, number>
): ChaucerLine[] {
  const result: ChaucerLine[] = [];
  const sortedKnown = [...knownLineNums.entries()].sort((a, b) => a[0] - b[0]);

  if (sortedKnown.length === 0) {
    // No line numbers found; assign sequential numbers
    return textLines
      .filter((t) => t.trim().length > 0)
      .map((text, i) => ({ lineNumber: i + 1, text: text.trim(), page: 0 }));
  }

  // Interpolate between known points
  for (let i = 0; i < sortedKnown.length - 1; i++) {
    const [idx1, num1] = sortedKnown[i];
    const [idx2, num2] = sortedKnown[i + 1];
    const linesBetween = idx2 - idx1;
    const numDiff = num2 - num1;

    for (let j = idx1; j < idx2; j++) {
      const frac = (j - idx1) / linesBetween;
      const lineNum = Math.round(num1 + frac * numDiff);
      if (textLines[j].trim().length > 0) {
        result.push({
          lineNumber: lineNum,
          text: textLines[j].trim(),
          page: 0, // Will be set later
        });
      }
    }
  }

  // Handle lines after last known number
  const [lastIdx, lastNum] = sortedKnown[sortedKnown.length - 1];
  let nextNum = lastNum;
  for (let j = lastIdx; j < textLines.length; j++) {
    if (textLines[j].trim().length > 0) {
      result.push({
        lineNumber: nextNum++,
        text: textLines[j].trim(),
        page: 0,
      });
    }
  }

  return result;
}

// ── Work Detection ──────────────────────────────────────────────────

/**
 * Heuristic patterns to detect the start of major works in the PDF.
 * These are based on common headings in the Riverside Chaucer.
 */
const WORK_HEADINGS: Array<{
  pattern: RegExp;
  workId: string;
  title: string;
  abbreviation: string;
}> = [
  { pattern: /THE\s+CANTERBURY\s+TALES/i, workId: "ct", title: "The Canterbury Tales", abbreviation: "CT" },
  { pattern: /GENERAL\s+PROLOGUE/i, workId: "ct-gp", title: "General Prologue", abbreviation: "CT" },
  { pattern: /THE\s+KNIGHT['']?S\s+TALE/i, workId: "ct-knt", title: "The Knight's Tale", abbreviation: "CT" },
  { pattern: /THE\s+MILLER['']?S\s+(?:PROLOGUE|TALE)/i, workId: "ct-milt", title: "The Miller's Tale", abbreviation: "CT" },
  { pattern: /TROILUS\s+AND\s+CRISEYDE/i, workId: "troilus", title: "Troilus and Criseyde", abbreviation: "Tr" },
  { pattern: /THE\s+BOOK\s+OF\s+THE\s+DUCHESS/i, workId: "bd", title: "The Book of the Duchess", abbreviation: "BD" },
  { pattern: /THE\s+HOUSE\s+OF\s+FAME/i, workId: "hf", title: "The House of Fame", abbreviation: "HF" },
  { pattern: /THE\s+PARLIAMENT\s+OF\s+FOWLS/i, workId: "pf", title: "The Parliament of Fowls", abbreviation: "PF" },
  { pattern: /THE\s+LEGEND\s+OF\s+GOOD\s+WOMEN/i, workId: "lgw", title: "The Legend of Good Women", abbreviation: "LGW" },
  { pattern: /BOECE/i, workId: "boece", title: "Boece", abbreviation: "Bo" },
  { pattern: /TREATISE\s+ON\s+THE\s+ASTROLABE/i, workId: "astr", title: "A Treatise on the Astrolabe", abbreviation: "Astr" },
];

// ── Main Parse Pipeline ─────────────────────────────────────────────

async function parsePdf(inspectOnly: boolean): Promise<void> {
  await downloadPdf();

  if (!fs.existsSync(PDF_PATH)) {
    console.error("PDF not found. Cannot proceed.");
    process.exit(1);
  }

  const pages = await extractPdfText();

  if (inspectOnly) {
    inspectPages(pages);
    return;
  }

  // Full parse
  inspectPages(pages);

  console.log("\n=== PARSING WORKS ===\n");

  // Map PDF pages to Riverside page numbers
  // The Riverside Chaucer typically has front matter, then numbered pages.
  // We need to detect the offset between PDF page numbers and printed page numbers.
  // This is done by looking for page numbers in headers/footers.
  const pageOffset = detectPageOffset(pages);
  console.log(`Detected page offset: PDF page - ${pageOffset} = Riverside page`);

  const works: ChaucerWork[] = [];
  let currentWork: ChaucerWork | null = null;
  let currentSection: ChaucerSection | null = null;

  for (const page of pages) {
    const riversidePage = page.pageNum - pageOffset;
    const text = page.text;

    // Check for work headings
    for (const heading of WORK_HEADINGS) {
      if (heading.pattern.test(text)) {
        console.log(`  Found "${heading.title}" on PDF page ${page.pageNum} (Riverside ~${riversidePage})`);

        // Handle Canterbury Tales structure specially
        if (heading.workId === "ct") {
          currentWork = {
            id: "ct",
            title: "The Canterbury Tales",
            abbreviation: "CT",
            sections: [],
          };
          works.push(currentWork);
        } else if (heading.workId.startsWith("ct-")) {
          // Sub-section of CT
          if (!currentWork || currentWork.id !== "ct") {
            currentWork = works.find((w) => w.id === "ct") || null;
          }
        } else {
          currentWork = {
            id: heading.workId,
            title: heading.title,
            abbreviation: heading.abbreviation,
            sections: [],
          };
          works.push(currentWork);
        }
        break;
      }
    }

    // Extract text lines and try to parse line numbers
    const textLines = text.split(/\s{2,}/).filter((l) => l.trim().length > 0);
    const lineNums = extractLineNumbers(text);

    if (currentWork && textLines.length > 0) {
      const parsedLines = interpolateLineNumbers(textLines, lineNums);
      for (const line of parsedLines) {
        line.page = riversidePage;
      }

      // Add to current section or create new one
      if (!currentSection || (currentWork.sections.length === 0)) {
        currentSection = {
          id: `${currentWork.id}-main`,
          title: currentWork.title,
          startPage: riversidePage,
          lines: [],
        };
        currentWork.sections.push(currentSection);
      }

      currentSection.lines.push(...parsedLines);
    }
  }

  // Post-process: split Canterbury Tales into fragments and tales
  const ctWork = works.find((w) => w.id === "ct");
  if (ctWork && ctWork.sections.length > 0) {
    const allLines = ctWork.sections.flatMap((s) => s.lines);
    ctWork.sections = buildCTSections(allLines);
  }

  // Output
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const output = JSON.stringify(works, null, 2);
  fs.writeFileSync(OUTPUT_PATH, output, "utf-8");

  const sizeMB = (Buffer.byteLength(output) / 1024 / 1024).toFixed(2);
  console.log(`\nOutput written to ${OUTPUT_PATH} (${sizeMB} MB)`);
  console.log(`Works found: ${works.length}`);
  for (const w of works) {
    const totalLines = w.sections.reduce((s, sec) => s + sec.lines.length, 0);
    console.log(`  ${w.abbreviation}: ${w.title} - ${w.sections.length} sections, ${totalLines} lines`);
  }
}

/**
 * Detect the offset between PDF page numbers and Riverside printed page numbers.
 * Looks for patterns like "23" or "xxiv" in page headers/footers.
 */
function detectPageOffset(pages: PageText[]): number {
  // Heuristic: scan pages 20-60 looking for printed page numbers
  // The General Prologue typically starts around Riverside page 23
  for (let i = 20; i < Math.min(60, pages.length); i++) {
    const text = pages[i].text;
    // Look for "GENERAL PROLOGUE" which should be on/near Riverside page 23
    if (/GENERAL\s+PROLOGUE/i.test(text)) {
      // Riverside page for GP start is typically 23
      return i + 1 - 23;
    }
  }

  // Fallback: look for any obvious page numbers in first 30 pages
  for (let i = 10; i < Math.min(30, pages.length); i++) {
    const match = pages[i].text.match(/^\s*(\d{1,3})\s/);
    if (match) {
      const printedPage = parseInt(match[1]);
      if (printedPage > 0 && printedPage < 100) {
        return (i + 1) - printedPage;
      }
    }
  }

  // Default offset (typical for academic editions)
  return 0;
}

/**
 * Build Canterbury Tales sections from all extracted lines,
 * using known fragment and tale boundaries.
 */
function buildCTSections(allLines: ChaucerLine[]): ChaucerSection[] {
  const sections: ChaucerSection[] = [];

  for (const frag of CT_FRAGMENTS) {
    const fragSection: ChaucerSection = {
      id: `ct-frag${frag.fragment.toLowerCase()}`,
      title: `Fragment ${frag.fragment}`,
      fragment: frag.fragment,
      startPage: 0,
      lines: [],
    };

    for (const tale of frag.tales) {
      // Find lines matching this tale's range
      const taleLines = allLines.filter(
        (l) => l.lineNumber >= tale.lineStart && l.lineNumber <= tale.lineEnd
      );

      if (taleLines.length > 0) {
        const taleSection: ChaucerSection = {
          id: `ct-${tale.tale.toLowerCase()}`,
          title: tale.title,
          fragment: frag.fragment,
          tale: tale.tale,
          startPage: taleLines[0].page,
          lines: taleLines,
        };
        sections.push(taleSection);

        if (fragSection.startPage === 0) {
          fragSection.startPage = taleLines[0].page;
        }
        fragSection.lines.push(...taleLines);
      }
    }

    if (fragSection.lines.length > 0) {
      sections.push(fragSection);
    }
  }

  return sections;
}

// ── CLI Entry Point ─────────────────────────────────────────────────

const args = process.argv.slice(2);
const inspectOnly = args.includes("--inspect");

if (args.includes("--help")) {
  console.log(`
Usage: npx tsx scripts/parse-chaucer.ts [options]

Options:
  --inspect   Only inspect the first 20 pages (don't parse fully)
  --help      Show this help message

The script expects the PDF at: ${PDF_PATH}
If not present, it will attempt to download from Dropbox.
You can also manually download and place the PDF there.

Output: ${OUTPUT_PATH}
`);
  process.exit(0);
}

parsePdf(inspectOnly).catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
