import { useState, type FormEvent } from 'react';
import { ArrowLeft } from 'lucide-react';
import { apiService } from '../services/api';
import { useApp } from '../hooks/AppContext';
import { DISCLAIMER_TEXT, type ComparisonResult } from '../types';

interface DocumentComparisonProps {
  docIds: string[];
  onCompare: (ids: string[]) => void;
  onBack: () => void;
}

function errMsg(e: unknown): string {
  if (typeof e === 'object' && e !== null && 'response' in e) {
    const r = (e as { response?: { data?: { detail?: string } } }).response;
    if (r?.data?.detail) return r.data.detail;
  }
  return e instanceof Error ? e.message : 'Comparison failed';
}

export function DocumentComparison({ docIds, onCompare, onBack }: DocumentComparisonProps) {
  const { state } = useApp();
  const [document1Id, setDocument1Id] = useState(docIds[0] || state.documents[0]?.document_id || '');
  const [document2Id, setDocument2Id] = useState(docIds[1] || state.documents[1]?.document_id || '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!document1Id || !document2Id) {
      setError('Select two documents to compare.');
      return;
    }
    if (document1Id === document2Id) {
      setError('Pick two different documents (e.g. old vs. new version).');
      return;
    }
    setLoading(true);
    try {
      const res = await apiService.compareDocuments(document1Id, document2Id, 'contract', 'not specified');
      setResult(res);
      onCompare([document1Id, document2Id]);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setLoading(false);
    }
  };

  const picker = (value: string, set: (v: string) => void, label: string) => (
    <div>
      <label className="label">{label}</label>
      {state.documents.length > 0 ? (
        <select className="input" value={value} onChange={(e) => set(e.target.value)}>
          <option value="">— choose —</option>
          {state.documents.map((d) => (
            <option key={d.document_id} value={d.document_id}>
              {d.filename}
            </option>
          ))}
        </select>
      ) : (
        <input
          className="input"
          placeholder="Document ID (upload documents first)"
          value={value}
          onChange={(e) => set(e.target.value)}
        />
      )}
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 text-sm">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back
        </button>
        <h1 className="text-xl font-bold text-slate-900">Compare Documents</h1>
      </div>
      <form onSubmit={submit} className="card">
        <div className="card-body space-y-4">
          {picker(document1Id, setDocument1Id, 'Original / first document')}
          {picker(document2Id, setDocument2Id, 'Revised / second document')}
          {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}
          <button className="btn-primary w-full" disabled={loading}>
            {loading ? 'Comparing…' : 'Compare'}
          </button>
        </div>
      </form>
      {result && (
        <div className="space-y-3">
          {result.changes.map((c, i) => (
            <div key={i} className="card">
              <div className="card-body space-y-1">
                <span className={`badge ${c.type === 'added' ? 'badge-low' : c.type === 'removed' ? 'badge-high' : 'badge-medium'}`}>
                  {c.type}
                </span>
                <p className="text-sm text-slate-800">{c.explanation}</p>
                <p className="text-sm text-slate-600"><strong>Practical impact:</strong> {c.impact}</p>
              </div>
            </div>
          ))}
          <p className="text-xs text-slate-500">{DISCLAIMER_TEXT}</p>
        </div>
      )}
    </div>
  );
}
