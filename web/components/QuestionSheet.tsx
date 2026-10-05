'use client';

import React from 'react';
import { QuestionItem } from '../lib/types';
import { ChevronRight, HelpCircle, X } from 'lucide-react';

interface QuestionSheetProps {
  question: QuestionItem;
  stepIndex?: number;
  totalSteps?: number;
  onSelectOption: (questionId: string, optionId: string) => void;
  onClose?: () => void;
  isLoading?: boolean;
}

export default function QuestionSheet({
  question,
  stepIndex = 1,
  totalSteps = 3,
  onSelectOption,
  onClose,
  isLoading = false,
}: QuestionSheetProps) {
  const { id, prompt, options } = question;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-surface dark:bg-slate-900 rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl animate-in slide-in-from-bottom duration-250 border-t sm:border border-borderSubtle dark:border-slate-800">
        {/* Drag handle for mobile */}
        <div className="w-12 h-1 bg-borderSubtle dark:bg-slate-700 rounded-full mx-auto mb-4 sm:hidden" />

        {/* Header & Progress */}
        <div className="flex items-center justify-between mb-3">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-soft text-brand dark:text-blue-400 text-xs font-bold">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Guided Recall Question {stepIndex} of {totalSteps}</span>
          </div>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-full text-textTertiary hover:text-textPrimary hover:bg-surfaceMuted transition cursor-pointer"
              title="Close and return to albums"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <h3 className="text-xl sm:text-2xl font-bold text-textPrimary leading-snug mb-5">
          {prompt}
        </h3>

        {/* 4 Large Option Tiles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-5">
          {options.map((opt) => (
            <button
              key={opt.id}
              type="button"
              disabled={isLoading}
              onClick={() => onSelectOption(id, opt.id)}
              className="text-left min-h-[56px] p-3.5 rounded-2xl bg-surfaceMuted dark:bg-slate-800 hover:bg-brand-soft dark:hover:bg-blue-950/40 hover:border-brand/50 text-textPrimary border border-borderSubtle dark:border-slate-700 flex items-center justify-between transition-all cursor-pointer group shadow-2xs active:scale-98"
            >
              <span className="font-semibold text-[15px]">{opt.label}</span>
              <ChevronRight className="w-4 h-4 text-textTertiary group-hover:text-brand transition shrink-0 ml-2" />
            </button>
          ))}
        </div>

        {/* Prominent "Can't recall" Button */}
        <div className="pt-3 border-t border-borderSubtle dark:border-slate-800 flex items-center justify-between gap-3">
          <button
            type="button"
            disabled={isLoading}
            onClick={() => onSelectOption(id, 'cant_recall')}
            className="flex-1 py-3 px-4 rounded-xl font-bold text-[14px] text-textSecondary hover:text-textPrimary bg-surfaceMuted hover:bg-borderSubtle/60 dark:bg-slate-800 dark:hover:bg-slate-700 transition cursor-pointer text-center"
          >
            Can&apos;t recall
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="py-3 px-4 rounded-xl text-xs font-semibold text-textTertiary hover:text-textSecondary transition cursor-pointer"
            >
              Back to albums
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
