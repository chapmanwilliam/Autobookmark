import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

export function registerSearchTools(server: McpServer) {
  server.tool(
    "search_chaucer",
    "Full-text search across all of Chaucer's works. Returns matching lines with context and canonical references.",
    {
      query: z.string().describe("Search query (case-insensitive)"),
      work: z.string().optional().describe("Filter to a specific work by ID or abbreviation (e.g. 'ct', 'troilus', 'BD')"),
    },
    async ({ query, work }) => {
      // Placeholder until parsed data is available
      return {
        content: [
          {
            type: "text" as const,
            text: `Search for "${query}"${work ? ` in ${work}` : ""}: Text data not yet loaded. Run 'npm run parse' to generate data/chaucer.json.`,
          },
        ],
      };
    }
  );
}
