'use client';

import React from 'react';
import { QuestionItem } from '../lib/types';
import { ChevronRight } from 'lucide-react';

interface QuestionSheetProps {
  question: QuestionItem;
  stepIndex?: number;
  totalSteps?: number;
  onSelectOption: (questionId: string, optionId: string) => void;
  isLoading?: boolean;
}

export default function QuestionSheet({
  question,
  stepIndex = 1,
  totalSteps = 3,
  onSelectOption,
  isLoading = false,
}: QuestionSheetProps) {
  const { id, prompt, options } = question;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-end sm:items-center justify-center">
      <div className="w-full max-w-lg bg-surface rounded-t-sheet sm:rounded-card p-6 shadow-sheet animate-in slide-in-from-bottom duration-200 border-t sm:border border-borderSubtle">
        {/* Drag handle per pdesign.md Section 24 */}
        <div className="w-12 h-1 bg-borderSubtle rounded-full mx-auto mb-5 sm:hidden" />

        {/* Header & Progress per Section 17 & 18 */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-[13px] font-medium text-textSecondary">
            Let&apos;s try another part of the memory.
          </p>
          <span className="text-[12px] text-textTertiary font-medium">
            {stepIndex} of {totalSteps}
          </span>
        </div>

        <h3 className="text-[20px] sm:text-[22px] font-semibold text-textPrimary leading-[28px] mb-5">
          {prompt}
        </h3>

        {/* 4 Large Option Tiles per Section 17 (touch target >= 48px, rounded 16px) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-5">
          {options.map((opt) => (
            <button
              key={opt.id}
              type="button"
              disabled={isLoading}
              onClick={() => onSelectOption(id, opt.id)}
              className="text-left min-h-[52px] p-3.5 rounded-[16px] bg-surfaceMuted hover:bg-brand-soft hover:border-brand/40 text-textPrimary border border-borderSubtle flex items-center justify-between transition-all cursor-pointer group"
            >
              <span className="font-medium text-[15px]">{opt.label}</span>
              <ChevronRight className="w-4 h-4 text-textTertiary group-hover:text-brand transition" />
            </button>
          ))}
        </div>

        {/* Prominent "Can't recall" Button per Section 17 & 24 */}
        <div className="pt-2 border-t border-borderSubtle">
          <button
            type="button"
            disabled={isLoading}
            onClick={() => onSelectOption(id, 'cant_recall')}
            className="w-full py-3 px-4 rounded-full font-medium text-[15px] text-textSecondary hover:text-textPrimary hover:bg-surfaceMuted transition cursor-pointer text-center"
          >
            Can&apos;t recall
          </button>
        </div>
      </div>
    </div>
  );
}
