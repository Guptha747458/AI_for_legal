import React, { useState, useRef } from 'react';
import { AlertTriangle, Check, LoaderCircle, Upload } from 'lucide-react';
import { apiService } from '../services/api';
import { useApp } from '../hooks/AppContext';
import type { DocumentType } from '../types';

interface DocumentUploadProps {
  onUploadComplete: (docId: string) => void;
}

export function DocumentUpload({ onUploadComplete }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType>('contract');
  const [jurisdiction, setJurisdiction] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { dispatch } = useApp();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.size > 20 * 1024 * 1024) {
        setError('File is too large. Maximum size is 20MB.');
        return;
      }
      setFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      if (files[0].size > 20 * 1024 * 1024) {
        setError('File is too large. Maximum size is 20MB.');
        return;
      }
      setFile(files[0]);
      setError(null);
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const text = e.clipboardData.getData('text/plain');
    if (text) {
      const blob = new Blob([text], { type: 'text/plain' });
      const fakeFile = new File([blob], 'pasted-text.txt', { type: 'text/plain' });
      setFile(fakeFile);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setIsUploading(true);
    try {
      const result = await apiService.uploadDocument(file, documentType, jurisdiction);
      dispatch({ type: 'ADD_DOCUMENT', document: result as any });
      setTimeout(() => onUploadComplete(result.document_id), 500);
    } catch (err) {
      const detail =
        typeof err === 'object' && err !== null && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError(detail || (err instanceof Error ? err.message : 'Failed to upload document'));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Upload Your Document</h1>
      <p className="text-slate-600 mb-6">
        Upload a contract, lease, or other legal document to get started. We support PDF, DOCX, and plain text files.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6" onPaste={handlePaste}>
        {/* File Upload Zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragOver
              ? 'border-blue-500 bg-blue-50'
              : file
              ? 'border-green-400 bg-green-50'
              : 'border-slate-300 hover:border-slate-400 bg-white'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click();
          }}
          role="button"
          tabIndex={0}
          aria-label="Choose a document to upload"
        >
          <input
            ref={fileInputRef}
            id="document-file"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            className="sr-only"
          />
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-12 h-12 text-slate-400" aria-hidden="true" />
            <div>
              <p className="text-sm font-medium text-slate-700">
                {file ? file.name : 'Drop your file here or click to browse'}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                PDF, DOCX, or TXT — up to 20MB
              </p>
            </div>
            {file && (
              <span className="badge bg-green-100 text-green-800">
                <Check className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                Ready
              </span>
            )}
          </div>
        </div>

        {/* Document Type */}
        <div>
          <label className="label" htmlFor="document-type">Document Type</label>
          <select
            id="document-type"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value as DocumentType)}
            className="input"
          >
            <option value="contract">General Contract</option>
            <option value="lease">Lease / Rental Agreement</option>
            <option value="employment">Employment Agreement</option>
            <option value="terms_of_service">Terms of Service</option>
            <option value="privacy_policy">Privacy Policy</option>
            <option value="notice">Legal Notice</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Jurisdiction (Optional) */}
        <div>
          <label className="label" htmlFor="jurisdiction">
            Jurisdiction <span className="text-slate-400">(optional)</span>
          </label>
          <input
            type="text"
            id="jurisdiction"
            placeholder="e.g., California, USA or England and Wales"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            className="input"
          />
          <p className="mt-1 text-xs text-slate-500">
            Helps tailor interpretations. Not required to use the tool.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div role="alert" className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={isUploading || !file}
          className="btn-primary w-full py-3 text-base"
        >
          {isUploading ? (
            <span className="flex items-center justify-center gap-2">
              <LoaderCircle className="animate-spin h-5 w-5" aria-hidden="true" />
              Processing...
            </span>
          ) : (
            'Upload & Analyze'
          )}
        </button>
      </form>

      {/* Disclaimer */}
      <div className="mt-8 card p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-sm text-slate-600">
            <p className="font-medium text-slate-900 mb-1">Before you proceed</p>
            <p>
              This tool is an informational aid, not a substitute for a licensed attorney.
              It does not create an attorney-client relationship. Documents are processed
              temporarily and not persisted without explicit consent.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
