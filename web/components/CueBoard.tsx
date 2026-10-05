'use client';

import React, { useState, useEffect } from 'react';
import { CueCardItem, CognitiveCardItem } from '../lib/types';
import CognitiveCueCard from './CognitiveCueCard';
import { ArrowRight, Send, Sparkles, Zap } from 'lucide-react';

interface CueBoardProps {
  cards: CueCardItem[];
  cognitiveCards?: CognitiveCardItem[];
  initialSelected?: string[];
  searchQuery?: string;
  onSubmitCues: (selectedCueIds: string[]) => void;
  onAddMemoryText?: (text: string) => void;
  onNoneOfThese: () => void;
  onSkipToAlbums?: () => void;
  onSwitchToSentenceMode?: () => void;
  onGenerateSmartCards?: (query: string) => void;
  isLoading?: boolean;
}

export default function CueBoard({
  cognitiveCards = [],
  initialSelected = [],
  searchQuery = '',
  onSubmitCues,
  onAddMemoryText,
  onNoneOfThese,
  onSkipToAlbums,
  onGenerateSmartCards,
  isLoading = false,
}: CueBoardProps) {
  const [selected, setSelected] = useState<string[]>(initialSelected);
  const [customMemory, setCustomMemory] = useState('');

  // Synchronize when initialSelected changes (e.g. from parsed query)
  useEffect(() => {
    if (initialSelected && initialSelected.length > 0) {
      setSelected((prev) => Array.from(new Set([...prev, ...initialSelected])));
    }
  }, [initialSelected]);

  const handleToggle = (cueId: string) => {
    setSelected((prev) =>
      prev.includes(cueId) ? prev.filter((id) => id !== cueId) : [...prev, cueId]
    );
  };

  const handleConfirm = () => {
    onSubmitCues(selected);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customMemory.trim() && onAddMemoryText) {
      onAddMemoryText(customMemory.trim());
      setCustomMemory('');
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-2 sm:px-4 py-3">
      {/* 1. Header with Cognitive Memory Framing */}
      <div className="mb-4">
        <div className="flex items-center justify-between gap-3 flex-wrap mb-1">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-brand bg-brand-soft px-2.5 py-1 rounded-full inline-block mb-1.5 border border-brand/20">
              Cognitive Memory Completion
            </span>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-textPrimary">
              Complete Your Photo Memory
            </h2>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {onGenerateSmartCards && (
              <button
                type="button"
                onClick={() => onGenerateSmartCards(customMemory || searchQuery)}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-soft text-brand hover:bg-brand hover:text-white transition cursor-pointer shadow-2xs border border-brand/30"
                title="Use Groq AI to synthesize smarter memory cards from your search"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Smarter AI Cards</span>
              </button>
            )}

            <button
              type="button"
              onClick={onSkipToAlbums || onNoneOfThese}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-amber-500/15 hover:bg-amber-500/25 text-amber-800 dark:text-amber-200 border border-amber-500/40 hover:border-amber-500/70 transition cursor-pointer shadow-xs active:scale-95"
              title="Skip straight to candidate albums without selecting cards"
            >
              <Zap className="w-4 h-4 text-amber-600 dark:text-amber-400" />
              <span>Skip Straight to 4 Albums →</span>
            </button>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-textSecondary max-w-2xl leading-relaxed">
          {searchQuery ? (
            <>
              Found candidate moments matching <strong className="text-textPrimary">&ldquo;{searchQuery}&rdquo;</strong> across your 400 photos. Since memory is often incomplete, choose any details below to anchor your lost context:
            </>
          ) : (
            'Found photos with similar context. Pick any details you recall below to help complete your vague memory and locate the exact album.'
          )}
        </p>
      </div>

      {/* 2. Detail prompt input */}
      <form onSubmit={handleCustomSubmit} className="mb-5 flex gap-2">
        <input
          type="text"
          value={customMemory}
          onChange={(e) => setCustomMemory(e.target.value)}
          placeholder="Remember a detail? (e.g. 'sunset at beach', 'with 2 friends', 'candlelight')..."
          className="flex-1 px-4 py-2.5 text-xs sm:text-sm rounded-xl bg-canvas dark:bg-slate-900 border border-borderSubtle text-textPrimary placeholder:text-textSecondary focus:border-brand focus:outline-none shadow-2xs"
        />
        <button
          type="submit"
          disabled={!customMemory.trim() || isLoading}
          className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-brand text-white hover:bg-blue-600 disabled:opacity-40 transition flex items-center gap-1.5 shrink-0 shadow-2xs cursor-pointer"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Add Detail</span>
        </button>
      </form>

      {/* 3. The 4 Big Square Cognitive Cards in 2x2 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {cognitiveCards.map((card, idx) => (
          <CognitiveCueCard
            key={card.id}
            card={card}
            cardIndex={idx}
            selectedOptionIds={selected}
            onToggleOption={handleToggle}
          />
        ))}
      </div>

      {/* 4. Action Bar */}
      <div className="flex items-center justify-between pt-4 border-t border-borderSubtle gap-3 flex-wrap">
        <button
          type="button"
          disabled={isLoading}
          onClick={onSkipToAlbums || onNoneOfThese}
          className="text-xs sm:text-sm text-textSecondary hover:text-textPrimary font-semibold py-2 px-3 rounded-lg hover:bg-surfaceMuted transition cursor-pointer flex items-center gap-1.5"
        >
          <Zap className="w-4 h-4 text-amber-500" />
          <span>Skip Straight to 4 Albums →</span>
        </button>

        <button
          type="button"
          disabled={isLoading}
          onClick={handleConfirm}
          className="px-6 py-3 rounded-xl font-bold text-xs sm:text-sm bg-brand hover:bg-blue-600 text-white shadow-md transition flex items-center gap-2 cursor-pointer"
        >
          {selected.length > 0 ? (
            <>
              <span>Reveal 4 Macro Albums ({selected.length} Cues Completed)</span>
              <ArrowRight className="w-4 h-4" />
            </>
          ) : (
            <>
              <span>Reveal 4 Macro Albums</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
