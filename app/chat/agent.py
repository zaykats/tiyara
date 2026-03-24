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
- Always start a new session by briefly acknowledging the fault description and the key pattern \
you noticed in the maintenance history
- Ask at most one clarifying question at a time before proceeding
- Ask clarifying questions in this priority order: \
(1) When exactly did the fault first appear, \
(2) Any recent maintenance on this component, \
(3) Any associated fault codes on the ECAM or EICAS, \
(4) Environmental conditions (temperature, humidity, recent flight route)
- Once you have enough context (after 1–3 clarifying exchanges), produce the step-by-step \
diagnostic and repair guide
- Format step-by-step guides with this exact JSON structure so the frontend can render them as \
cards:
```json
{
  "type": "step_guide",
  "title": "Fault Isolation Procedure — [Fault Name]",
  "steps": [
    {
      "number": 1,
      "title": "Short step title",
      "instruction": "Full detailed instruction here",
      "warning": null,
      "amm_reference": null
    }
  ],
  "closing_note": "What to do after completing all steps"
}
```
- Always cite the AMM chapter your recommendation comes from
- If the maintenance history shows this fault has recurred after previous fixes, explicitly flag \
this and adjust your recommendation to address the root cause, not just the symptom
- Never recommend a procedure that is outside the scope of the technician's stated role
- End every step guide with a safety reminder
"""


def build_system_prompt(
    amm_chunks: list[dict[str, Any]],
    case_history_matches: list[dict[str, Any]],
    excel_pattern_summary: Optional[dict[str, Any]],
    session_problem_description: str,
    engine_type: str,
) -> str:
    sections: list[str] = [_BASE_SYSTEM_PROMPT]

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
        history_text = "\n\n---\n\n".join(
            f"[Case #{i + 1} | ATA {c.get('ata_chapter', 'N/A')} | "
            f"relevance {c['similarity']:.2f}]\n" + c["resolution_summary"]
            for i, c in enumerate(case_history_matches)
        )
        sections.append(f"\n## Similar Resolved Cases\n{history_text}")

    return "\n".join(sections)
