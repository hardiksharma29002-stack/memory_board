'use client';

import React from 'react';
import { X } from 'lucide-react';

interface ScrollNudgeProps {
  onAccept: () => void;
  onDismiss: () => void;
}

export default function ScrollNudge({ onAccept, onDismiss }: ScrollNudgeProps) {
  return (
    <div className="fixed bottom-0 inset-x-0 z-40 p-4 sm:p-6 flex justify-center pointer-events-none animate-in slide-in-from-bottom duration-250">
      <div className="w-full max-w-md bg-surface border border-borderSubtle rounded-t-sheet sm:rounded-card p-5 shadow-sheet pointer-events-auto flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <div>
            <h4 className="font-semibold text-[17px] text-textPrimary leading-snug">
              Looking for a photo?
            </h4>
            <p className="text-[14px] text-textSecondary mt-0.5">
              Find it by what you remember.
            </p>
          </div>
          <button
            type="button"
            onClick={onDismiss}
            className="p-1 rounded-full text-textTertiary hover:text-textPrimary transition cursor-pointer"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 pt-2">
          <button
            type="button"
            onClick={onAccept}
            className="flex-1 py-2.5 px-4 rounded-full font-semibold text-[14px] bg-brand hover:bg-blue-600 text-white transition cursor-pointer text-center"
          >
            Find by memory
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="py-2.5 px-4 rounded-full font-medium text-[14px] text-textSecondary hover:bg-surfaceMuted transition cursor-pointer text-center"
          >
            Not now
          </button>
        </div>
      </div>
    </div>
  );
}
