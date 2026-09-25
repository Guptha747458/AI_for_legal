import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Info } from 'lucide-react';
import { apiService } from '../services/api';
import { useApp } from '../hooks/AppContext';
import {
  CLAUSE_CATEGORIES,
  DISCLAIMER_TEXT,
  type Classification,
  type Clause,
} from '../types';

interface DocumentViewerProps {
  documentId: string;
  onBack: () => void;
}

type ViewMode = 'original' | 'simplified' | 'side-by-side';

export function DocumentViewer({ documentId, onBack }: DocumentViewerProps) {
  const { state } = useApp();
  const stored = state.documents.find((d) => d.document_id === documentId);
  const [clauses, setClauses] = useState<Clause[]>(
    (stored?.clauses ?? []) as Clause[],
  );
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<ViewMode>('side-by-side');
  const [simplified, setSimplified] = useState<Record<string, { text: string; terms: string[] }>>({});
  const [classifications, setClassifications] = useState<Record<string, Classification>>({});
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const [termDef, setTermDef] = useState<{ term: string; definition: string } | null>(null);

  useEffect(() => {
    if (clauses.length > 0) return;
    setLoadingDoc(true);
    apiService
      .getDocument(documentId)
      .then((doc) => setClauses((doc.clauses ?? []) as Clause[]))
      .catch(() => setError('Could not reload document text. Re-upload it (sessions are in-memory).'))
      .finally(() => setLoadingDoc(false));
  }, [documentId, clauses.length]);

  const selected = useMemo(
    () => clauses.find((c) => c.clause_id === selectedId) ?? null,
    [clauses, selectedId],
  );

  const setClauseBusy = (id: string, v: boolean) =>
    setBusy((b) => ({ ...b, [id]: v }));

  const simplify = useCallback(
    async (clause: Clause) => {
      setError(null);
      setClauseBusy(clause.clause_id, true);
      try {
        const res = await apiService.simplifySection(clause.clause_id, documentId, 'contract');
        setSimplified((s) => ({
          ...s,
          [clause.clause_id]: { text: res.simplified_text, terms: res.key_terms ?? [] },
        }));
        setSelectedId(clause.clause_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Simplification failed');
      } finally {
        setClauseBusy(clause.clause_id, false);
      }
    },
    [documentId],
  );

  const classify = useCallback(
    async (clause: Clause) => {
      setError(null);
      setClauseBusy(clause.clause_id, true);
      try {
        const res = await apiService.classifyClause(clause.clause_id, documentId, 'contract', 'not specified');
        setClassifications((c) => ({ ...c, [clause.clause_id]: res }));
        setSelectedId(clause.clause_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Classification failed');
      } finally {
        setClauseBusy(clause.clause_id, false);
      }
    },
    [documentId],
  );

  const lookupTerm = async (term: string) => {
    try {
      const res = await apiService.explainTerm(term, selected?.text ?? '');
      setTermDef({ term: res.term, definition: res.definition });
    } catch {
      setTermDef({ term, definition: 'Lookup failed. Try again.' });
    }
  };

  const visible = clauses.filter(
    (c) =>
      !filter ||
      c.text.toLowerCase().includes(filter.toLowerCase()) ||
      (classifications[c.clause_id]?.category ?? '').includes(filter.toLowerCase()),
  );

  const categoryColor = (cat?: string) =>
    CLAUSE_CATEGORIES.find((c) => c.value === cat)?.color ?? 'bg-slate-100 text-slate-700';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <button onClick={onBack} className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </button>
          <h1 className="text-xl font-bold text-slate-900 truncate max-w-[60vw]">
            {stored?.filename ?? 'Document'}
          </h1>
          <p className="text-xs text-slate-500">
            {clauses.length} clauses
            {stored?.mode === 'demo' ? ' · demo analysis (no API key)' : ''}
          </p>
        </div>
        <div className="flex gap-1 bg-white border rounded-lg p-1">
          {(['original', 'simplified', 'side-by-side'] as ViewMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 text-sm rounded-md ${mode === m ? 'bg-blue-50 text-blue-700' : 'text-slate-500 hover:bg-slate-100'}`}
            >
              {m === 'side-by-side' ? 'Side-by-side' : m[0].toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <input
        className="input max-w-md"
        placeholder="Filter clauses or categories…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}
      {loadingDoc && <p className="text-sm text-slate-500">Loading document…</p>}

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <div className="space-y-3 max-h-[65vh] overflow-y-auto scrollbar-thin pr-1">
          {visible.map((clause) => {
            const cls = classifications[clause.clause_id];
            const simp = simplified[clause.clause_id];
            const isSel = selectedId === clause.clause_id;
            return (
              <div
                key={clause.clause_id}
                onClick={() => setSelectedId(clause.clause_id)}
                className={`card cursor-pointer transition-shadow hover:shadow-md ${isSel ? 'ring-2 ring-blue-500' : ''} ${
                  cls?.attention_level === 'high'
                    ? 'border-l-4 border-l-red-400'
                    : cls?.attention_level === 'medium'
                      ? 'border-l-4 border-l-amber-400'
                      : ''
                }`}
              >
                <div className="card-body space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium text-slate-500">§{clause.clause_index + 1} · p.{clause.page_number}</span>
                    {cls && <span className={`badge ${categoryColor(cls.category)}`}>{cls.category.replace(/_/g, ' ')}</span>}
                    {cls && (
                      <span className={`badge ${cls.attention_level === 'high' ? 'badge-high' : cls.attention_level === 'medium' ? 'badge-medium' : 'badge-low'}`}>
                        {cls.attention_level} attention
                      </span>
                    )}
                  </div>
                  {(mode === 'original' || mode === 'side-by-side') && (
                    <p className="text-sm text-slate-800 leading-relaxed">{clause.text}</p>
                  )}
                  {(mode === 'simplified' || mode === 'side-by-side') && (
                    <div className="rounded-lg bg-blue-50/60 p-3">
                      <p className="text-xs font-medium text-blue-800 mb-1">PLAIN LANGUAGE</p>
                      {simp ? (
                        <>
                          <p className="text-sm text-slate-700">{simp.text}</p>
                          {simp.terms.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {simp.terms.map((t) => (
                                <button
                                  key={t}
                                  className="badge bg-white border border-blue-200 text-blue-700 hover:bg-blue-100"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    lookupTerm(t);
                                  }}
                                >
                                  {t} <Info className="ml-1 inline h-3.5 w-3.5" aria-hidden="true" />
                                </button>
                              ))}
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-slate-500">Not simplified yet — use the panel on the right.</p>
                      )}
                    </div>
                  )}
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <button className="btn-outline text-xs" disabled={!!busy[clause.clause_id]} onClick={() => simplify(clause)}>
                      {busy[clause.clause_id] ? '…' : simp ? 'Re-simplify' : 'Simplify'}
                    </button>
                    <button className="btn-outline text-xs" disabled={!!busy[clause.clause_id]} onClick={() => classify(clause)}>
                      {busy[clause.clause_id] ? '…' : cls ? 'Re-analyze risk' : 'Analyze risk'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
          {visible.length === 0 && !loadingDoc && (
            <p className="text-sm text-slate-500">No clauses match this filter.</p>
          )}
        </div>

        <div className="space-y-3">
          <div className="card lg:sticky lg:top-4">
            <div className="card-header font-medium text-sm">Clause detail</div>
            <div className="card-body text-sm space-y-2 max-h-[50vh] overflow-y-auto scrollbar-thin">
              {!selected ? (
                <p className="text-slate-500">Select a clause to inspect its simplification and risk analysis.</p>
              ) : (
                <>
                  <p className="text-slate-800">{selected.text}</p>
                  {simplified[selected.clause_id] && (
                    <div className="rounded bg-blue-50 p-2 text-slate-700">
                      {simplified[selected.clause_id].text}
                    </div>
                  )}
                  {classifications[selected.clause_id] ? (
                    <>
                      <p><strong>Why it matters:</strong> {classifications[selected.clause_id].rationale}</p>
                      <p>{classifications[selected.clause_id].plain_explanation}</p>
                    </>
                  ) : (
                    <button className="btn-outline text-xs" onClick={() => classify(selected)}>
                      Analyze this clause
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
          {termDef && (
            <div className="card">
              <div className="card-header text-sm font-medium">Glossary — {termDef.term}</div>
              <div className="card-body text-sm text-slate-700">{termDef.definition}</div>
            </div>
          )}
          <p className="text-xs text-slate-500">{DISCLAIMER_TEXT}</p>
        </div>
      </div>
    </div>
  );
}
