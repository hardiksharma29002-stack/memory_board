'use client';

import React from 'react';
import { CognitiveCardItem, CognitiveOptionItem } from '../lib/types';
import {
  Sun,
  Moon,
  Users,
  User,
  MapPin,
  Coffee,
  Sparkles,
  Palette,
  Home,
  Check,
  Compass,
} from 'lucide-react';

interface CognitiveCueCardProps {
  card: CognitiveCardItem;
  selectedOptionIds: string[];
  onToggleOption: (optionId: string) => void;
}

export default function CognitiveCueCard({
  card,
  selectedOptionIds,
  onToggleOption,
}: CognitiveCueCardProps) {
  const { id, title, options } = card;

  // Small, subtle icons (14px)
  const renderIcon = (iconName?: string) => {
    switch (iconName) {
      case 'sun':
      case 'sunset':
        return <Sun className="w-3.5 h-3.5 text-amber-500 shrink-0" aria-hidden="true" />;
      case 'moon':
        return <Moon className="w-3.5 h-3.5 text-indigo-400 shrink-0" aria-hidden="true" />;
      case 'sparkles':
        return <Sparkles className="w-3.5 h-3.5 text-pink-500 shrink-0" aria-hidden="true" />;
      case 'user':
        return <User className="w-3.5 h-3.5 text-sky-500 shrink-0" aria-hidden="true" />;
      case 'users':
        return <Users className="w-3.5 h-3.5 text-emerald-500 shrink-0" aria-hidden="true" />;
      case 'coffee':
        return <Coffee className="w-3.5 h-3.5 text-amber-600 shrink-0" aria-hidden="true" />;
      case 'home':
        return <Home className="w-3.5 h-3.5 text-blue-500 shrink-0" aria-hidden="true" />;
      case 'compass':
        return <Compass className="w-3.5 h-3.5 text-teal-500 shrink-0" aria-hidden="true" />;
      case 'palette':
        return <Palette className="w-3.5 h-3.5 text-rose-500 shrink-0" aria-hidden="true" />;
      default:
        return <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" aria-hidden="true" />;
    }
  };

  return (
    <div
      aria-labelledby={`card-title-${id}`}
      className="bg-surface rounded-xl border border-borderSubtle p-3.5 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition"
    >
      <div className="mb-2.5">
        <h3
          id={`card-title-${id}`}
          className="text-xs font-bold uppercase tracking-wider text-textSecondary"
        >
          {title}
        </h3>
      </div>

      {/* Compact option pills */}
      <div role="group" aria-label={title} className="flex flex-wrap gap-1.5">
        {options.map((opt: CognitiveOptionItem) => {
          const isSelected = selectedOptionIds.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              role="checkbox"
              aria-checked={isSelected}
              onClick={() => onToggleOption(opt.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 cursor-pointer ${
                isSelected
                  ? 'bg-brand text-white shadow-xs font-semibold'
                  : 'bg-canvas dark:bg-slate-900 text-textPrimary border border-borderSubtle hover:border-slate-400'
              }`}
            >
              {renderIcon(opt.icon)}
              <span>{opt.label}</span>
              {isSelected && <Check className="w-3 h-3 stroke-[3] ml-0.5" />}
            </button>
          );
        })}
      </div>
    </div>
  );
}
