'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { trackEvent } from './telemetry';

export type NudgeStage = 'initial' | 'scrolling_detected';

interface UseScrollNudgeOptions {
  isViewerOpen?: boolean;
  hasFoundRecently?: boolean;
  enabled?: boolean;
}

export function useScrollNudge({
  isViewerOpen = false,
  hasFoundRecently = false,
  enabled = true,
}: UseScrollNudgeOptions = {}) {
  const [showNudge, setShowNudge] = useState(false);
  const [nudgeStage, setNudgeStage] = useState<NudgeStage>('initial');

  // Track session dismissal
  const dismissedInSessionRef = useRef(false);

  // Scroll timing trackers
  const scrollStartRef = useRef<number | null>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hasTriggeredScrollingRef = useRef(false);

  // Show initial nudge after initial page load (e.g. 1000ms)
  useEffect(() => {
    if (!enabled || isViewerOpen || hasFoundRecently || dismissedInSessionRef.current) {
      return;
    }

    const timer = setTimeout(() => {
      if (!dismissedInSessionRef.current && !hasTriggeredScrollingRef.current) {
        setShowNudge(true);
        setNudgeStage('initial');
        trackEvent('nudge_initial_shown');
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [enabled, isViewerOpen, hasFoundRecently]);

  const handleDismiss = useCallback(() => {
    setShowNudge(false);
    dismissedInSessionRef.current = true;
    trackEvent('nudge_dismissed', { stage: nudgeStage });
  }, [nudgeStage]);

  const handleAccept = useCallback(() => {
    setShowNudge(false);
    dismissedInSessionRef.current = true;
    trackEvent('nudge_accepted', { stage: nudgeStage });
  }, [nudgeStage]);

  // Handle scroll events: after 1-2 seconds of scrolling, transition to "scrolling_detected"
  const onScroll = useCallback(() => {
    if (!enabled || isViewerOpen || hasFoundRecently || dismissedInSessionRef.current) {
      return;
    }

    const now = Date.now();

    // Start timer for continuous scrolling
    if (scrollStartRef.current === null) {
      scrollStartRef.current = now;
    }

    const scrollElapsed = now - scrollStartRef.current;

    // After 1.2 to 2 seconds of scrolling activity, switch to "scrolling_detected"
    if (scrollElapsed >= 1200 && !hasTriggeredScrollingRef.current) {
      hasTriggeredScrollingRef.current = true;
      setNudgeStage('scrolling_detected');
      setShowNudge(true);
      trackEvent('nudge_scrolling_detected_shown', { scroll_ms: scrollElapsed });
    }

    // Reset scroll start when user stops scrolling for > 1500ms
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    scrollTimeoutRef.current = setTimeout(() => {
      scrollStartRef.current = null;
    }, 1500);
  }, [enabled, isViewerOpen, hasFoundRecently]);

  useEffect(() => {
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [onScroll]);

  return {
    showNudge,
    nudgeStage,
    handleDismiss,
    handleAccept,
  };
}
