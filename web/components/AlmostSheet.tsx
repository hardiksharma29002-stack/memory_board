'use client';

import React from 'react';
import SafePhotoThumbnail from './SafePhotoThumbnail';
import { X, Clock, Users, MapPin, Palette, HelpCircle } from 'lucide-react';

interface AlmostSheetProps {
  photoId: string;
  onClose: () => void;
  onSelectAxis: (photoId: string, axis: string) => void;
  isLoading?: boolean;
}

export default function AlmostSheet({
  photoId,
  onClose,
  onSelectAxis,
  isLoading = false,
}: AlmostSheetProps) {
  const options = [
    { id: 'diff_place', label: 'Different place', icon: MapPin },
    { id: 'diff_time', label: 'Different time of day', icon: Clock },
    { id: 'diff_people', label: 'Different people', icon: Users },
    { id: 'diff_look', label: 'Different look', icon: Palette },
    { id: 'cant_say', label: 'Can’t say', icon: HelpCircle },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-end sm:items-center justify-center">
      <div className="w-full max-w-lg bg-surface rounded-t-sheet sm:rounded-card p-6 shadow-sheet animate-in slide-in-from-bottom duration-200 border-t sm:border border-borderSubtle">
        {/* Drag handle per pdesign.md Section 24 */}
        <div className="w-12 h-1 bg-borderSubtle rounded-full mx-auto mb-4 sm:hidden" />

        {/* Header per Section 20 */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-borderSubtle">
          <h3 className="font-semibold text-[20px] text-textPrimary leading-tight">
            What&apos;s different?
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-full text-textTertiary hover:text-textPrimary hover:bg-surfaceMuted transition cursor-pointer"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Reference Thumbnail Context */}
        <div className="flex items-center gap-3 p-2.5 rounded-tile bg-surfaceMuted mb-4">
          <div className="w-12 h-12 rounded-md overflow-hidden shrink-0 bg-surface">
            <SafePhotoThumbnail
              src={`/thumbs/${photoId}_256.webp`}
              photoId={photoId}
              alt="Reference anchor photo"
              className="w-full h-full object-cover"
            />
          </div>
          <p className="text-[13px] text-textSecondary leading-snug">
            Choose what differed so we can adjust the search.
          </p>
        </div>

        {/* 5 Options per Section 20 */}
        <div className="space-y-2 mb-2">
          {options.map((opt) => {
            const Icon = opt.icon;
            return (
              <button
                key={opt.id}
                type="button"
                disabled={isLoading}
                onClick={() => onSelectAxis(photoId, opt.id)}
                className="w-full text-left p-3.5 rounded-[16px] bg-surface hover:bg-brand-soft border border-borderSubtle hover:border-brand/40 flex items-center gap-3 transition cursor-pointer"
              >
                <Icon className="w-4 h-4 text-brand shrink-0" />
                <span className="font-medium text-[15px] text-textPrimary">
                  {opt.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
