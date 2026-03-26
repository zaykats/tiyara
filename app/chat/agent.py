"""Build the Tiyara AI system prompt with injected RAG context."""

from typing import Any, Optional


_BASE_SYSTEM_PROMPT = """\
You are Tiyara AI, an expert aircraft maintenance assistant with deep knowledge of aviation \
engineering, ATA chapters, and MRO best practices. You assist certified aircraft technicians \
in diagnosing faults and applying correct maintenance procedures.

Your personality: precise, calm, and methodical. You communicate like a senior licensed \
aircraft engineer — authoritative but collaborative. You never guess. If you are not certain, \
you say so and ask a clarifying question.

Your behavior rules:
- Be concise and direct. No greetings, no filler, no repetition.
- Use this exact markdown structure for every diagnostic response:

## Diagnosis
2–3 sentences max. State the most likely root cause with inline source: [AMM XX-XX-XX] or [Case #N] or [History].

## Risk Level
One line: 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low — and why in one sentence.

## History Patterns
2–4 bullet points only. Flag recurrences. Be specific (e.g. "EGT loss recurred 8× — root cause never resolved").

## Procedure
Numbered steps. Each step: **bold title**, one short paragraph of instruction, AMM ref in brackets. \
Max 6 steps. If more are needed, group them.

## Parts & Tooling
Two short bullet lists: Parts (with P/N if known) and Tooling. Max 5 items each.

## Follow-up
3–5 bullet points max.

## Sources
Markdown table: Reference | Page | Notes. One row per source.

- Cite sources inline as [AMM XX-XX-XX, p.Y], [Case #N], or [History].
- If no AMM was ingested for this engine, add one line under Sources: \
  "⚠️ No AMM ingested for [ATA chapters] — steps based on general MRO practice."
- If the fault has recurred after previous fixes, flag it prominently under History Patterns.
- Ask at most one clarifying question, only if a critical detail is truly missing. \
Do NOT put clarifying questions in the Follow-up section — Follow-up is for required actions only.
- The ⚠️ "No AMM ingested" warning must appear ONLY in the first response of a session. \
Never repeat it in follow-up replies.
- At the very end of every response, after all sections, output exactly this line — \
no markdown formatting, no label before it, nothing after it:
SUGGESTIONS: <question 1> | <question 2> | <question 3>
These must be 3 short, specific questions a technician would actually ask next. \
Base them on what was just discussed. Do not number them. This line must always be present.
"""


def build_system_prompt(
    amm_chunks: list[dict[str, Any]],
    case_history_matches: list[dict[str, Any]],
    excel_pattern_summary: Optional[dict[str, Any]],
    session_problem_description: str,
    engine_type: str,
    is_first_message: bool = True,
) -> str:
    sections: list[str] = [_BASE_SYSTEM_PROMPT]
    if not is_first_message:
        sections.append("\n[This is a follow-up message — do NOT repeat the ⚠️ AMM warning.]")

    # ── Engine / fault context ────────────────────────────────────────────────
    sections.append(
        f"\n## Session Context\n"
        f"Engine type: {engine_type}\n"
        f"Reported fault: {session_problem_description}\n"
    )

    # ── Excel pattern summary ─────────────────────────────────────────────────
    if excel_pattern_summary:
        import json

        sections.append(
            "\n## Maintenance History Pattern Analysis (from uploaded Excel log)\n"
            + json.dumps(excel_pattern_summary, indent=2)
        )

    # ── AMM chunks ────────────────────────────────────────────────────────────
    if amm_chunks:
        chunk_text = "\n\n---\n\n".join(
            f"[AMM {c.get('ata_chapter', 'N/A')} | {c.get('source_filename', '')} "
            f"p.{c.get('page_number', '?')} | relevance {c['similarity']:.2f}]\n"
            + c["chunk_text"]
            for c in amm_chunks
        )
        sections.append(f"\n## Relevant AMM Sections\n{chunk_text}")

    # ── Case history ──────────────────────────────────────────────────────────
    if case_history_matches:
        import json as _json
        history_parts = []
        for i, c in enumerate(case_history_matches):
            try:
                s = _json.loads(c["resolution_summary"])
                part = (
                    f"### Resolved Case #{i + 1} — ATA {c.get('ata_chapter', 'N/A')} "
                    f"(similarity {c['similarity']:.2f})\n"
                    f"**Fault:** {s.get('fault_description', 'N/A')}\n"
                    f"**Root Cause:** {s.get('root_cause', 'N/A')}\n"
                    f"**Steps Applied:** {', '.join(s.get('steps_applied', [])) or 'N/A'}\n"
                    f"**Outcome:** {s.get('outcome', 'N/A')}"
                )
            except Exception:
                part = (
                    f"### Resolved Case #{i + 1} — ATA {c.get('ata_chapter', 'N/A')}\n"
                    + c["resolution_summary"]
                )
            history_parts.append(part)
        sections.append("\n## Similar Resolved Cases\n" + "\n\n---\n\n".join(history_parts))

    return "\n".join(sections)
