'use client';

import React, { useState } from 'react';
import { PhotoItem } from '../lib/types';
import { ArrowLeft, Check, Share2, PlusSquare, CheckCheck } from 'lucide-react';

interface FoundViewProps {
  photo: PhotoItem;
  otherPhotos?: PhotoItem[];
  onBackToTimeline: () => void;
  onSelectOtherPhoto?: (photo: PhotoItem) => void;
}

export default function FoundView({
  photo,
  otherPhotos = [],
  onBackToTimeline,
  onSelectOtherPhoto,
}: FoundViewProps) {
  const [copiedShare, setCopiedShare] = useState(false);
  const [albumSaved, setAlbumSaved] = useState(false);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Memory Found',
          text: 'Found this photo with Memory Board!',
          url: window.location.href,
        });
      } catch {
        // Fallback to clipboard
        navigator.clipboard.writeText(window.location.href);
        setCopiedShare(true);
        setTimeout(() => setCopiedShare(false), 2000);
      }
    } else {
      navigator.clipboard.writeText(window.location.href);
      setCopiedShare(true);
      setTimeout(() => setCopiedShare(false), 2000);
    }
  };

  const handleAddToAlbum = () => {
    setAlbumSaved(true);
    setTimeout(() => setAlbumSaved(false), 2500);
  };

  return (
    <div className="w-full max-w-lg mx-auto px-4 py-4 sm:py-6 animate-in fade-in duration-300">
      {/* Top Header per pdesign.md Section 22 */}
      <div className="flex items-center justify-between mb-4">
        <button
          type="button"
          onClick={onBackToTimeline}
          className="inline-flex items-center gap-1.5 text-[14px] text-textSecondary hover:text-textPrimary transition cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Photos</span>
        </button>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold bg-success-soft text-success border border-success/20">
          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Found it</span>
        </div>
      </div>

      {/* Hero Photo Display per Section 22 (object-fit: contain) */}
      <div className="w-full aspect-[4/3] rounded-card overflow-hidden bg-black/5 border border-borderSubtle mb-4 flex items-center justify-center shadow-card">
        <img
          src={`/thumbs/${photo.id}_1024.webp`}
          alt="Found target photo"
          className="w-full h-full object-contain"
        />
      </div>

      {/* Supporting text */}
      <div className="text-center mb-6">
        <p className="text-[17px] font-semibold text-textPrimary">
          You found the photo.
        </p>
        {photo.taken_at && (
          <p className="text-[13px] text-textTertiary mt-0.5">
            {photo.taken_at.slice(0, 10)}
          </p>
        )}
      </div>

      {/* Primary Actions per Section 22 */}
      <div className="grid grid-cols-3 gap-2.5 mb-8">
        <button
          type="button"
          onClick={handleShare}
          className="py-3 px-2 rounded-full font-medium text-[14px] bg-brand text-white hover:bg-blue-600 transition flex items-center justify-center gap-1.5 cursor-pointer shadow-sm"
        >
          {copiedShare ? (
            <>
              <CheckCheck className="w-4 h-4" />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Share2 className="w-4 h-4" />
              <span>Share</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={handleAddToAlbum}
          className="py-3 px-2 rounded-full font-medium text-[14px] bg-surfaceMuted text-textPrimary hover:bg-borderSubtle transition flex items-center justify-center gap-1.5 cursor-pointer border border-borderSubtle"
        >
          {albumSaved ? (
            <>
              <Check className="w-4 h-4 text-success" />
              <span>Added</span>
            </>
          ) : (
            <>
              <PlusSquare className="w-4 h-4" />
              <span>Album</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onBackToTimeline}
          className="py-3 px-2 rounded-full font-medium text-[14px] bg-surfaceMuted text-textSecondary hover:text-textPrimary hover:bg-borderSubtle transition flex items-center justify-center cursor-pointer border border-borderSubtle"
        >
          Done
        </button>
      </div>

      {/* Other Photos Strip per Section 22 */}
      {otherPhotos.length > 0 && (
        <div>
          <p className="text-[13px] font-medium text-textSecondary mb-2.5">
            Other photos from this group
          </p>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {otherPhotos.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelectOtherPhoto && onSelectOtherPhoto(p)}
                className={`shrink-0 w-16 h-16 rounded-tile overflow-hidden border transition cursor-pointer ${
                  p.id === photo.id
                    ? 'border-brand ring-2 ring-brand/30'
                    : 'border-borderSubtle opacity-75 hover:opacity-100'
                }`}
              >
                <img
                  src={p.thumb_256}
                  alt="Related thumbnail"
                  className="w-full h-full object-cover"
                />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
