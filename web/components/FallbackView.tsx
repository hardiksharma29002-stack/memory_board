'use client';

import React, { useState } from 'react';
import { Check, RefreshCw, Sparkles, Send, ShieldAlert, Compass } from 'lucide-react';
import { ClueItem, FollowupProbeItem } from '../lib/types';

interface FallbackViewProps {
  message: string;
  level?: number;
  relaxedClueIds?: string[];
  suggestedQuestionId?: string;
  clues?: ClueItem[];
  followupProbes?: FollowupProbeItem[];
  preservedContext?: string[];
  onTryAgain: () => void;
  onSelectProbeOption: (optionText: string) => void;
  onAddMemoryText: (text: string) => void;
  onViewFilteredTimeline: () => void;
  isLoading?: boolean;
}

export default function FallbackView({
  message,
  clues = [],
  followupProbes = [],
  preservedContext = [],
  onTryAgain,
  onSelectProbeOption,
  onAddMemoryText,
  onViewFilteredTimeline,
  isLoading = false,
}: FallbackViewProps) {
  const [typedMemory, setTypedMemory] = useState('');

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (typedMemory.trim()) {
      onAddMemoryText(typedMemory.trim());
      setTypedMemory('');
    }
  };

  const activeContextLabels =
    clues.length > 0
      ? clues.map((c) => c.label)
      : preservedContext.length > 0
      ? preservedContext
      : ['Previous search context'];

  return (
    <main
      aria-label="Memory Search Recovery Assistant"
      className="w-full max-w-2xl mx-auto px-4 py-6"
    >
      {/* 1. Header with clear high-contrast explanation */}
      <header className="mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800 text-xs font-bold uppercase tracking-wider mb-2">
          <ShieldAlert className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span>Refining Memory Trail (Zero Context Lost)</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-textPrimary leading-tight mb-2">
          Let&apos;s probe a different memory angle.
        </h2>
        <p className="text-base text-textSecondary leading-relaxed">
          {message || 'We kept your exact clues in memory and synthesized new contextual probes.'}
        </p>
      </header>

      {/* 2. Persistent Context Trail: NEVER LOSE CONTEXT */}
      <section
        aria-label="Preserved Memory Context"
        className="bg-brand/5 dark:bg-brand/10 rounded-2xl p-4 sm:p-5 border-2 border-brand/30 mb-6 shadow-sm"
      >
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-brand" aria-hidden="true" />
          <h3 className="text-sm font-extrabold uppercase tracking-wider text-brand">
            Preserved Active Clues ({activeContextLabels.length})
          </h3>
        </div>
        <p className="text-xs text-textSecondary mb-3">
          These memory anchors remain active and locked into your search:
        </p>
        <div className="flex flex-wrap gap-2" role="list">
          {activeContextLabels.map((clueLabel, idx) => (
            <span
              key={idx}
              role="listitem"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-white dark:bg-slate-800 text-textPrimary border border-borderSubtle shadow-xs"
            >
              <Check className="w-3.5 h-3.5 text-emerald-600 stroke-[3]" aria-hidden="true" />
              <span>{clueLabel}</span>
            </span>
          ))}
        </div>
      </section>

      {/* 3. Follow-up Contextual Memory Probes (Synthesized from clues) */}
      {followupProbes.length > 0 && (
        <section
          aria-label="Contextual Memory Probes"
          className="bg-surface rounded-2xl p-5 border-2 border-slate-200 dark:border-slate-800 shadow-md mb-6"
        >
          <div className="flex items-center gap-2 mb-3">
            <Compass className="w-5 h-5 text-indigo-500" aria-hidden="true" />
            <h3 className="text-lg font-bold text-textPrimary">
              Do any of these related details jog your memory?
            </h3>
          </div>
          <p className="text-sm text-textSecondary mb-4">
            Select an option to immediately tighten candidate albums:
          </p>

          <div className="space-y-4">
            {followupProbes.map((probe, pIdx) => (
              <div key={pIdx} className="bg-canvas dark:bg-slate-900 p-4 rounded-xl border border-borderSubtle">
                <p className="font-semibold text-sm text-textPrimary mb-2.5">
                  {pIdx + 1}. {probe.question}
                </p>
                <div className="flex flex-wrap gap-2">
                  {probe.options.map((opt, oIdx) => (
                    <button
                      key={oIdx}
                      type="button"
                      disabled={isLoading}
                      onClick={() => onSelectProbeOption(opt)}
                      aria-label={`Select clue: ${opt}`}
                      className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-surface hover:bg-brand hover:text-white text-textPrimary border border-slate-300 dark:border-slate-700 transition min-h-[38px] flex items-center gap-1.5 cursor-pointer shadow-xs focus:ring-2 focus:ring-brand"
                    >
                      <span>+ {opt}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 4. Type or select at each point */}
      <section
        aria-label="Type Additional Clue"
        className="bg-surface rounded-2xl p-5 border-2 border-slate-200 dark:border-slate-800 shadow-md mb-6"
      >
        <h3 className="text-sm font-bold uppercase tracking-wider text-textSecondary mb-2">
          Or Type Any Specific Detail You Remember
        </h3>
        <form onSubmit={handleCustomSubmit} className="flex flex-col sm:flex-row gap-3">
          <label htmlFor="fallback-type-input" className="sr-only">
            Type additional memory detail
          </label>
          <input
            id="fallback-type-input"
            type="text"
            value={typedMemory}
            onChange={(e) => setTypedMemory(e.target.value)}
            placeholder="e.g. 'taken near water', 'red jacket', 'birthday cake'..."
            className="flex-1 px-4 py-3 rounded-xl bg-canvas dark:bg-slate-900 border-2 border-borderSubtle text-textPrimary placeholder:text-textSecondary text-sm min-h-[44px] focus:outline-none focus:border-brand"
          />
          <button
            type="submit"
            disabled={!typedMemory.trim() || isLoading}
            aria-label="Submit typed memory detail"
            className="px-5 py-3 rounded-xl font-bold text-sm bg-brand text-white hover:bg-blue-600 disabled:opacity-40 transition flex items-center justify-center gap-2 min-h-[44px] shadow-sm"
          >
            <Send className="w-4 h-4" aria-hidden="true" />
            <span>Search Albums</span>
          </button>
        </form>
      </section>

      {/* 5. Simulated Hiding Places Checked (Archive, Trash, Locked, Unbacked) */}
      <section
        aria-label="Hiding Places Checked"
        className="bg-surface rounded-2xl p-4 sm:p-5 border border-borderSubtle shadow-sm mb-6"
      >
        <p className="text-xs font-bold uppercase tracking-wider text-textSecondary mb-3">
          Verified Photo Locations Checked
        </p>
        <div className="grid grid-cols-2 gap-3" role="list">
          <div role="listitem" className="flex items-center gap-2 text-sm text-textPrimary">
            <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center justify-center font-bold">
              ✓
            </span>
            <span>Archive</span>
          </div>
          <div role="listitem" className="flex items-center gap-2 text-sm text-textPrimary">
            <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center justify-center font-bold">
              ✓
            </span>
            <span>Trash</span>
          </div>
          <div role="listitem" className="flex items-center gap-2 text-sm text-textPrimary">
            <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center justify-center font-bold">
              ✓
            </span>
            <span>Locked folder</span>
          </div>
          <div role="listitem" className="flex items-center gap-2 text-sm text-textPrimary">
            <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center justify-center font-bold">
              ✓
            </span>
            <span>Device Storage</span>
          </div>
        </div>
      </section>

      {/* 6. Action Buttons */}
      <footer className="flex flex-col gap-3">
        <button
          type="button"
          disabled={isLoading}
          onClick={onTryAgain}
          aria-label="Re-evaluate macro albums with loosened clues"
          className="w-full py-4 px-6 rounded-2xl font-bold text-base bg-brand hover:bg-blue-600 text-white shadow-md flex items-center justify-center gap-2 cursor-pointer transition min-h-[50px] focus:ring-4 focus:ring-blue-300"
        >
          <RefreshCw className="w-4 h-4" aria-hidden="true" />
          <span>Loosen Clues &amp; Refresh 4 Macro Albums</span>
        </button>

        <button
          type="button"
          disabled={isLoading}
          onClick={onViewFilteredTimeline}
          aria-label="View all matching photos across the library timeline"
          className="w-full py-3.5 px-6 rounded-2xl font-semibold text-sm text-textSecondary hover:bg-surfaceMuted transition cursor-pointer text-center min-h-[44px]"
        >
          Browse All Photos In Timeline
        </button>
      </footer>
    </main>
  );
}
