import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { parseReference } from "../parser/reference-parser.js";
import worksMetadata from "../../data/works-metadata.json";

interface TaleMeta {
  tale: string;
  title: string;
  lineRange: [number, number];
}

interface SectionMeta {
  id: string;
  title: string;
  fragment?: string;
  tales?: TaleMeta[];
}

interface WorkMeta {
  id: string;
  title: string;
  abbreviation: string;
  sections: SectionMeta[];
}

export function registerContextTools(server: McpServer) {
  server.tool(
    "get_context",
    "Get scholarly context for a Chaucer reference: which work, tale, fragment, and approximate narrative position.",
    {
      reference: z.string().describe("Chaucer reference (e.g. 'CT I.43', 'KnT 1500', 'Tr III.1')"),
    },
    async ({ reference }) => {
      const parsed = parseReference(reference);
      if (!parsed) {
        return {
          content: [
            {
              type: "text" as const,
              text: `Could not parse reference "${reference}".`,
            },
          ],
        };
      }

      const context: Record<string, string | undefined> = {
        work: parsed.workTitle,
        abbreviation: parsed.abbreviation,
        section: parsed.sectionTitle,
        line: String(parsed.startLine),
      };

      // For Canterbury Tales, identify the tale
      if (parsed.workId === "ct" && parsed.section) {
        const work = (worksMetadata.works as WorkMeta[]).find((w) => w.id === "ct");
        const section = work?.sections.find((s) => s.fragment === parsed.section);
        if (section?.tales) {
          const tale = section.tales.find(
            (t) => parsed.startLine >= t.lineRange[0] && parsed.startLine <= t.lineRange[1]
          );
          if (tale) {
            context.tale = tale.title;
            context.taleAbbreviation = tale.tale;
            const pos = parsed.startLine - tale.lineRange[0];
            const total = tale.lineRange[1] - tale.lineRange[0];
            const pct = Math.round((pos / total) * 100);
            context.positionInTale = `~${pct}% through (line ${parsed.startLine} of ${tale.lineRange[0]}-${tale.lineRange[1]})`;
          }
        }
      }

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(context, null, 2),
          },
        ],
      };
    }
  );
}
