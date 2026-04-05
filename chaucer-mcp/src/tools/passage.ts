import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { parseReference } from "../parser/reference-parser.js";

export function registerPassageTools(server: McpServer) {
  server.tool(
    "get_passage",
    "Retrieve a specific passage by canonical reference. Accepts flexible formats like 'CT I.1-42', 'KnT 1234-1300', 'Tr II.456-500', 'BD 1-50'.",
    {
      reference: z.string().describe("Chaucer reference (e.g. 'CT I.1-42', 'KnT 859-900', 'Tr II.456-500', 'BD 1-50')"),
    },
    async ({ reference }) => {
      const parsed = parseReference(reference);
      if (!parsed) {
        return {
          content: [
            {
              type: "text" as const,
              text: `Could not parse reference "${reference}". Try formats like: CT I.1-42, KnT 859-900, Tr II.456-500, BD 1-50, GP 1-100`,
            },
          ],
        };
      }

      // Placeholder until parsed data is available
      return {
        content: [
          {
            type: "text" as const,
            text: `Parsed reference: ${JSON.stringify(parsed, null, 2)}\n\nText data not yet loaded. Run 'npm run parse' to generate data/chaucer.json.`,
          },
        ],
      };
    }
  );
}
