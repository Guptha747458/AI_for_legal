import axios from 'axios';
import type {
  Classification,
  ComparisonResult,
  QAResponse,
  ChecklistResult,
  JobStatus,
  DocumentType,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
});

export interface UploadResult {
  document_id: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  clause_count: number;
  total_chars: number;
  clauses: Array<{
    clause_id: string;
    text: string;
    page_number: number;
    clause_index: number;
    title?: string | null;
  }>;
  job_id: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  mode?: 'live' | 'demo';
}

export interface AnalysisResponse<T> {
  data: T;
}

export const apiService = {
  uploadDocument: async (
    file: File,
    documentType: DocumentType,
    jurisdiction: string,
  ): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    formData.append('jurisdiction', jurisdiction);

    const response = await api.post<UploadResult>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  pollJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await api.get<JobStatus>(`/jobs/${jobId}`);
    return response.data;
  },

  classifyClause: async (
    clauseId: string,
    documentId: string,
    documentType: DocumentType,
    jurisdiction: string,
  ): Promise<Classification> => {
    const response = await api.post<Classification>(`/analyze/classify/${clauseId}`, null, {
      params: {
        document_id: documentId,
        document_type: documentType,
        jurisdiction,
      },
    });
    return response.data;
  },

  simplifySection: async (
    sectionId: string,
    documentId: string,
    documentType: DocumentType,
  ): Promise<{ section_id: string; simplified_text: string; key_terms: string[] }> => {
    const response = await api.post(
      `/analyze/simplify/${sectionId}`,
      null,
      {
        params: {
          document_id: documentId,
          document_type: documentType,
        },
      },
    );
    return response.data;
  },

  compareDocuments: async (
    documentId1: string,
    documentId2: string,
    documentType: DocumentType,
    jurisdiction: string,
  ): Promise<ComparisonResult> => {
    const response = await api.post<ComparisonResult>(
      '/analyze/compare',
      null,
      {
        params: {
          document_id_1: documentId1,
          document_id_2: documentId2,
          document_type: documentType,
          jurisdiction,
        },
      },
    );
    return response.data;
  },

  answerQuestion: async (
    documentId: string,
    question: string,
    jurisdiction: string,
  ): Promise<QAResponse> => {
    const response = await api.post<QAResponse>(
      '/analyze/qa',
      {
        document_id: documentId,
        question,
        jurisdiction,
      },
    );
    return response.data;
  },

  generateChecklist: async (
    documentId: string,
    jurisdiction: string,
  ): Promise<ChecklistResult> => {
    const response = await api.post<ChecklistResult>(
      '/analyze/checklist',
      {
        document_id: documentId,
        jurisdiction,
      },
    );
    return response.data;
  },

  clearJob: async (jobId: string): Promise<{ status: string }> => {
    const response = await api.post<{ status: string }>(`/jobs/${jobId}/clear`);
    return response.data;
  },

  getDocument: async (documentId: string) => {
    const response = await api.get(`/documents/${documentId}`);
    return response.data as {
      document_id: string;
      filename: string;
      clauses: Array<{
        clause_id: string;
        text: string;
        page_number: number;
        clause_index: number;
        title?: string | null;
      }>;
    };
  },

  explainTerm: async (term: string, context = '') => {
    const response = await api.post('/analyze/glossary', { term, context });
    return response.data as { term: string; definition: string; demo?: boolean };
  },

  deleteDocument: async (documentId: string) => {
    const response = await api.delete(`/documents/${documentId}`);
    return response.data;
  },
};

export default api;