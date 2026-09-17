import { useState } from 'react';
import { apiService } from '../services/api';
import { DISCLAIMER_TEXT, type ChecklistResult } from '../types';

interface ActionChecklistProps {
  documentId: string;
  onBack: () => void;
}

export function ActionChecklist({ documentId, onBack }: ActionChecklistProps) {
  const [jurisdiction, setJurisdiction] = useState('');
  const [result, setResult] = useState<ChecklistResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.generateChecklist(documentId, jurisdiction || 'not specified');
      setResult(res);
      setChecked({});
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate checklist');
    } finally {
      setLoading(false);
    }
  };

  const exportText = () => {
    if (!result) return;
    const lines = [
      'LegalLens — Action Checklist (informational only, not legal advice)',
      '',
      'ACTION ITEMS:',
      ...result.action_items.map((a, i) => `${checked[i] ? '[x]' : '[ ]'} [${a.urgency}] ${a.text}`),
      '',
      'QUESTIONS FOR YOUR LAWYER:',
      ...result.questions_for_lawyer.map((q, i) => `${i + 1}. ${q.question}`),
      '',
      DISCLAIMER_TEXT,
    ];
    navigator.clipboard?.writeText(lines.join('\n')).catch(() => {});
  };

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="text-slate-600 hover:text-slate-900 text-sm">← Back</button>
        <h1 className="text-xl font-bold text-slate-900">Action Checklist</h1>
      </div>
      <div className="flex gap-2">
        <input
          className="input"
          placeholder="Jurisdiction (optional)"
          value={jurisdiction}
          onChange={(e) => setJurisdiction(e.target.value)}
        />
        <button className="btn-primary" onClick={generate} disabled={loading}>
          {loading ? 'Generating…' : 'Generate'}
        </button>
        {result && (
          <button className="btn-outline" onClick={exportText}>
            Copy
          </button>
        )}
      </div>
      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}
      {result && (
        <>
          <div className="card">
            <div className="card-header font-medium">Things to verify</div>
            <div className="card-body space-y-2">
              {result.action_items.map((a, i) => (
                <label key={i} className="flex items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!checked[i]}
                    onChange={() => setChecked((c) => ({ ...c, [i]: !c[i] }))}
                    className="mt-1"
                  />
                  <span>
                    <span
                      className={`badge mr-2 ${
                        a.urgency === 'high'
                          ? 'badge-high'
                          : a.urgency === 'medium'
                            ? 'badge-medium'
                            : 'badge-low'
                      }`}
                    >
                      {a.urgency}
                    </span>
                    {a.text}
                  </span>
                </label>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-header font-medium">Questions to ask a lawyer</div>
            <div className="card-body space-y-2">
              {result.questions_for_lawyer.map((q, i) => (
                <p key={i} className="text-sm text-slate-700">
                  {i + 1}. {q.question}
                </p>
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-500">{DISCLAIMER_TEXT}</p>
        </>
      )}
    </div>
  );
}
