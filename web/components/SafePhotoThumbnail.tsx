/* eslint-disable @next/next/no-img-element */
'use client';

import React, { useState, useEffect } from 'react';
import { Image as ImageIcon } from 'lucide-react';

interface SafePhotoThumbnailProps {
  src: string;
  alt?: string;
  photoId?: string;
  palette?: string[];
  className?: string;
  loading?: 'lazy' | 'eager';
  aspectRatio?: 'square' | 'contain' | 'auto';
  onClick?: () => void;
}

export default function SafePhotoThumbnail({
  src,
  alt = '',
  photoId,
  palette,
  className = '',
  loading = 'lazy',
  aspectRatio = 'square',
  onClick,
}: SafePhotoThumbnailProps) {
  const [currentSrc, setCurrentSrc] = useState<string>(src);
  const [stage, setStage] = useState<'primary' | 'direct' | 'api' | 'raw' | 'svg'>('primary');
  const [isLoaded, setIsLoaded] = useState(false);

  // Reset when source changes
  useEffect(() => {
    setCurrentSrc(src);
    setStage('primary');
    setIsLoaded(false);
  }, [src, photoId]);

  const handleError = () => {
    const pid = photoId || extractPhotoId(currentSrc);

    if (stage === 'primary') {
      // Step 2: Try direct Uvicorn IPv4 port
      setStage('direct');
      if (src.startsWith('/')) {
        setCurrentSrc(`http://127.0.0.1:8000${src}`);
      } else {
        setStage('api');
        setCurrentSrc(`/api/photos/${pid}/thumb?size=256`);
      }
    } else if (stage === 'direct') {
      // Step 3: Try API on-the-fly thumb generator
      setStage('api');
      setCurrentSrc(`/api/photos/${pid}/thumb?size=256`);
    } else if (stage === 'api') {
      // Step 4: Try raw photo stream
      setStage('raw');
      setCurrentSrc(`/api/photos/${pid}/raw`);
    } else {
      // Step 5: Final SVG / CSS gradient fallback
      setStage('svg');
    }
  };

  function extractPhotoId(url: string): string {
    const match = url.match(/([a-f0-9]{16})/i);
    return match ? match[1] : 'photo';
  }

  // Generate pleasant CSS gradient from palette or neutrals
  const colors = palette && palette.length >= 2 ? palette : ['#334155', '#475569', '#64748b'];
  const gradientStyle = {
    background: `linear-gradient(135deg, ${colors[0]} 0%, ${colors[1]} 50%, ${colors[2] || colors[0]} 100%)`,
  };

  if (stage === 'svg') {
    return (
      <div
        onClick={onClick}
        style={gradientStyle}
        className={`w-full h-full flex flex-col items-center justify-center p-2 text-white/90 select-none ${className}`}
      >
        <div className="w-8 h-8 rounded-full bg-white/15 flex items-center justify-center mb-1 backdrop-blur-xs">
          <ImageIcon className="w-4 h-4 text-white" />
        </div>
        <span className="text-[10px] font-medium tracking-wide opacity-80 uppercase">
          Memory
        </span>
      </div>
    );
  }

  return (
    <div className={`relative w-full h-full overflow-hidden ${className}`}>
      {/* Background skeleton/gradient while loading */}
      {!isLoaded && (
        <div
          style={gradientStyle}
          className="absolute inset-0 animate-pulse opacity-40"
        />
      )}
      <img
        src={currentSrc}
        alt={alt}
        loading={loading}
        onLoad={() => setIsLoaded(true)}
        onError={handleError}
        onClick={onClick}
        className={`w-full h-full ${
          aspectRatio === 'contain' ? 'object-contain' : 'object-cover'
        } transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
      />
    </div>
  );
}
