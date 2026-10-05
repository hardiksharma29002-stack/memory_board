'use client';

import React from 'react';
import { X, Sparkles, Zap, Brain } from 'lucide-react';

interface ScrollNudgeProps {
  stage?: 'initial' | 'scrolling_detected';
  onAccept: () => void;
  onDismiss: () => void;
}

export default function ScrollNudge({
  stage = 'initial',
  onAccept,
  onDismiss,
}: ScrollNudgeProps) {
  const isScrollingDetected = stage === 'scrolling_detected';

  return (
    <aside
      aria-label="Photo Retrieval Assistant Nudge"
      className="fixed bottom-0 inset-x-0 z-40 p-3 sm:p-5 flex justify-center pointer-events-none animate-in slide-in-from-bottom duration-250"
    >
      <div
        className={`w-full max-w-md bg-surface dark:bg-slate-900 border rounded-2xl p-4 sm:p-5 shadow-2xl pointer-events-auto flex flex-col gap-3 transition-all duration-300 ${
          isScrollingDetected
            ? 'border-amber-500/60 dark:border-amber-400/50 ring-2 ring-amber-500/20 shadow-amber-500/10'
            : 'border-borderSubtle dark:border-slate-800'
        }`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            {/* Status Badge */}
            {isScrollingDetected ? (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30 text-[11px] font-bold tracking-wide mb-1.5 animate-pulse">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                </span>
                <Zap className="w-3 h-3 text-amber-600 dark:text-amber-400" />
                <span>Scrolling detected</span>
              </div>
            ) : (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand/10 text-brand dark:text-blue-400 border border-brand/20 text-[11px] font-bold tracking-wide mb-1.5">
                <Brain className="w-3 h-3 text-brand" />
                <span>Find photos by memory</span>
              </div>
            )}

            <h4 className="font-bold text-[16px] sm:text-[17px] text-textPrimary leading-snug">
              {isScrollingDetected ? 'Still scrolling through photos?' : 'Looking for a photo?'}
            </h4>
            <p className="text-[13px] sm:text-[14px] text-textSecondary mt-0.5 leading-relaxed">
              {isScrollingDetected
                ? 'Scrolling detected! Skip manual hunting — find your exact photo by what you remember.'
                : 'Find photos by what you remember (lighting, people count, setting) instead of endless searching.'}
            </p>
          </div>

          <button
            type="button"
            onClick={onDismiss}
            className="p-1.5 rounded-full text-textTertiary hover:text-textPrimary hover:bg-surfaceMuted transition cursor-pointer shrink-0"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 pt-1">
          <button
            type="button"
            onClick={onAccept}
            className={`flex-1 py-2.5 px-4 rounded-xl font-bold text-[14px] text-white transition cursor-pointer flex items-center justify-center gap-2 shadow-sm ${
              isScrollingDetected
                ? 'bg-amber-600 hover:bg-amber-700 active:scale-98'
                : 'bg-brand hover:bg-blue-600 active:scale-98'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Find by memory</span>
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="py-2.5 px-4 rounded-xl font-medium text-[13px] text-textSecondary hover:bg-surfaceMuted hover:text-textPrimary transition cursor-pointer text-center"
          >
            Not now
          </button>
        </div>
      </div>
    </aside>
  );
}
