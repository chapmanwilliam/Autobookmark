import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import worksMetadata from "../../data/works-metadata.json";

interface TaleMeta {
  id: string;
  tale: string;
  title: string;
  lineRange: [number, number];
}

interface SectionMeta {
  id: string;
  title: string;
  fragment?: string;
  book?: string;
  tales?: TaleMeta[];
}

interface WorkMeta {
  id: string;
  title: string;
  abbreviation: string;
  sections: SectionMeta[];
}

export function registerWorksTools(server: McpServer) {
  server.tool(
    "list_works",
    "List all available Chaucer works with their sections, tales, fragments, and line ranges",
    {},
    async () => {
      const works = (worksMetadata.works as WorkMeta[]).map((w) => ({
        id: w.id,
        title: w.title,
        abbreviation: w.abbreviation,
        sections: w.sections.map((s) => ({
          id: s.id,
          title: s.title,
          fragment: s.fragment,
          book: s.book,
          tales: s.tales?.map((t) => ({
            abbreviation: t.tale,
            title: t.title,
            lineRange: `${t.lineRange[0]}-${t.lineRange[1]}`,
          })),
        })),
      }));

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(works, null, 2),
          },
        ],
      };
    }
  );

  server.tool(
    "get_work",
    "Retrieve the full text of a Chaucer work or tale by its ID or abbreviation. For long works, results are paginated.",
    {
      id: z.string().describe("Work or tale ID/abbreviation (e.g. 'KnT', 'Troilus', 'BD', 'GP')"),
      page: z.number().optional().describe("Page number for paginated results (default 1, 100 lines per page)"),
    },
    async ({ id, page }) => {
      // This will be implemented once parsed data is available
      return {
        content: [
          {
            type: "text" as const,
            text: `Text data not yet loaded. Work "${id}" recognized but parsed text is required. Run 'npm run parse' to generate data/chaucer.json.`,
          },
        ],
      };
    }
  );
}
