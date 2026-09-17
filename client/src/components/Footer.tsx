import { DISCLAIMER_TEXT } from '../types';

export function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-white font-semibold text-lg">LegalLens</h3>
            <p className="mt-2 text-sm text-slate-400 max-w-md">
              AI-powered legal document assistant helping everyday users understand,
              compare, and navigate legal documents with confidence.
            </p>
          </div>
          <div>
            <h4 className="text-white font-medium text-sm uppercase tracking-wide">Disclaimer</h4>
            <p className="mt-2 text-sm text-slate-400 max-w-md">{DISCLAIMER_TEXT}</p>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row justify-between gap-4">
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} LegalLens. This tool does not create an attorney-client relationship.
          </p>
          <p className="text-xs text-slate-500">
            For legal advice, consult a licensed attorney in your jurisdiction.
          </p>
        </div>
      </div>
    </footer>
  );
}
