// /ask — Phase 4 NL query endpoint (wired to OpenRouter + planner/executor graph)
// Route: POST /ask  Body: { question: string }
// Guards: date_issued_sk IS NOT NULL only; refusal for uncomputable; cap at 1000/day
// Router: OpenRouter (free/cheap/super-cheap, cap 1000/day, $10 ceiling)
// Status: Wired — calls FastAPI backend (src/ai.api) for planner→executor→critic

import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  // 1. Rate / cap guard (1000/day — enforce in middleware or DB; notes in middleware.ts)
  // 2. Call planner/executor/critic via FastAPI backend
  // 3. Return: { sql, answer, citations: [{source, snippet}], refusal?, is_refusal }

  try {
    const body = await req.json();
    const question = String(body?.question || '');

    if (!question.trim()) {
      return NextResponse.json({ error: 'question required' }, { status: 400 });
    }

    // 2. Call the FastAPI backend (runs planner → executor → critic pipeline)
    // Backend: src/ai/api.py — exposes POST /ask at API_BASE_URL (configured in .env)
    const backendUrl = process.env.API_BASE_URL || 'http://localhost:8000';
    const apiResp = await fetch(`${backendUrl}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!apiResp.ok) {
      const err = await apiResp.text();
      return NextResponse.json({ error: 'backend failed', detail: err }, { status: 502 });
    }

    const data = await apiResp.json();

    // 3. Return the full pipeline response
    return NextResponse.json({
      question,
      status: 'Wired — Phase 4 / Phase 5 deploy',
      sql: data.sql,
      answer: data.answer,
      citations: data.citations,
      is_refusal: data.is_refusal,
      refusal_reason: data.refusal_reason,
      router: 'openrouter',
      cap_remaining: 'see middleware (1000/day)',
      trace_id: data.trace_id,
      latency_ms: data.latency_ms,
    });
  } catch (e: any) {
    return NextResponse.json({ error: 'internal', detail: String(e) }, { status: 500 });
  }
}