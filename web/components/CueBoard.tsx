'use client';

import React, { useState } from 'react';
import { CueCardItem, CognitiveCardItem } from '../lib/types';
import CognitiveCueCard from './CognitiveCueCard';
import { ArrowRight, Send, Sparkles } from 'lucide-react';

interface CueBoardProps {
  cards: CueCardItem[];
  cognitiveCards?: CognitiveCardItem[];
  onSubmitCues: (selectedCueIds: string[]) => void;
  onAddMemoryText?: (text: string) => void;
  onNoneOfThese: () => void;
  onSwitchToSentenceMode?: () => void;
  onGenerateSmartCards?: (query: string) => void;
  isLoading?: boolean;
}

export default function CueBoard({
  cognitiveCards = [],
  onSubmitCues,
  onAddMemoryText,
  onNoneOfThese,
  onGenerateSmartCards,
  isLoading = false,
}: CueBoardProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const [customMemory, setCustomMemory] = useState('');

  const handleToggle = (cueId: string) => {
    setSelected((prev) =>
      prev.includes(cueId) ? prev.filter((id) => id !== cueId) : [...prev, cueId]
    );
  };

  const handleConfirm = () => {
    if (selected.length > 0) {
      onSubmitCues(selected);
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customMemory.trim() && onAddMemoryText) {
      onAddMemoryText(customMemory.trim());
      setCustomMemory('');
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-3">
      {/* Clean minimal header */}
      <div className="flex items-center justify-between gap-2 mb-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-textPrimary mb-0.5">
            Pick any cues you recall
          </h2>
          <p className="text-xs text-textSecondary">
            Select anything that rings a bell, or type what you remember.
          </p>
        </div>

        {onGenerateSmartCards && (
          <button
            type="button"
            onClick={() => onGenerateSmartCards(customMemory)}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-soft text-brand hover:bg-brand hover:text-white transition cursor-pointer shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Smarter AI Cards</span>
          </button>
        )}
      </div>

      {/* Sleek inline type-in */}
      <form onSubmit={handleCustomSubmit} className="mb-4 flex gap-2">
        <input
          type="text"
          value={customMemory}
          onChange={(e) => setCustomMemory(e.target.value)}
          placeholder="Or type a detail (e.g. 'sunset at beach with 2 friends')..."
          className="flex-1 px-3.5 py-2 text-sm rounded-xl bg-canvas dark:bg-slate-900 border border-borderSubtle text-textPrimary placeholder:text-textSecondary focus:border-brand focus:outline-none"
        />
        <button
          type="submit"
          disabled={!customMemory.trim() || isLoading}
          className="px-4 py-2 text-xs font-semibold rounded-xl bg-brand text-white hover:bg-blue-600 disabled:opacity-40 transition flex items-center gap-1.5 shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Add</span>
        </button>
      </form>

      {/* Compact Cue Cards Grid */}
      <div className="space-y-3 mb-6">
        {cognitiveCards.map((card) => (
          <CognitiveCueCard
            key={card.id}
            card={card}
            selectedOptionIds={selected}
            onToggleOption={handleToggle}
          />
        ))}
      </div>

      {/* Clean Bottom Action Bar */}
      <div className="flex items-center justify-between pt-3 border-t border-borderSubtle">
        <button
          type="button"
          disabled={isLoading}
          onClick={onNoneOfThese}
          className="text-xs text-textSecondary hover:text-textPrimary font-medium py-2 px-3 rounded-lg hover:bg-surfaceMuted transition cursor-pointer"
        >
          None of these match
        </button>

        <button
          type="button"
          disabled={selected.length === 0 || isLoading}
          onClick={handleConfirm}
          className="px-5 py-2.5 rounded-xl font-bold text-xs bg-brand hover:bg-blue-600 text-white shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
        >
          <span>Show 4 Albums ({selected.length})</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
