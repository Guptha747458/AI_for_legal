import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { apiService } from '../services/api';

interface GlossaryPageProps {
  onBack: () => void;
}

const COMMON_TERMS = [
  'indemnify',
  'liability',
  'arbitration',
  'jurisdiction',
  'termination',
  'force majeure',
  'severability',
  'warranty',
];

export function GlossaryPage({ onBack }: GlossaryPageProps) {
  const [term, setTerm] = useState('');
  const [definition, setDefinition] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lookup = async (t: string) => {
    const q = t.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.explainTerm(q);
      setDefinition(res.definition);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Lookup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 text-sm">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back
        </button>
        <h1 className="text-xl font-bold text-slate-900">Legal Glossary</h1>
      </div>
      <p className="text-sm text-slate-600">Click a term or type your own for a plain-language definition.</p>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          lookup(term);
        }}
      >
        <input
          className="input"
          placeholder="e.g. indemnify"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
        <button className="btn-primary" disabled={loading || !term.trim()}>
          Define
        </button>
      </form>
      <div className="flex flex-wrap gap-2">
        {COMMON_TERMS.map((t) => (
          <button key={t} className="btn-outline text-xs" onClick={() => lookup(t)} disabled={loading}>
            {t}
          </button>
        ))}
      </div>
      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}
      {loading && <p className="text-sm text-slate-500">Looking up…</p>}
      {definition && (
        <div className="card">
          <div className="card-body text-sm text-slate-700">{definition}</div>
        </div>
      )}
    </div>
  );
}
