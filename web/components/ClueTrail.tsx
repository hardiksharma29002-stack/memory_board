'use client';

import React from 'react';
import { ClueItem } from '../lib/types';
import { X, Undo2 } from 'lucide-react';

interface ClueTrailProps {
  clues: ClueItem[];
  onRemoveClue: (clueId: string) => void;
  onRewind: () => void;
  canRewind: boolean;
}

export default function ClueTrail({
  clues,
  onRemoveClue,
  onRewind,
  canRewind,
}: ClueTrailProps) {
  if (clues.length === 0) return null;

  return (
    <div className="w-full max-w-lg mx-auto mb-5 px-1 flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-textSecondary">
          You remember:
        </span>

        {canRewind && (
          <button
            type="button"
            onClick={onRewind}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold text-brand bg-brand-soft hover:bg-brand hover:text-white border border-brand/20 transition cursor-pointer shadow-2xs"
            title="Rewind: Undo your last added clue and step back one memory step"
          >
            <Undo2 className="w-3.5 h-3.5" />
            <span>Rewind (Undo Last Clue)</span>
          </button>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {clues.map((clue) => (
          <span
            key={clue.id}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-normal bg-brand-soft text-brand border border-brand/20 transition-all select-none"
          >
            <span>{clue.label}</span>
            <button
              type="button"
              onClick={() => onRemoveClue(clue.id)}
              className="w-4 h-4 rounded-full flex items-center justify-center hover:bg-brand hover:text-white transition cursor-pointer"
              title={`Remove ${clue.label}`}
            >
              <X className="w-3 h-3 stroke-[2.5]" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
