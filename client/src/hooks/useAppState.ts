import type { Document } from '../types';

export interface AppState {
  documents: Document[];
  activeDocumentId: string | null;
  comparisonDocumentIds: string[];
  analysisResults: Record<string, unknown>;
}

export const initialState: AppState = {
  documents: [],
  activeDocumentId: null,
  comparisonDocumentIds: [],
  analysisResults: {},
};

export type AppAction =
  | { type: 'ADD_DOCUMENT'; document: Document }
  | { type: 'SET_ACTIVE_DOCUMENT'; documentId: string | null }
  | { type: 'SET_COMPARISON_DOCUMENTS'; documentIds: string[] }
  | { type: 'SET_ANALYSIS_RESULT'; documentId: string; result: unknown };

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'ADD_DOCUMENT':
      return {
        ...state,
        documents: [...state.documents, action.document],
      };
    case 'SET_ACTIVE_DOCUMENT':
      return {
        ...state,
        activeDocumentId: action.documentId,
      };
    case 'SET_COMPARISON_DOCUMENTS':
      return {
        ...state,
        comparisonDocumentIds: action.documentIds,
      };
    case 'SET_ANALYSIS_RESULT':
      return {
        ...state,
        analysisResults: {
          ...state.analysisResults,
          [action.documentId]: action.result,
        },
      };
    default:
      return state;
  }
}