'use client';

import React from 'react';
import { CueCardItem } from '../lib/types';
import { Check } from 'lucide-react';

interface CueCardProps {
  card: CueCardItem;
  isSelected: boolean;
  onToggle: (cueId: string) => void;
}

export default function CueCard({ card, isSelected, onToggle }: CueCardProps) {
  const { cue_id, label, preview_photo_ids, palette } = card;

  return (
    <div
      onClick={() => onToggle(cue_id)}
      className={`cursor-pointer rounded-card p-4 transition-all duration-150 select-none flex flex-col justify-between ${
        isSelected
          ? 'bg-brand-soft border-2 border-brand shadow-card scale-[0.99]'
          : 'bg-surface border border-borderSubtle shadow-card hover:border-slate-400'
      }`}
    >
      <div>
        {/* Layer 1 & 4: Label and Selection Checkmark */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <h3 className="font-semibold text-[16px] text-textPrimary leading-snug line-clamp-2">
            {label}
          </h3>
          <div
            className={`w-6 h-6 rounded-full shrink-0 flex items-center justify-center transition-colors ${
              isSelected
                ? 'bg-brand text-white font-bold'
                : 'border border-borderSubtle bg-canvas'
            }`}
          >
            {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
          </div>
        </div>

        {/* Layer 2: Color Evidence (Three Tiny Swatches) */}
        <div className="flex items-center gap-1.5 mb-3.5">
          {palette.slice(0, 3).map((hex, i) => (
            <span
              key={i}
              className="w-3 h-3 rounded-full border border-black/10 inline-block shadow-xs"
              style={{ backgroundColor: hex }}
              title={hex}
            />
          ))}
        </div>
      </div>

      {/* Layer 3: Recognition Evidence (3 Thumbnails Strip) */}
      <div className="grid grid-cols-3 gap-1.5 rounded-tile overflow-hidden bg-surfaceMuted p-1">
        {preview_photo_ids.slice(0, 3).map((pid) => (
          <div key={pid} className="aspect-square rounded-md overflow-hidden bg-surfaceMuted">
            <img
              src={`/thumbs/${pid}_256.webp`}
              alt="Recognition clue preview"
              className="w-full h-full object-cover"
              loading="lazy"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
