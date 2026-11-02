// Middleware: enforce daily request cap and route preference (free -> cheap -> super-cheap)
// Applied globally or per-route in next.config.mjs middleware matcher.
// Config: read from .env (LLM_DAILY_REQUEST_CAP, LLM_ROUTE_FREE_FIRST, LLM_ROUTE_CHEAP_FALLBACK, LLM_USE_SUPER_CHEAP_MODEL_ON_FREE_FAIL)
// This is the routing enforcement layer — the planner does not decide routing; this does.

import { NextResponse } from 'next/server';

export const config = {
  matcher: ['/api/ask/:path*'],
};

// NOT ENFORCED YET. This was a stub that answered every request with a JSON
// body, which short-circuited the /ask API. It now passes requests through.
// The 1000/day cap needs a store (Redis/DB) for daily counts before it is real.
export default function middleware() {
  return NextResponse.next();
}
