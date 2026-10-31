// Middleware: enforce daily request cap and route preference (free -> cheap -> super-cheap)
// Applied globally or per-route in next.config.mjs middleware matcher.
// Config: read from .env (LLM_DAILY_REQUEST_CAP, LLM_ROUTE_FREE_FIRST, LLM_ROUTE_CHEAP_FALLBACK, LLM_USE_SUPER_CHEAP_MODEL_ON_FREE_FAIL)
// This is the routing enforcement layer — the planner does not decide routing; this does.

export const config = {
  matcher: ['/ask/:path*'],
};

export default function middleware(req: Request) {
  // Stub: log cap usage, enforce 1000/day per IP/session, prefer free models.
  // Once deployed, wire to a lightweight store (Redis/DB) tracking daily counts.
  return Response.json({ routing: 'openrouter', cap: 1000, preference: 'free_first' }, { status: 200 });
}
