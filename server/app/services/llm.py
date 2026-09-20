"""LLM service using Groq's OpenAI-compatible chat completions API."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from app.core.settings import settings


class LLMService:
    """
    Service for interacting with Groq chat completions.
    Uses tool calling to force structured JSON outputs.
    """

    def __init__(self) -> None:
        self.api_key = settings.api_key
        self.model = settings.model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self._client = None

    def _get_client(self):  # type: ignore[no-untyped-def]
        if self._client is None and settings.is_available():
            from groq import Groq

            self._client = Groq(api_key=settings.api_key)
        return self._client

    def is_available(self) -> bool:
        return settings.is_available()

    @property
    def use_demo(self) -> bool:
        return not settings.is_available()

    @staticmethod
    def _to_groq_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]

    def _call_groq_sync(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        tool_name: str,
    ) -> dict[str, Any]:
        """Blocking Groq tool-calling request (runs in a worker thread)."""
        from groq import APIError, Groq

        client = self._get_client()
        if client is None:
            raise RuntimeError("Groq API key is not configured")
        assert isinstance(client, Groq)

        try:
            response = client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                tools=self._to_groq_tools(tools),
                tool_choice={"type": "function", "function": {"name": tool_name}},
            )
        except APIError as exc:
            raise RuntimeError(f"Groq request failed for model '{self.model}': {exc}") from exc
        message = response.choices[0].message

        for tool_call in message.tool_calls or []:
            function = tool_call.function
            if function.name == tool_name:
                try:
                    data = json.loads(function.arguments)
                except json.JSONDecodeError:
                    data = None
                if isinstance(data, dict):
                    return data

        text = message.content or ""
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"raw_text": text}
        except json.JSONDecodeError:
            return {"raw_text": text}

    async def _call_groq(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        tool_name: str,
    ) -> dict[str, Any]:
        """Call Groq in a worker thread to avoid blocking the event loop."""
        return await asyncio.to_thread(self._call_groq_sync, system, user, tools, tool_name)

    async def generate_simplification(
        self,
        document_type: str,
        section_id: str,
        original_text: str,
    ) -> dict[str, Any]:
        """Generate a plain-language summary of a section."""
        if self.use_demo:
            return self._demo_simplify(section_id, original_text)
        tool = {
            "name": "simplify_section",
            "description": "Simplify a legal clause into plain language while preserving the section ID",
            "input_schema": {
                "type": "object",
                "properties": {
                    "section_id": {"type": "string", "description": "The original section ID"},
                    "simplified_text": {
                        "type": "string",
                        "description": "Plain-language summary of the clause",
                    },
                    "key_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Legal terms that need definition",
                    },
                },
                "required": ["section_id", "simplified_text", "key_terms"],
            },
        }

        system = (
            "You are LegalLens, a document simplification assistant.\n"
            "Your task is to produce a plain-language summary of legal text, section by section.\n"
            "Rules:\n"
            "- Keep the original section/clause IDs so the UI can link back.\n"
            "- Use simple, clear language (target 8th-grade reading level).\n"
            "- Do NOT add legal advice or recommendations.\n"
            "- Preserve the meaning accurately; do not soften or exaggerate.\n"
            "- Output only the simplified text and mapping IDs."
        )

        user = (
            f"Document type: {document_type}\n"
            f"Section ID: {section_id}\n"
            f"Original text:\n{original_text}\n\n"
            "Return JSON with keys: section_id, simplified_text, key_terms (list of terms that need definition)."
        )

        return await self._call_groq(system, user, [tool], "simplify_section")

    async def generate_classification(
        self,
        document_type: str,
        jurisdiction: str,
        clause_id: str,
        clause_text: str,
    ) -> dict[str, Any]:
        """Classify a clause and flag risk factors."""
        if self.use_demo:
            return self._demo_classify(clause_id, clause_text)
        tool = {
            "name": "classify_clause",
            "description": "Classify a legal clause and flag its risk level",
            "input_schema": {
                "type": "object",
                "properties": {
                    "clause_id": {"type": "string", "description": "The clause ID"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "obligations",
                            "rights",
                            "deadlines",
                            "penalties_fees",
                            "termination",
                            "auto_renewal",
                            "liability_indemnification",
                            "dispute_resolution",
                            "data_privacy",
                            "unusual_nonstandard",
                        ],
                    },
                    "attention_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "How much attention this clause warrants",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Why this clause needs attention in plain language",
                    },
                    "plain_explanation": {
                        "type": "string",
                        "description": "Plain-language explanation of the clause",
                    },
                },
                "required": [
                    "clause_id",
                    "category",
                    "attention_level",
                    "rationale",
                    "plain_explanation",
                ],
            },
        }

        system = (
            "You are LegalLens, a clause classification and risk analysis assistant.\n"
            "Classify the given clause into ONE primary category and flag any risk factors.\n"
            "Categories: obligations, rights, deadlines, penalties_fees, termination, "
            "auto_renewal, liability_indemnification, dispute_resolution, data_privacy, "
            "unusual_nonstandard.\n"
            "Rules:\n"
            "- Output valid JSON matching the schema exactly.\n"
            "- attention_level: 'low', 'medium', or 'high' based on how much attention the clause warrants.\n"
            "- rationale: Explain WHY this clause needs attention in plain language.\n"
            "- Do NOT give legal advice or tell the user what to do.\n"
            "- Use jurisdiction context if provided; otherwise note interpretation may vary."
        )

        user = (
            f"Document type: {document_type}\n"
            f"Jurisdiction: {jurisdiction or 'not specified (interpretation may vary by jurisdiction)'}\n"
            f"Clause ID: {clause_id}\n"
            f"Clause text:\n{clause_text}\n\n"
            "Return JSON with keys: clause_id, category, attention_level, rationale, plain_explanation."
        )

        return await self._call_groq(system, user, [tool], "classify_clause")

    async def generate_comparison(
        self,
        document_type: str,
        jurisdiction: str,
        original_text: str,
        revised_text: str,
    ) -> dict[str, Any]:
        """Compare two document versions and produce a structured diff."""
        if self.use_demo:
            return self._demo_compare(original_text, revised_text)
        tool = {
            "name": "compare_documents",
            "description": "Compare two document versions and produce a structured diff",
            "input_schema": {
                "type": "object",
                "properties": {
                    "changes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["added", "removed", "modified"],
                                },
                                "clause_id_old": {"type": "string"},
                                "clause_id_new": {"type": "string"},
                                "explanation": {
                                    "type": "string",
                                    "description": "Plain-language explanation of the change",
                                },
                                "impact": {
                                    "type": "string",
                                    "description": "Practical impact of the change",
                                },
                            },
                            "required": ["type", "explanation", "impact"],
                        },
                    }
                },
                "required": ["changes"],
            },
        }

        system = (
            "You are LegalLens, a document comparison assistant.\n"
            "Compare two versions of a document and produce a structured diff.\n"
            "Rules:\n"
            "- Identify ADDED, REMOVED, and MODIFIED clauses.\n"
            "- For each change, explain the PRACTICAL IMPACT in plain language.\n"
            "- Reference clause IDs from both versions.\n"
            "- Do NOT give legal advice or recommend which version to choose.\n"
            "- Output only the structured diff with plain-language explanations."
        )

        user = (
            f"Document type: {document_type}\n"
            f"Jurisdiction: {jurisdiction or 'not specified (interpretation may vary by jurisdiction)'}\n\n"
            f"Original document:\n{original_text}\n\n"
            f"Revised document:\n{revised_text}\n\n"
            "Return JSON with keys: changes (list of {type, clause_id_old, clause_id_new, explanation, impact})."
        )

        return await self._call_groq(system, user, [tool], "compare_documents")

    async def generate_qa(
        self,
        document_type: str,
        jurisdiction: str,
        context: str,
        question: str,
    ) -> dict[str, Any]:
        """Generate a grounded answer to a document question."""
        if self.use_demo:
            return self._demo_qa(context, question)
        tool = {
            "name": "answer_question",
            "description": "Answer a question about the document using only the provided excerpts",
            "input_schema": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The grounded answer to the question",
                    },
                    "citations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of clause IDs cited in the answer",
                    },
                    "disclaimer_needed": {
                        "type": "boolean",
                        "description": "Whether the answer requires a legal disclaimer",
                    },
                },
                "required": ["answer", "citations", "disclaimer_needed"],
            },
        }

        system = (
            "You are LegalLens, a document-grounded Q&A assistant.\n"
            "Answer questions about the provided document ONLY.\n"
            "Rules:\n"
            "- Every answer MUST cite the specific clause ID and section it comes from.\n"
            "- If the answer is not in the document, say so explicitly.\n"
            "- NEVER fabricate clauses, citations, or legal conclusions.\n"
            "- Do NOT give legal advice (e.g., 'you should sign' or 'this is illegal').\n"
            "- If the question requires legal judgment, explain considerations neutrally and recommend a lawyer.\n"
            "- Include jurisdiction caveat if relevant.\n"
            "- Use plain language; define legal terms inline when needed."
        )

        user = (
            f"Document type: {document_type}\n"
            f"Jurisdiction: {jurisdiction or 'not specified (interpretation may vary by jurisdiction)'}\n\n"
            f"Relevant document excerpts:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Return JSON with keys: answer, citations (list of clause_ids), disclaimer_needed (bool)."
        )

        return await self._call_groq(system, user, [tool], "answer_question")

    async def generate_checklist(
        self,
        document_type: str,
        jurisdiction: str,
        analysis_summary: str,
    ) -> dict[str, Any]:
        """Generate an action checklist and questions for a lawyer."""
        if self.use_demo:
            return self._demo_checklist(analysis_summary)
        tool = {
            "name": "generate_checklist",
            "description": "Generate an action checklist and questions for a lawyer",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "clause_id": {"type": "string"},
                                "urgency": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high"],
                                },
                            },
                            "required": ["text", "clause_id", "urgency"],
                        },
                    },
                    "questions_for_lawyer": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "related_clause_id": {"type": "string"},
                            },
                            "required": ["question", "related_clause_id"],
                        },
                    },
                },
                "required": ["action_items", "questions_for_lawyer"],
            },
        }

        system = (
            "You are LegalLens, a document analysis assistant.\n"
            "Based on the document, generate:\n"
            "1. An action checklist (tasks the user should consider)\n"
            "2. Questions to ask a lawyer (tailored to flagged risk areas)\n"
            "Rules:\n"
            "- Each item must reference the relevant clause ID or section.\n"
            "- Do NOT tell the user what to decide (e.g., 'sign' or 'don't sign').\n"
            "- Frame items as things to VERIFY or ASK ABOUT.\n"
            "- Include jurisdiction caveat if relevant.\n"
            "- Output only the structured checklist and questions."
        )

        user = (
            f"Document type: {document_type}\n"
            f"Jurisdiction: {jurisdiction or 'not specified (interpretation may vary by jurisdiction)'}\n\n"
            f"Document summary and flagged clauses:\n{analysis_summary}\n\n"
            "Return JSON with keys: action_items (list of {text, clause_id, urgency}), "
            "questions_for_lawyer (list of {question, related_clause_id})."
        )

        return await self._call_groq(system, user, [tool], "generate_checklist")


    # ------------------------------------------------------------------
    # Demo (offline) fallbacks — deterministic, rule-based, no API key needed.
    # Clearly marked so the UI can show "demo analysis" state.
    # ------------------------------------------------------------------

    @staticmethod
    def _demo_terms(text: str) -> list[str]:
        glossary = [
            "indemnify", "liability", "arbitration", "jurisdiction",
            "termination", "renewal", "confidential", "warranty",
            "force majeure", "assignment", "severability",
        ]
        lowered = text.lower()
        return [t for t in glossary if t in lowered][:6]

    def _demo_simplify(self, section_id: str, text: str) -> dict[str, Any]:
        first = text.strip().split(".")[0].strip()
        if len(first) > 220:
            first = first[:217] + "..."
        return {
            "section_id": section_id,
            "simplified_text": (
                f"In plain language: {first}. "
                "This is a demo simplification (no API key configured) — "
                "connect a Groq key for full AI summaries."
            ),
            "key_terms": self._demo_terms(text),
            "demo": True,
        }

    def _demo_classify(self, clause_id: str, text: str) -> dict[str, Any]:
        lowered = text.lower()
        rules: list[tuple[str, str, str, str]] = [
            ("indemnif", "liability_indemnification", "high",
             "Indemnification clauses can shift significant costs onto you — worth reviewing closely."),
            ("arbitrat", "dispute_resolution", "high",
             "Arbitration clauses can waive your right to sue in court — worth reviewing closely."),
            ("terminat", "termination", "medium",
             "Termination terms control how and when either side can end the agreement."),
            ("renew", "auto_renewal", "medium",
             "Auto-renewal can lock you in unless you cancel in time."),
            ("fee|penalt|late|interest", "penalties_fees", "medium",
             "Fee and penalty terms affect what you may owe if things go wrong."),
            ("confidential|privacy|data", "data_privacy", "medium",
             "Data and privacy terms control how your information is used."),
            ("deadline|days|notice", "deadlines", "low",
             "This sets time limits you may need to act on."),
            ("shall|must|agree to|obligat", "obligations", "low",
             "This describes something a party must do."),
            ("right|entitled|may ", "rights", "low",
             "This describes something a party is allowed to do."),
        ]
        for pattern, category, level, rationale in rules:
            if re.search(pattern, lowered):
                return {
                    "clause_id": clause_id,
                    "category": category,
                    "attention_level": level,
                    "rationale": rationale,
                    "plain_explanation": (
                        f"This looks like a {category.replace('_', ' ')} clause. {rationale}"
                    ),
                    "demo": True,
                }
        return {
            "clause_id": clause_id,
            "category": "unusual_nonstandard",
            "attention_level": "low",
            "rationale": "No common risk pattern matched; still worth reading carefully.",
            "plain_explanation": "This clause doesn't match a common category in demo mode.",
            "demo": True,
        }

    def _demo_compare(self, original: str, revised: str) -> dict[str, Any]:
        o_lines = [line.strip() for line in original.splitlines() if line.strip()]
        r_lines = [line.strip() for line in revised.splitlines() if line.strip()]
        o_set, r_set = set(o_lines), set(r_lines)
        changes: list[dict[str, Any]] = []
        for line in r_lines:
            if line not in o_set:
                changes.append({
                    "type": "added",
                    "explanation": f"New text appears in the revised version: “{line[:140]}”.",
                    "impact": "Review whether the addition creates new duties, costs, or deadlines for you.",
                })
        for line in o_lines:
            if line not in r_set:
                changes.append({
                    "type": "removed",
                    "explanation": f"Text removed from the original: “{line[:140]}”.",
                    "impact": "Check whether a protection, right, or deadline you relied on was removed.",
                })
        if not changes:
            changes.append({
                "type": "modified",
                "explanation": "No line-level differences detected in demo mode.",
                "impact": "The documents look textually identical at line level; connect an API key for semantic diff.",
            })
        return {"changes": changes[:20], "demo": True}

    def _demo_qa(self, context: str, question: str) -> dict[str, Any]:
        q_words = {w.lower().strip("?,.") for w in question.split() if len(w) > 3}
        best = ""
        best_score = 0
        for para in context.split("\n\n"):
            words = set(para.lower().split())
            score = len(q_words & words)
            if score > best_score:
                best_score = score
                best = para.strip()
        if best_score == 0 or not best:
            return {
                "answer": (
                    "I couldn't find that in the uploaded document text (demo search). "
                    "Try rephrasing, or upload the section that covers it. "
                    "For decisions with real consequences, consult a licensed attorney."
                ),
                "citations": [],
                "disclaimer_needed": True,
                "demo": True,
            }
        snippet = best[:600]
        return {
            "answer": (
                f"Based on the document text: “{snippet}”. "
                "(Demo answer — connect a Groq key for full AI Q&A. "
                "This is general information, not legal advice.)"
            ),
            "citations": [],
            "disclaimer_needed": True,
            "demo": True,
        }

    def _demo_checklist(self, summary: str) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        questions: list[dict[str, Any]] = []
        lowered = summary.lower()
        if "day" in lowered or "notice" in lowered or "deadline" in lowered:
            items.append({"text": "Calendar every deadline and notice period mentioned.", "clause_id": "", "urgency": "high"})
            questions.append({"question": "What happens if I miss a notice deadline?", "related_clause_id": ""})
        if "fee" in lowered or "penalt" in lowered or "payment" in lowered:
            items.append({"text": "Verify all fees, payment dates, and late penalties.", "clause_id": "", "urgency": "medium"})
            questions.append({"question": "Are these fees negotiable or capped?", "related_clause_id": ""})
        if "terminat" in lowered or "renew" in lowered:
            items.append({"text": "Confirm how to terminate or opt out of renewal, and by when.", "clause_id": "", "urgency": "high"})
            questions.append({"question": "What is the exact renewal/termination notice process?", "related_clause_id": ""})
        if "indemnif" in lowered or "liabilit" in lowered:
            items.append({"text": "Review who bears liability and whether it is capped.", "clause_id": "", "urgency": "high"})
            questions.append({"question": "Is the indemnification mutual, and is liability limited?", "related_clause_id": ""})
        if "arbitrat" in lowered or "dispute" in lowered:
            items.append({"text": "Note where and how disputes must be resolved.", "clause_id": "", "urgency": "medium"})
            questions.append({"question": "Am I waiving court access or a jury trial here?", "related_clause_id": ""})
        if not items:
            items.append({"text": "Read the full document and note any dates, payments, and duties.", "clause_id": "", "urgency": "low"})
            questions.append({"question": "Are there any one-sided or unusual terms I should know about?", "related_clause_id": ""})
        items.append({"text": "Keep a signed copy and confirm the jurisdiction that applies.", "clause_id": "", "urgency": "low"})
        return {"action_items": items, "questions_for_lawyer": questions, "demo": True}


# Global LLM service instance
llm_service = LLMService()
