export interface ChaucerWork {
  id: string;
  title: string;
  abbreviation: string;
  sections: ChaucerSection[];
}

export interface ChaucerSection {
  id: string;
  title: string;
  fragment?: string;
  book?: string;
  tale?: string;
  startPage: number;
  lines: ChaucerLine[];
}

export interface ChaucerLine {
  lineNumber: number;
  text: string;
  page: number;
}

export interface SearchResult {
  reference: string;
  line: ChaucerLine;
  context: ChaucerLine[];
  work: string;
  section: string;
}

export interface WorksMetadata {
  works: WorkMeta[];
  taleAbbreviations: Record<string, TaleRef>;
}

export interface WorkMeta {
  id: string;
  title: string;
  abbreviation: string;
  sections: SectionMeta[];
}

export interface SectionMeta {
  id: string;
  title: string;
  fragment?: string;
  book?: string;
  tale?: string;
  lineRange: [number, number];
  startPage: number;
}

export interface TaleRef {
  abbreviation: string;
  title: string;
  fragment: string;
  lineRange: [number, number];
}
