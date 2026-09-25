import React, { useState, useCallback } from 'react';
import { Scale } from 'lucide-react';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { Footer } from './components/Footer';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentViewer } from './pages/DocumentViewer';
import { DocumentComparison } from './pages/DocumentComparison';
import { DocumentChat } from './pages/DocumentChat';
import { ActionChecklist } from './pages/ActionChecklist';
import { GlossaryPage } from './pages/GlossaryPage';
import { useApp } from './hooks/AppContext';

type Page = 'upload' | 'viewer' | 'compare' | 'chat' | 'checklist' | 'glossary';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('upload');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [compareDocIds, setCompareDocIds] = useState<string[]>([]);

  const handleNavigate = useCallback(
    (page: Page, docId?: string) => {
      setCurrentPage(page);
      if (docId) setSelectedDocId(docId);
    },
    [],
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <DisclaimerBanner />

      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-16 flex-col items-stretch gap-2 py-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:py-0">
            <div className="flex min-w-0 items-center gap-3">
              <button
                onClick={() => handleNavigate('upload')}
                className="inline-flex shrink-0 items-center gap-2 text-xl font-bold text-blue-700 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              >
                <Scale className="h-5 w-5" aria-hidden="true" />
                LegalLens
              </button>
              <span className="truncate text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                Informational Aid Only
              </span>
            </div>
            <nav className="-mx-1 flex min-w-0 items-center gap-1 overflow-x-auto px-1 pb-1 sm:mx-0 sm:overflow-visible sm:px-0 sm:pb-0" aria-label="Primary navigation">
              {['upload', 'viewer', 'compare', 'chat', 'checklist', 'glossary'].map(
                (page) => (
                  <button
                    key={page}
                    onClick={() => handleNavigate(page as Page)}
                    aria-current={currentPage === page ? 'page' : undefined}
                    className={`shrink-0 px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      currentPage === page
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    {page.charAt(0).toUpperCase() + page.slice(1)}
                  </button>
                ),
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        {currentPage === 'upload' && (
          <DocumentUpload
            onUploadComplete={(docId) => {
              handleNavigate('viewer', docId);
            }}
          />
        )}
        {currentPage === 'viewer' &&
          (selectedDocId ? (
            <DocumentViewer documentId={selectedDocId} onBack={() => handleNavigate('upload')} />
          ) : (
            <DocPicker
              label="Select a document to view"
              onPick={(id) => handleNavigate('viewer', id)}
              onUpload={() => handleNavigate('upload')}
            />
          ))}
        {currentPage === 'compare' && (
          <DocumentComparison
            docIds={compareDocIds}
            onCompare={(ids) => setCompareDocIds(ids)}
            onBack={() => handleNavigate('upload')}
          />
        )}
        {currentPage === 'chat' &&
          (selectedDocId ? (
            <DocumentChat documentId={selectedDocId} onBack={() => handleNavigate('upload')} />
          ) : (
            <DocPicker
              label="Select a document to chat with"
              onPick={(id) => handleNavigate('chat', id)}
              onUpload={() => handleNavigate('upload')}
            />
          ))}
        {currentPage === 'checklist' &&
          (selectedDocId ? (
            <ActionChecklist documentId={selectedDocId} onBack={() => handleNavigate('upload')} />
          ) : (
            <DocPicker
              label="Select a document for a checklist"
              onPick={(id) => handleNavigate('checklist', id)}
              onUpload={() => handleNavigate('upload')}
            />
          ))}
        {currentPage === 'glossary' && (
          <GlossaryPage onBack={() => handleNavigate('upload')} />
        )}
      </main>

      <Footer />
    </div>
  );
}

function DocPicker({
  label,
  onPick,
  onUpload,
}: {
  label: string;
  onPick: (id: string) => void;
  onUpload: () => void;
}) {
  const { state } = useApp();
  if (state.documents.length === 0) {
    return (
      <div className="card max-w-xl mx-auto">
        <div className="card-body text-center space-y-3">
          <p className="text-slate-600">No documents uploaded yet.</p>
          <button className="btn-primary" onClick={onUpload}>
            Upload a document
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="max-w-xl mx-auto space-y-3">
      <h2 className="font-medium text-slate-900">{label}</h2>
      {state.documents.map((d) => (
        <button key={d.document_id} className="card w-full text-left hover:shadow-md" onClick={() => onPick(d.document_id)}>
          <div className="card-body">
            <p className="font-medium text-slate-900">{d.filename}</p>
            <p className="text-xs text-slate-500">{d.clause_count ?? d.chunk_count} clauses</p>
          </div>
        </button>
      ))}
    </div>
  );
}
