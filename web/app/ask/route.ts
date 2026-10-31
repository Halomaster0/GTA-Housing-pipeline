// /ask — Phase 4 NL query endpoint (stub, wired to OpenRouter)
// Route: POST /ask  Body: { question: string }
// Guards: date_issued_sk IS NOT NULL only; refusal for uncomputable; cap at 1000/day
// Router: OpenRouter (free/cheap/super-cheap, cap 1000/day, $10 ceiling)
// Status: STUB — endpoint exists; full graph integration needs retrieval + cache (Phase 4 remainder)

import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  // 1. Rate / cap guard (1000/day — enforce in middleware or DB; stub notes it)
  // Read OPENROUTER_API_KEY / API_BASE_URL from env at deploy
  // 2. Call planner (Python graph / FastAPI) or direct SQL via local warehouse read
  // 3. Return: { sql, answer, citations: [{source, snippet}], refusal?, is_refusal }

  try {
    const body = await req.json();
    const question = String(body?.question || '');

    if (!question.trim()) {
      return NextResponse.json({ error: 'question required' }, { status: 400 });
    }

    // Placeholder: planner/graph call not yet wired (Phase 4 remainder)
    // Once wired, planner uses date_issued_sk IS NOT NULL (not dim_status.status_code='ISSUED')
    // and refuses per-capita / uncomputable queries.
    return NextResponse.json({
      question,
      status: 'STUB — Phase 4 retry / Phase 5 deploy',
      sql: null,
      answer: 'Endpoint live. Integration with planner/executor graph (src/ai/planner.py + executor.py) and OpenRouter endpoint is the Phase 4 remainder — not yet fully wired. Data authority: data/warehouse.duckdb (Oct 2026, 833,848 permits, 652,715 issued). Toronto 100k-unit exception EXCLUDED per audit decision.',
      citations: [{ source: 'docs/data-vintage-decision-2026-10-31.md', snippet: 'Oct warehouse default; Sept held; Toronto 100k excluded' }],
      is_refusal: false,
      refusal_reason: null,
      router: 'openrouter',
      cap_remaining: 'see middleware (1000/day)',
    });
  } catch (e: any) {
    return NextResponse.json({ error: 'internal', detail: String(e) }, { status: 500 });
  }
}
