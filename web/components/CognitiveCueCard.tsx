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
  Sunset,
  Trees,
  Waves,
  Gift,
  Flame,
} from 'lucide-react';

interface CognitiveCueCardProps {
  card: CognitiveCardItem;
  cardIndex: number;
  selectedOptionIds: string[];
  onToggleOption: (optionId: string) => void;
}

export default function CognitiveCueCard({
  card,
  cardIndex,
  selectedOptionIds,
  onToggleOption,
}: CognitiveCueCardProps) {
  const { id, title, category, description, options } = card;

  // Icon resolver with prominent, vibrant visuals
  const renderIcon = (iconName?: string) => {
    switch (iconName) {
      case 'sun':
        return <Sun className="w-4 h-4 text-amber-500 shrink-0" aria-hidden="true" />;
      case 'sunset':
        return <Sunset className="w-4 h-4 text-orange-500 shrink-0" aria-hidden="true" />;
      case 'moon':
        return <Moon className="w-4 h-4 text-indigo-400 shrink-0" aria-hidden="true" />;
      case 'sparkles':
        return <Sparkles className="w-4 h-4 text-pink-500 shrink-0" aria-hidden="true" />;
      case 'user':
        return <User className="w-4 h-4 text-sky-500 shrink-0" aria-hidden="true" />;
      case 'users':
        return <Users className="w-4 h-4 text-emerald-500 shrink-0" aria-hidden="true" />;
      case 'coffee':
        return <Coffee className="w-4 h-4 text-amber-700 shrink-0" aria-hidden="true" />;
      case 'home':
        return <Home className="w-4 h-4 text-blue-500 shrink-0" aria-hidden="true" />;
      case 'compass':
        return <Compass className="w-4 h-4 text-teal-500 shrink-0" aria-hidden="true" />;
      case 'palette':
        return <Palette className="w-4 h-4 text-rose-500 shrink-0" aria-hidden="true" />;
      case 'trees':
        return <Trees className="w-4 h-4 text-emerald-600 shrink-0" aria-hidden="true" />;
      case 'waves':
        return <Waves className="w-4 h-4 text-cyan-500 shrink-0" aria-hidden="true" />;
      case 'gift':
        return <Gift className="w-4 h-4 text-purple-500 shrink-0" aria-hidden="true" />;
      case 'flame':
        return <Flame className="w-4 h-4 text-orange-600 shrink-0" aria-hidden="true" />;
      default:
        return <MapPin className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />;
    }
  };

  // Card category theme colors
  const cardThemes = [
    {
      badgeBg: 'bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-200 border-amber-200',
      activeBorder: 'border-amber-400 dark:border-amber-600 ring-2 ring-amber-400/20',
      numBadge: 'bg-amber-500 text-white',
    },
    {
      badgeBg: 'bg-blue-50 dark:bg-blue-950/60 text-blue-800 dark:text-blue-200 border-blue-200',
      activeBorder: 'border-blue-400 dark:border-blue-600 ring-2 ring-blue-400/20',
      numBadge: 'bg-blue-500 text-white',
    },
    {
      badgeBg: 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-200 border-emerald-200',
      activeBorder: 'border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-400/20',
      numBadge: 'bg-emerald-500 text-white',
    },
    {
      badgeBg: 'bg-purple-50 dark:bg-purple-950/60 text-purple-800 dark:text-purple-200 border-purple-200',
      activeBorder: 'border-purple-400 dark:border-purple-600 ring-2 ring-purple-400/20',
      numBadge: 'bg-purple-500 text-white',
    },
  ];

  const theme = cardThemes[cardIndex % cardThemes.length];
  const cardSelectedCount = options.filter((o) => selectedOptionIds.includes(o.id)).length;
  const isCardAnswered = cardSelectedCount > 0;

  return (
    <div
      aria-labelledby={`card-title-${id}`}
      className={`bg-surface rounded-2xl border-2 p-5 flex flex-col justify-between transition-all duration-200 shadow-xs hover:shadow-md ${
        isCardAnswered ? theme.activeBorder : 'border-borderSubtle hover:border-slate-300 dark:hover:border-slate-700'
      }`}
    >
      {/* 1. Header with Number, Category & Status */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${theme.numBadge}`}>
              {cardIndex + 1}
            </span>
            <span className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border ${theme.badgeBg}`}>
              {category || 'Memory Anchor'}
            </span>
          </div>

          {isCardAnswered && (
            <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200 dark:border-emerald-800">
              <Check className="w-3 h-3 stroke-[2.5]" />
              <span>{cardSelectedCount} selected</span>
            </span>
          )}
        </div>

        {/* Title & Prompt Description */}
        <h3
          id={`card-title-${id}`}
          className="text-base font-bold text-textPrimary leading-snug mb-1"
        >
          {title}
        </h3>
        <p className="text-xs text-textSecondary mb-4 leading-relaxed">
          {description || 'Choose any detail that feels familiar:'}
        </p>
      </div>

      {/* 2. Big Touch-Friendly Option Cards */}
      <div role="group" aria-label={title} className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-auto">
        {options.map((opt: CognitiveOptionItem) => {
          const isSelected = selectedOptionIds.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              role="checkbox"
              aria-checked={isSelected}
              onClick={() => onToggleOption(opt.id)}
              className={`p-3 rounded-xl text-xs font-medium text-left transition-all flex items-start gap-2.5 cursor-pointer border ${
                isSelected
                  ? 'bg-brand text-white border-brand shadow-xs font-semibold'
                  : 'bg-canvas dark:bg-slate-900 text-textPrimary border-borderSubtle hover:border-brand/50 hover:bg-surfaceMuted'
              }`}
            >
              <div className={`p-1.5 rounded-lg shrink-0 ${isSelected ? 'bg-white/20 text-white' : 'bg-surfaceMuted'}`}>
                {renderIcon(opt.icon)}
              </div>
              <div className="flex-1 min-w-0">
                <span className="leading-snug block truncate">{opt.label}</span>
              </div>
              {isSelected && <Check className="w-4 h-4 stroke-[3] text-white shrink-0 mt-0.5" />}
            </button>
          );
        })}
      </div>
    </div>
  );
}
