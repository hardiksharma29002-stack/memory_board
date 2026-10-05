'use client';

import React, { useState } from 'react';
import { ArrowLeft, X } from 'lucide-react';

interface SentenceModeProps {
  onBackToCards: () => void;
  onSubmitSentence: (blanks: Record<string, string>) => void;
  isLoading?: boolean;
}

interface BlankOption {
  id: string;
  label: string;
  cueId: string;
}

const BLANK_DEFINITIONS: Record<
  string,
  { label: string; placeholder: string; options: BlankOption[] }
> = {
  time: {
    label: 'Time of day',
    placeholder: 'time of day',
    options: [
      { id: 'morning', label: 'Morning', cueId: 'time_morning' },
      { id: 'afternoon', label: 'Afternoon', cueId: 'time_afternoon' },
      { id: 'evening', label: 'Evening', cueId: 'time_evening' },
      { id: 'night', label: 'Night', cueId: 'time_night' },
    ],
  },
  setting: {
    label: 'Setting',
    placeholder: 'setting',
    options: [
      { id: 'outdoors', label: 'Outdoors', cueId: 'setting_outdoors' },
      { id: 'indoors', label: 'Indoors', cueId: 'setting_indoors' },
      { id: 'street', label: 'Street / Market', cueId: 'setting_street' },
      { id: 'event', label: 'Event / Celebration', cueId: 'setting_event' },
    ],
  },
  people: {
    label: 'People',
    placeholder: 'how many people',
    options: [
      { id: 'solo', label: '1 person', cueId: 'people_solo' },
      { id: 'pair', label: '2 people', cueId: 'people_pair' },
      { id: 'group', label: '3–5 people', cueId: 'people_group' },
      { id: 'crowd', label: 'A crowd', cueId: 'people_crowd' },
    ],
  },
  look: {
    label: 'Look or Vibe',
    placeholder: 'what stood out',
    options: [
      { id: 'warm', label: 'Warm yellow light', cueId: 'lighting_warm' },
      { id: 'colorful', label: 'Bright & colourful', cueId: 'color_colorful' },
      { id: 'food', label: 'Food & drinks', cueId: 'subject_food' },
      { id: 'nature', label: 'Greenery & nature', cueId: 'setting_nature' },
    ],
  },
};

export default function SentenceMode({
  onBackToCards,
  onSubmitSentence,
  isLoading = false,
}: SentenceModeProps) {
  const [selectedBlanks, setSelectedBlanks] = useState<Record<string, BlankOption>>({});
  const [activePickerKey, setActivePickerKey] = useState<string | null>(null);

  const handleSelectOption = (key: string, option: BlankOption) => {
    setSelectedBlanks((prev) => ({ ...prev, [key]: option }));
    setActivePickerKey(null);
  };

  const handleClearBlank = (key: string) => {
    setSelectedBlanks((prev) => {
      const copy = { ...prev };
      delete copy[key];
      return copy;
    });
  };

  const handleConfirm = () => {
    const blankCues: Record<string, string> = {};
    for (const [key, opt] of Object.entries(selectedBlanks)) {
      blankCues[key] = opt.cueId;
    }
    onSubmitSentence(blankCues);
  };

  const filledCount = Object.keys(selectedBlanks).length;

  return (
    <div className="w-full max-w-lg mx-auto px-4 py-4 sm:py-6">
      {/* Top back navigation */}
      <div className="mb-4">
        <button
          type="button"
          onClick={onBackToCards}
          className="inline-flex items-center gap-1.5 text-[14px] text-textSecondary hover:text-textPrimary transition cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to cue cards</span>
        </button>
      </div>

      {/* Header per Section 19 */}
      <div className="mb-8">
        <h2 className="text-[26px] sm:text-[28px] font-semibold text-textPrimary tracking-tight leading-[32px] mb-1.5">
          Fill in what you recall
        </h2>
        <p className="text-textSecondary text-[15px] leading-[22px]">
          Tap each blank to describe the memory. Skip what you aren’t sure of.
        </p>
      </div>

      {/* Editorial Sentence Layout per pdesign.md Section 19 */}
      <div className="bg-surface rounded-card p-6 border border-borderSubtle shadow-card text-[20px] sm:text-[22px] leading-[38px] text-textPrimary font-normal mb-8">
        <span>It was </span>
        {selectedBlanks.time ? (
          <span className="inline-flex items-center gap-1 bg-brand-soft text-brand font-medium px-2.5 py-0.5 rounded-full text-[17px] border border-brand/20 my-1">
            <span>{selectedBlanks.time.label}</span>
            <button
              type="button"
              onClick={() => handleClearBlank('time')}
              className="hover:text-textPrimary"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setActivePickerKey('time')}
            className="border-b-2 border-dashed border-textTertiary text-brand font-medium px-1.5 hover:border-brand transition cursor-pointer"
          >
            [ time of day ]
          </button>
        )}

        <span>, </span>
        <br className="hidden sm:inline" />

        {selectedBlanks.setting ? (
          <span className="inline-flex items-center gap-1 bg-brand-soft text-brand font-medium px-2.5 py-0.5 rounded-full text-[17px] border border-brand/20 my-1">
            <span>{selectedBlanks.setting.label}</span>
            <button
              type="button"
              onClick={() => handleClearBlank('setting')}
              className="hover:text-textPrimary"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setActivePickerKey('setting')}
            className="border-b-2 border-dashed border-textTertiary text-brand font-medium px-1.5 hover:border-brand transition cursor-pointer"
          >
            [ setting ]
          </button>
        )}

        <span>, with </span>

        {selectedBlanks.people ? (
          <span className="inline-flex items-center gap-1 bg-brand-soft text-brand font-medium px-2.5 py-0.5 rounded-full text-[17px] border border-brand/20 my-1">
            <span>{selectedBlanks.people.label}</span>
            <button
              type="button"
              onClick={() => handleClearBlank('people')}
              className="hover:text-textPrimary"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setActivePickerKey('people')}
            className="border-b-2 border-dashed border-textTertiary text-brand font-medium px-1.5 hover:border-brand transition cursor-pointer"
          >
            [ 3–5 people ]
          </button>
        )}

        <span>, </span>
        <br className="hidden sm:inline" />

        <span>and </span>

        {selectedBlanks.look ? (
          <span className="inline-flex items-center gap-1 bg-brand-soft text-brand font-medium px-2.5 py-0.5 rounded-full text-[17px] border border-brand/20 my-1">
            <span>{selectedBlanks.look.label}</span>
            <button
              type="button"
              onClick={() => handleClearBlank('look')}
              className="hover:text-textPrimary"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setActivePickerKey('look')}
            className="border-b-2 border-dashed border-textTertiary text-brand font-medium px-1.5 hover:border-brand transition cursor-pointer"
          >
            [ what stood out ]
          </button>
        )}

        <span>.</span>
      </div>

      {/* Primary Submit Button */}
      {filledCount > 0 ? (
        <button
          type="button"
          disabled={isLoading}
          onClick={handleConfirm}
          className="w-full py-3.5 px-6 rounded-full font-semibold text-[15px] bg-brand hover:bg-blue-600 text-white shadow-sheet flex items-center justify-center gap-2 cursor-pointer transition-all"
        >
          <span>Show me photos ({filledCount} clue{filledCount > 1 ? 's' : ''})</span>
        </button>
      ) : (
        <p className="text-center text-[14px] text-textTertiary">
          Tap any of the blanks above to begin.
        </p>
      )}

      {/* Blank Option Picker Bottom Sheet */}
      {activePickerKey && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-end sm:items-center justify-center">
          <div className="w-full max-w-lg bg-surface rounded-t-sheet sm:rounded-card p-6 shadow-sheet animate-in slide-in-from-bottom duration-200 border-t sm:border border-borderSubtle">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-borderSubtle">
              <h4 className="font-semibold text-[18px] text-textPrimary">
                Choose {BLANK_DEFINITIONS[activePickerKey].label}
              </h4>
              <button
                type="button"
                onClick={() => setActivePickerKey(null)}
                className="p-1 rounded-full text-textTertiary hover:text-textPrimary"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 py-2">
              {BLANK_DEFINITIONS[activePickerKey].options.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => handleSelectOption(activePickerKey, opt)}
                  className="text-left p-3.5 rounded-[16px] bg-surfaceMuted hover:bg-brand-soft hover:border-brand/40 text-textPrimary border border-borderSubtle font-medium text-[15px] transition cursor-pointer"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
