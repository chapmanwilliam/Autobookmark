/**
 * Parse flexible Chaucer reference strings into canonical form.
 *
 * Supported formats:
 *   "CT I.1-42", "Fragment I, lines 1-42"
 *   "KnT 1234-1300"
 *   "Tr II.456-500", "Troilus Book 2 lines 456-500"
 *   "BD 1-50"
 *   "GP 1-100"
 */

import worksMetadata from "../../data/works-metadata.json";

const ROMAN: Record<string, number> = {
  I: 1, II: 2, III: 3, IV: 4, V: 5,
  VI: 6, VII: 7, VIII: 8, IX: 9, X: 10,
};

const ROMAN_FROM_NUM: Record<number, string> = Object.fromEntries(
  Object.entries(ROMAN).map(([k, v]) => [v, k])
);

export interface ParsedReference {
  workId: string;
  workTitle: string;
  abbreviation: string;
  section?: string;       // fragment or book roman numeral
  sectionTitle?: string;
  tale?: string;          // tale abbreviation if applicable
  startLine: number;
  endLine?: number;
}

const taleAbbrevs = worksMetadata.taleAbbreviations as Record<string, { title: string; fragment: string; lineRange: [number, number] }>;

export function parseReference(input: string): ParsedReference | null {
  const s = input.trim();

  // Try tale abbreviation first: "KnT 859-2482" or "GP 1-100"
  const taleMatch = s.match(/^([A-Z][a-z]*T?|GP|Ret|Thop|Mel)\s+(\d+)(?:\s*[-–]\s*(\d+))?$/);
  if (taleMatch) {
    const abbrev = taleMatch[1];
    const tale = taleAbbrevs[abbrev];
    if (tale) {
      return {
        workId: "ct",
        workTitle: "The Canterbury Tales",
        abbreviation: "CT",
        section: tale.fragment,
        sectionTitle: `Fragment ${tale.fragment}`,
        tale: abbrev,
        startLine: parseInt(taleMatch[2]),
        endLine: taleMatch[3] ? parseInt(taleMatch[3]) : undefined,
      };
    }
  }

  // CT Fragment reference: "CT I.1-42" or "CT I 1-42"
  const ctMatch = s.match(/^CT\s+(I{1,3}V?|VI{0,3}|IX|X)\s*[.\s]\s*(\d+)(?:\s*[-–]\s*(\d+))?$/i);
  if (ctMatch) {
    const frag = ctMatch[1].toUpperCase();
    return {
      workId: "ct",
      workTitle: "The Canterbury Tales",
      abbreviation: "CT",
      section: frag,
      sectionTitle: `Fragment ${frag}`,
      startLine: parseInt(ctMatch[2]),
      endLine: ctMatch[3] ? parseInt(ctMatch[3]) : undefined,
    };
  }

  // "Fragment I, lines 1-42" or "Fragment I lines 1-42"
  const fragMatch = s.match(/^Fragment\s+(I{1,3}V?|VI{0,3}|IX|X),?\s*(?:lines?\s+)?(\d+)(?:\s*[-–]\s*(\d+))?$/i);
  if (fragMatch) {
    const frag = fragMatch[1].toUpperCase();
    return {
      workId: "ct",
      workTitle: "The Canterbury Tales",
      abbreviation: "CT",
      section: frag,
      sectionTitle: `Fragment ${frag}`,
      startLine: parseInt(fragMatch[2]),
      endLine: fragMatch[3] ? parseInt(fragMatch[3]) : undefined,
    };
  }

  // Troilus: "Tr II.456-500" or "Troilus Book 2 lines 456-500"
  const trMatch = s.match(/^(?:Tr|Troilus(?:\s+and\s+Criseyde)?)\s+(?:Book\s+)?(\d|I{1,3}V?|V)\s*[.\s,]\s*(?:lines?\s+)?(\d+)(?:\s*[-–]\s*(\d+))?$/i);
  if (trMatch) {
    let book = trMatch[1];
    if (/^\d+$/.test(book)) {
      book = ROMAN_FROM_NUM[parseInt(book)] || book;
    }
    return {
      workId: "troilus",
      workTitle: "Troilus and Criseyde",
      abbreviation: "Tr",
      section: book.toUpperCase(),
      sectionTitle: `Book ${book.toUpperCase()}`,
      startLine: parseInt(trMatch[2]),
      endLine: trMatch[3] ? parseInt(trMatch[3]) : undefined,
    };
  }

  // Simple work references: "BD 1-50", "HF 100-200", "PF 1-50", "LGW 1-100"
  const workAbbrevs: Record<string, { id: string; title: string }> = {
    BD: { id: "bd", title: "The Book of the Duchess" },
    HF: { id: "hf", title: "The House of Fame" },
    PF: { id: "pf", title: "The Parliament of Fowls" },
    LGW: { id: "lgw", title: "The Legend of Good Women" },
    Bo: { id: "boece", title: "Boece" },
    Astr: { id: "astr", title: "A Treatise on the Astrolabe" },
  };

  const workMatch = s.match(/^(BD|HF|PF|LGW|Bo|Astr)\s+(\d+)(?:\s*[-–]\s*(\d+))?$/i);
  if (workMatch) {
    const abbr = workMatch[1].toUpperCase() === "BO" ? "Bo" : workMatch[1].toUpperCase() === "ASTR" ? "Astr" : workMatch[1].toUpperCase();
    const work = workAbbrevs[abbr];
    if (work) {
      return {
        workId: work.id,
        workTitle: work.title,
        abbreviation: abbr,
        startLine: parseInt(workMatch[2]),
        endLine: workMatch[3] ? parseInt(workMatch[3]) : undefined,
      };
    }
  }

  return null;
}

/**
 * Format a canonical reference string
 */
export function formatReference(workAbbrev: string, section: string | undefined, lineNumber: number): string {
  if (section) {
    return `${workAbbrev} ${section}.${lineNumber}`;
  }
  return `${workAbbrev} ${lineNumber}`;
}
