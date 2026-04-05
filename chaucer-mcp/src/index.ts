import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerWorksTools } from "./tools/works.js";
import { registerSearchTools } from "./tools/search.js";
import { registerPassageTools } from "./tools/passage.js";
import { registerContextTools } from "./tools/context.js";

type Env = {
  CHAUCER_MCP: DurableObjectNamespace;
};

export class ChaucerMCP extends McpAgent {
  server = new McpServer({
    name: "Chaucer",
    version: "1.0.0",
  });

  async init() {
    registerWorksTools(this.server);
    registerSearchTools(this.server);
    registerPassageTools(this.server);
    registerContextTools(this.server);
  }
}

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);

    if (url.pathname === "/sse" || url.pathname === "/sse/message") {
      return (ChaucerMCP as any).serveSSE("/sse").fetch(request, env, ctx);
    }

    if (url.pathname === "/mcp") {
      return (ChaucerMCP as any).serveSSE("/mcp").fetch(request, env, ctx);
    }

    // Landing page
    return new Response(
      `<!DOCTYPE html>
<html>
<head><title>Chaucer MCP Server</title></head>
<body>
  <h1>Chaucer MCP Server</h1>
  <p>An MCP server serving the complete works of Geoffrey Chaucer from the Riverside Chaucer.</p>
  <h2>Available Tools</h2>
  <ul>
    <li><strong>list_works</strong> - List all available works with sections and line ranges</li>
    <li><strong>search_chaucer</strong> - Full-text search across all works</li>
    <li><strong>get_passage</strong> - Retrieve a passage by canonical reference</li>
    <li><strong>get_work</strong> - Retrieve an entire work or tale</li>
    <li><strong>get_context</strong> - Get scholarly context for a reference</li>
  </ul>
  <h2>Connect</h2>
  <p>MCP endpoint: <code>/sse</code></p>
</body>
</html>`,
      {
        status: 200,
        headers: { "Content-Type": "text/html" },
      }
    );
  },
};
