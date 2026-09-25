import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { DISCLAIMER_TEXT } from '../types';

interface DisclaimerBannerProps {
  dismissible?: boolean;
}

export function DisclaimerBanner({ dismissible = false }: DisclaimerBannerProps) {
  const [visible, setVisible] = useState(true);

  if (!visible) {
    return null;
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-sm text-amber-900">
      <div className="max-w-7xl mx-auto flex items-start gap-3">
        <div className="flex-shrink-0">
          <AlertTriangle className="w-5 h-5 text-amber-600" aria-hidden="true" />
        </div>
        <div className="flex-1">
          <p className="font-medium text-amber-900">Important Legal Disclaimer</p>
          <p className="mt-1 text-amber-800">{DISCLAIMER_TEXT}</p>
        </div>
        {dismissible && (
          <button
            type="button"
            onClick={() => setVisible(false)}
            className="flex-shrink-0 text-amber-700 hover:text-amber-900 focus:outline-none focus:ring-2 focus:ring-amber-500 rounded"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  );
}
