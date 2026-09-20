# LegalLens — AI-Powered Legal Document Assistant

Informational aid for understanding contracts, leases, policies, and notices.
**Not legal advice. Does not create an attorney-client relationship.**

## Tech stack (confirmed)

| Layer | Choice |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.11+ + FastAPI + Uvicorn |
| LLM | Anthropic Claude Messages API with tool calling (structured JSON) |
| Parsing | `python-docx`, `pdfplumber`, `PyPDF2` (PDF / DOCX / TXT) |
| Grounding | In-memory hash-embedding vector store (session-scoped, no persistence) |

No API key? The backend runs in **demo mode** with deterministic rule-based
analysis so every feature is testable offline. Set `ANTHROPIC_API_KEY` for live
Claude output.

## Folder structure (AI_for_legal is the project root)

```
AI_for_legal/
├── client/                  # React + TS + Vite + Tailwind
│   └── src/
│       ├── components/      # DisclaimerBanner, Footer, DocumentUpload
│       ├── pages/           # DocumentViewer, DocumentComparison, DocumentChat,
│       │                    #   ActionChecklist, GlossaryPage
│       ├── hooks/           # AppContext, useAppState, useInterval
│       ├── services/        # api.ts (axios client)
│       ├── types/           # shared TS types
│       └── styles/
├── server/                  # FastAPI backend
│   └── app/
│       ├── main.py          # all API routes
│       ├── core/            # settings, document processor (PDF/DOCX/TXT)
│       ├── services/        # llm, chunker, vector_store, documents, glossary
│       ├── models/          # jobs, responses
│       └── prompts/         # prompt templates per feature
├── samples/                 # sample-contract.txt + sample-contract-v2.txt
├── shared/                  # reserved for shared types
└── package.json             # root dev scripts
```

## Run

```powershell
# backend (http://localhost:8000)
cd server
copy .env.example .env   # optional; without ANTHROPIC_API_KEY you get demo mode
python -m uvicorn app.main:app --reload

# frontend (http://localhost:5173, proxies /api → :8000)
cd client
npm install
npm run dev
```

## Test (sample contract, feature by feature)

```powershell
# From the project root: runs the full backend regression suite.
npm test

cd client
npm run typecheck
npm run lint
npm run build
```

`server/tests/test_pipeline.py` exercises every core use case against
`samples/sample-contract.txt` and `samples/sample-contract-v2.txt`:
1. Simplifier, 2. Clause/risk highlighter, 3. Comparison, 4. Grounded Q&A,
5. Checklist + lawyer questions, 6. Glossary.

`server/tests/test_validation.py` covers upload signature validation, bounded
request input, and correct not-found behavior for document deletion.

## Safety

- Persistent disclaimer banner + footer + per-answer disclaimer.
- Q&A is document-grounded with citations; out-of-scope answers say so explicitly.
- No definitive legal conclusions; jurisdiction is optional and caveated.
- Session-only in-memory storage; `DELETE /api/v1/documents/{id}` wipes a document.
