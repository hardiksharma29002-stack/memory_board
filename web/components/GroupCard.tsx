'use client';

import React from 'react';
import { GroupCardItem, PhotoItem } from '../lib/types';
import BandBadge from './BandBadge';
import { Check, Sparkles } from 'lucide-react';

interface GroupCardProps {
  group: GroupCardItem;
  rank?: number;
  onPhotoClick: (photo: PhotoItem) => void;
  onFound: (photoId: string) => void;
  onAlmost: (photoId: string) => void;
  onNotHere?: () => void;
}

export default function GroupCard({
  group,
  rank = 1,
  onPhotoClick,
  onFound,
  onAlmost,
  onNotHere,
}: GroupCardProps) {
  const { id, label, confidence, why_chips, photos, photo_count } = group;

  return (
    <div
      aria-labelledby={`album-title-${id}`}
      className="bg-surface rounded-2xl p-4 sm:p-5 mb-5 border border-borderSubtle shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition"
    >
      {/* 1. Simple Header: Album Rank & Name */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-textSecondary uppercase tracking-wider">
            Album {rank} of 4
          </span>
          <BandBadge confidence={confidence} />
        </div>
        <span className="text-xs text-textSecondary">
          {photo_count || photos.length} photos
        </span>
      </div>

      <h3
        id={`album-title-${id}`}
        className="text-lg sm:text-xl font-bold text-textPrimary leading-snug mb-1"
      >
        {label}
      </h3>
      <p className="text-[11px] text-textSecondary mb-2 font-medium">
        Higher confidence score = more likely to find your image in this album
      </p>

      {/* 2. Compact Matching Clues */}
      {why_chips.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap mb-3.5">
          {why_chips.map((chip, idx) => (
            <span
              key={idx}
              className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-surfaceMuted text-textSecondary border border-borderSubtle flex items-center gap-1"
            >
              <Sparkles className="w-2.5 h-2.5 text-brand" />
              <span>{chip}</span>
            </span>
          ))}
        </div>
      )}

      {/* 3. Photo Strip */}
      <div className="flex gap-2 overflow-x-auto pb-2 pt-1 scroll-smooth snap-x mb-3.5 focus:outline-none">
        {photos.map((photo, idx) => (
          <div
            key={photo.id}
            role="button"
            tabIndex={0}
            aria-label={`Photo ${idx + 1}. Click to enlarge.`}
            onClick={() => onPhotoClick(photo)}
            className="group/photo relative shrink-0 w-24 sm:w-28 aspect-square rounded-xl overflow-hidden bg-surfaceMuted border border-borderSubtle hover:border-brand cursor-pointer snap-start transition"
          >
            <img
              src={photo.thumb_256}
              alt=""
              className="w-full h-full object-cover group-hover/photo:scale-105 transition-transform"
              loading="lazy"
            />
            {/* Minimal quick tap overlay */}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/photo:opacity-100 transition-opacity flex items-center justify-center p-1.5">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onFound(photo.id);
                }}
                className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-600 text-white shadow-xs"
              >
                Found it
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 4. Minimal Footer Actions */}
      <div className="flex items-center justify-between pt-2.5 border-t border-borderSubtle">
        <div className="flex items-center gap-2">
          {photos[0] && (
            <button
              type="button"
              onClick={() => onFound(photos[0].id)}
              className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white transition flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Found in this Album</span>
            </button>
          )}

          {photos[0] && (
            <button
              type="button"
              onClick={() => onAlmost(photos[0].id)}
              className="px-3 py-1.5 rounded-xl text-xs font-medium text-textSecondary hover:bg-surfaceMuted transition"
            >
              Almost
            </button>
          )}
        </div>

        {onNotHere && (
          <button
            type="button"
            onClick={onNotHere}
            className="text-xs text-textSecondary hover:text-rose-600 dark:hover:text-rose-400 font-medium py-1 px-2.5 rounded-lg hover:bg-surfaceMuted transition"
          >
            Not here
          </button>
        )}
      </div>
    </div>
  );
}
