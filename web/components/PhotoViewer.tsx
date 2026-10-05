'use client';

import React, { useEffect } from 'react';
import { PhotoItem } from '../lib/types';
import SafePhotoThumbnail from './SafePhotoThumbnail';
import { X, Check, Calendar, Camera, Trash2 } from 'lucide-react';

interface PhotoViewerProps {
  photo: PhotoItem | null;
  onClose: () => void;
  onFound: (photoId: string) => void;
  onAlmost: (photoId: string) => void;
  onDelete?: (photoId: string) => void;
}

export default function PhotoViewer({ photo, onClose, onFound, onAlmost, onDelete }: PhotoViewerProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!photo) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-2 sm:p-6 animate-in fade-in duration-150">
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col rounded-card overflow-hidden bg-surface shadow-2xl border border-borderSubtle">
        {/* Top Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-borderSubtle bg-surface z-10">
          <div className="flex items-center gap-3">
            {photo.taken_at && (
              <span className="flex items-center gap-1.5 text-[13px] text-textSecondary font-medium">
                <Calendar className="w-3.5 h-3.5 text-textTertiary" />
                {new Date(photo.taken_at).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </span>
            )}
            {photo.source && (
              <span className="flex items-center gap-1 text-[13px] text-textTertiary capitalize">
                <Camera className="w-3.5 h-3.5 text-textTertiary" />
                {photo.source}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {onDelete && (
              <button
                type="button"
                onClick={() => {
                  onDelete(photo.id);
                  onClose();
                }}
                className="p-1.5 rounded-full text-rose-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition cursor-pointer"
                title="Delete this photo"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-full text-textTertiary hover:text-textPrimary hover:bg-surfaceMuted transition cursor-pointer"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Photo Container */}
        <div className="flex-1 min-h-[300px] max-h-[66vh] flex items-center justify-center bg-black/90 overflow-hidden p-2">
          <SafePhotoThumbnail
            src={photo.thumb_1024 || photo.thumb_256}
            photoId={photo.id}
            palette={photo.palette ? (() => { try { return JSON.parse(photo.palette); } catch { return undefined; } })() : undefined}
            alt="Full photo view"
            aspectRatio="contain"
            className="max-h-[66vh] max-w-full"
          />
        </div>

        {/* Bottom Actions Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-borderSubtle bg-surface gap-3">
          <button
            type="button"
            onClick={() => {
              onAlmost(photo.id);
              onClose();
            }}
            className="px-4 py-2 rounded-full text-[14px] font-medium text-textPrimary bg-surfaceMuted hover:bg-borderSubtle transition cursor-pointer"
          >
            Almost!
          </button>

          <button
            type="button"
            onClick={() => {
              onFound(photo.id);
              onClose();
            }}
            className="px-5 py-2 rounded-full text-[14px] font-semibold text-white bg-success hover:opacity-90 flex items-center gap-1.5 transition cursor-pointer shadow-sm"
          >
            <Check className="w-4 h-4" />
            <span>Found it</span>
          </button>
        </div>
      </div>
    </div>
  );
}
