export interface Document {
  document_id: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  clause_count?: number;
  total_chars: number;
  job_id: string;
  status: string;
  mode?: 'live' | 'demo';
  clauses?: Clause[];
}

export interface Clause {
  clause_id: string;
  document_id: string;
  text: string;
  char_count: number;
  page_number: number;
  start_pos: number;
  end_pos: number;
  clause_index: number;
  category?: string;
  title?: string;
  heading_level?: number;
  simplified_text?: string;
  key_terms?: string[];
  classification?: Classification;
}

export interface Classification {
  clause_id: string;
  category: string;
  attention_level: 'low' | 'medium' | 'high';
  rationale: string;
  plain_explanation: string;
}

export interface ComparisonChange {
  type: 'added' | 'removed' | 'modified';
  clause_id_old?: string;
  clause_id_new?: string;
  explanation: string;
  impact: string;
}

export interface ComparisonResult {
  changes: ComparisonChange[];
}

export interface QAResponse {
  answer: string;
  citations: string[];
  disclaimer_needed: boolean;
}

export interface ActionItem {
  text: string;
  clause_id: string;
  urgency: 'low' | 'medium' | 'high';
}

export interface LawyerQuestion {
  question: string;
  related_clause_id: string;
}

export interface ChecklistResult {
  action_items: ActionItem[];
  questions_for_lawyer: LawyerQuestion[];
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  created_at: number;
  error: string | null;
  result: Record<string, unknown> | null;
}

export type DocumentType = 
  | 'contract'
  | 'lease'
  | 'employment'
  | 'terms_of_service'
  | 'privacy_policy'
  | 'notice'
  | 'other';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface ClauseCategory {
  value: string;
  label: string;
  color: string;
}

export const CLAUSE_CATEGORIES: ClauseCategory[] = [
  { value: 'obligations', label: 'Obligations', color: 'bg-blue-100 text-blue-800' },
  { value: 'rights', label: 'Rights', color: 'bg-green-100 text-green-800' },
  { value: 'deadlines', label: 'Deadlines', color: 'bg-amber-100 text-amber-800' },
  { value: 'penalties_fees', label: 'Penalties/Fees', color: 'bg-red-100 text-red-800' },
  { value: 'termination', label: 'Termination', color: 'bg-orange-100 text-orange-800' },
  { value: 'auto_renewal', label: 'Auto-renewal', color: 'bg-purple-100 text-purple-800' },
  { value: 'liability_indemnification', label: 'Liability/Indemnification', color: 'bg-rose-100 text-rose-800' },
  { value: 'dispute_resolution', label: 'Dispute Resolution', color: 'bg-indigo-100 text-indigo-800' },
  { value: 'data_privacy', label: 'Data/Privacy', color: 'bg-teal-100 text-teal-800' },
  { value: 'unusual_nonstandard', label: 'Unusual/Non-standard', color: 'bg-slate-100 text-slate-800' },
];

export const DOCUMENT_TYPES: { value: DocumentType; label: string }[] = [
  { value: 'contract', label: 'General Contract' },
  { value: 'lease', label: 'Lease/Rental Agreement' },
  { value: 'employment', label: 'Employment Agreement' },
  { value: 'terms_of_service', label: 'Terms of Service' },
  { value: 'privacy_policy', label: 'Privacy Policy' },
  { value: 'notice', label: 'Legal Notice' },
  { value: 'other', label: 'Other' },
];

export const DISCLAIMER_TEXT = `LegalLens provides general information and document interpretation help, not legal advice. It does not create an attorney-client relationship. For decisions with real consequences, please consult a licensed attorney in your jurisdiction.`;