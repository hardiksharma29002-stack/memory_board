'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  UploadCloud,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  RotateCcw,
  Smartphone,
} from 'lucide-react';
import { uploadPhotos, resetSamplePhotos, fetchPhotoStats } from '../lib/api';

interface PhotoUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export default function PhotoUploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
}: PhotoUploadModalProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stats, setStats] = useState<{
    total_photos: number;
    cap: number;
    available_slots: number;
    has_sample_backup: boolean;
  }>({ total_photos: 413, cap: 500, available_slots: 87, has_sample_backup: true });

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      loadStats();
    }
  }, [isOpen]);

  const loadStats = async () => {
    try {
      const data = await fetchPhotoStats();
      setStats({
        total_photos: data.total_photos,
        cap: data.cap,
        available_slots: data.available_slots,
        has_sample_backup: data.has_sample_backup,
      });
    } catch {
      // fallback
    }
  };

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      setSelectedFiles(files);
      setErrorMessage(null);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setErrorMessage('Please select photos from your gallery or computer.');
      return;
    }

    setIsLoading(true);
    setStatusMessage('Uploading and extracting CLIP AI embeddings...');
    setErrorMessage(null);

    try {
      const result = await uploadPhotos(selectedFiles, replaceExisting);
      setStatusMessage(result.message);
      setSelectedFiles([]);
      await loadStats();
      onUploadSuccess();
      setTimeout(() => {
        setIsLoading(false);
        onClose();
      }, 1500);
    } catch (err: unknown) {
      setIsLoading(false);
      const msg = err instanceof Error ? err.message : 'Error uploading photos. Please try again.';
      setErrorMessage(msg);
    }
  };

  const handleResetSample = async () => {
    if (
      !confirm(
        'Reset photo library to default 400 sample photos? Your uploaded photos will be replaced.'
      )
    ) {
      return;
    }

    setIsLoading(true);
    setStatusMessage('Restoring 400 sample photos and regenerating embeddings...');
    setErrorMessage(null);

    try {
      const result = await resetSamplePhotos();
      setStatusMessage(result.message);
      await loadStats();
      onUploadSuccess();
      setTimeout(() => {
        setIsLoading(false);
        onClose();
      }, 1200);
    } catch (err: unknown) {
      setIsLoading(false);
      const msg = err instanceof Error ? err.message : 'Error resetting sample photos.';
      setErrorMessage(msg);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in"
    >
      <div className="bg-surface rounded-2xl w-full max-w-lg p-5 sm:p-6 border border-borderSubtle shadow-2xl relative max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          disabled={isLoading}
          className="absolute top-4 right-4 p-1.5 rounded-full text-textSecondary hover:text-textPrimary hover:bg-surfaceMuted transition cursor-pointer"
          aria-label="Close upload modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2.5 mb-1.5">
          <div className="p-2 rounded-xl bg-brand-soft text-brand">
            <UploadCloud className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-textPrimary">Add Photos to Library</h2>
            <p className="text-xs text-textSecondary">
              Upload personal photos to test real vague memory retrieval
            </p>
          </div>
        </div>

        {/* 📸 User Nudge Banner */}
        <div className="mt-3 mb-4 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-bold">Recommendation:</span> Add ~100 real photos from your
            personal gallery (trips, outings, festive occasions) for the most authentic vague memory
            retrieval experience!
          </div>
        </div>

        {/* Library Capacity Meter (500 Cap) */}
        <div className="mb-4 p-3 rounded-xl bg-surfaceMuted border border-borderSubtle">
          <div className="flex items-center justify-between text-xs font-semibold mb-1.5">
            <span className="text-textSecondary">Library Photo Capacity</span>
            <span className="text-textPrimary">
              {stats.total_photos} / {stats.cap} photos
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                stats.total_photos >= 450 ? 'bg-amber-500' : 'bg-brand'
              }`}
              style={{ width: `${Math.min(100, (stats.total_photos / stats.cap) * 100)}%` }}
            />
          </div>
          <p className="text-[11px] text-textSecondary mt-1.5 flex items-center justify-between">
            <span>Library capacity: {stats.total_photos} photos</span>
            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Auto-expanding (unlimited)</span>
          </p>
        </div>

        {/* Native Mobile Gallery / File Picker Trigger */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          id="gallery-photo-input"
        />

        <div
          role="button"
          tabIndex={0}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          className="border-2 border-dashed border-borderSubtle hover:border-brand rounded-2xl p-6 text-center cursor-pointer transition bg-canvas hover:bg-brand-soft/20 flex flex-col items-center justify-center gap-2 mb-4"
        >
          <div className="p-3 rounded-full bg-surfaceMuted text-brand">
            <Smartphone className="w-6 h-6 sm:hidden" />
            <ImageIcon className="w-6 h-6 hidden sm:block" />
          </div>
          <div className="text-sm font-semibold text-textPrimary">
            <span className="sm:hidden">Tap to Open Mobile Gallery</span>
            <span className="hidden sm:inline">Choose Photos or Drop Here</span>
          </div>
          <p className="text-xs text-textSecondary">
            Directly opens your phone&apos;s photo library (JPG, PNG, WebP)
          </p>
          {selectedFiles.length > 0 && (
            <div className="mt-1 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 text-xs font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{selectedFiles.length} photos selected</span>
            </div>
          )}
        </div>

        {/* Replace / Keep Options */}
        <div className="space-y-2 mb-4">
          <label className="flex items-center gap-2.5 p-2.5 rounded-xl border border-borderSubtle bg-surface hover:bg-surfaceMuted cursor-pointer text-xs font-medium transition">
            <input
              type="checkbox"
              checked={replaceExisting}
              onChange={(e) => setReplaceExisting(e.target.checked)}
              className="w-4 h-4 text-brand rounded-sm focus:ring-brand"
            />
            <span className="text-textPrimary">
              Replace demo photos (Clear existing 400 photos and index only mine)
            </span>
          </label>
        </div>

        {/* Error or Status message */}
        {errorMessage && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {statusMessage && (
          <div className="mb-4 p-3 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Modal Action Buttons */}
        <div className="flex items-center justify-between gap-3 pt-3 border-t border-borderSubtle">
          <button
            type="button"
            onClick={handleResetSample}
            disabled={isLoading}
            className="text-xs font-medium text-textSecondary hover:text-textPrimary flex items-center gap-1 px-2 py-1.5 rounded-lg hover:bg-surfaceMuted transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to 400 Sample Photos</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold text-textSecondary hover:bg-surfaceMuted transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleUpload}
              disabled={isLoading || selectedFiles.length === 0}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand text-white hover:bg-blue-600 disabled:opacity-40 transition flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Indexing...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>Upload & Index</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
