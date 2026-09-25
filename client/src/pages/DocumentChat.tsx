import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { apiService } from '../services/api';
import { DISCLAIMER_TEXT, type QAResponse } from '../types';

interface DocumentChatProps {
  documentId: string;
  onBack: () => void;
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  citations?: string[];
}

const SUGGESTED = [
  'What are my termination rights?',
  'What fees or penalties could apply?',
  'What deadlines should I watch?',
  'Does this auto-renew?',
];

export function DocumentChat({ documentId, onBack }: DocumentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;
    setError(null);
    setMessages((m) => [...m, { role: 'user', text: q }]);
    setInput('');
    setLoading(true);
    try {
      const res: QAResponse = await apiService.answerQuestion(documentId, q, jurisdiction || 'not specified');
      setMessages((m) => [...m, { role: 'assistant', text: res.answer, citations: res.citations }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to answer question');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 text-sm">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back
        </button>
        <h1 className="text-xl font-bold text-slate-900">Document Q&amp;A</h1>
      </div>
      <p className="text-sm text-slate-600">
        Answers are grounded in your uploaded document and cite their sources. This is general
        information, not legal advice.
      </p>
      <input
        className="input"
        placeholder="Jurisdiction (optional)"
        value={jurisdiction}
        onChange={(e) => setJurisdiction(e.target.value)}
      />
      <div className="flex flex-wrap gap-2">
        {SUGGESTED.map((s) => (
          <button key={s} className="btn-outline text-xs" onClick={() => send(s)} disabled={loading}>
            {s}
          </button>
        ))}
      </div>
      <div className="card">
        <div className="card-body space-y-4 max-h-[50vh] overflow-y-auto scrollbar-thin">
          {messages.length === 0 && (
            <p className="text-sm text-slate-500">Ask a question about the document to begin.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
              <div
                className={`inline-block max-w-[90%] rounded-lg px-3 py-2 text-sm ${
                  m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-800'
                }`}
              >
                {m.text}
                {m.citations && m.citations.length > 0 && (
                  <div className="mt-1 text-xs opacity-80">Sources: {m.citations.join(', ')}</div>
                )}
              </div>
            </div>
          ))}
          {loading && <p className="text-sm text-slate-500">Thinking…</p>}
        </div>
      </div>
      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          className="input"
          placeholder="e.g. Can either party terminate early?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="btn-primary" disabled={loading || !input.trim()}>
          Ask
        </button>
      </form>
      <p className="text-xs text-slate-500">{DISCLAIMER_TEXT}</p>
    </div>
  );
}
