'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { trackEvent } from './telemetry';

interface UseScrollNudgeOptions {
  isViewerOpen?: boolean;
  hasFoundRecently?: boolean; // Within 60s
  enabled?: boolean;
}

export function useScrollNudge({
  isViewerOpen = false,
  hasFoundRecently = false,
  enabled = true,
}: UseScrollNudgeOptions = {}) {
  const [showNudge, setShowNudge] = useState(false);

  // Session guard: max 1 nudge per session
  const shownInSessionRef = useRef(false);

  // Continuous scrolling tracking
  const lastScrollTimeRef = useRef<number>(0);
  const continuousScrollStartRef = useRef<number | null>(null);
  const totalScrolledRowsRef = useRef<number>(0);
  const directionReversalsRef = useRef<number>(0);
  const lastDirectionRef = useRef<'down' | 'up' | null>(null);
  const lastScrollYRef = useRef<number>(0);

  // Check persistent suppression (3 dismissals in 14 days -> 30 days suppression)
  const isSuppressed = useCallback((): boolean => {
    try {
      const dismissalsJson = localStorage.getItem('mb_nudge_dismissals');
      if (!dismissalsJson) return false;

      const dismissals: number[] = JSON.parse(dismissalsJson);
      const now = Date.now();
      const fourteenDaysAgo = now - 14 * 24 * 60 * 60 * 1000;
      const recentDismissals = dismissals.filter((ts) => ts > fourteenDaysAgo);

      if (recentDismissals.length >= 3) {
        // Suppress until 30 days after the 3rd dismissal
        const lastDismiss = Math.max(...recentDismissals);
        const thirtyDaysAfter = lastDismiss + 30 * 24 * 60 * 60 * 1000;
        if (now < thirtyDaysAfter) {
          return true;
        }
      }
      return false;
    } catch {
      return false;
    }
  }, []);

  const handleDismiss = useCallback(() => {
    setShowNudge(false);
    trackEvent('nudge_dismissed');

    try {
      const dismissalsJson = localStorage.getItem('mb_nudge_dismissals');
      const dismissals: number[] = dismissalsJson ? JSON.parse(dismissalsJson) : [];
      dismissals.push(Date.now());
      localStorage.setItem('mb_nudge_dismissals', JSON.stringify(dismissals));
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const handleAccept = useCallback(() => {
    setShowNudge(false);
    trackEvent('nudge_accepted');
  }, []);

  const onScroll = useCallback(() => {
    if (!enabled || isViewerOpen || hasFoundRecently || shownInSessionRef.current) {
      return;
    }

    if (isSuppressed()) {
      trackEvent('nudge_suppressed');
      return;
    }

    const now = Date.now();
    const currentY = window.scrollY || document.documentElement.scrollTop;
    const deltaY = currentY - lastScrollYRef.current;

    // Check gap < 800ms for continuous scrolling
    if (now - lastScrollTimeRef.current < 800) {
      if (!continuousScrollStartRef.current) {
        continuousScrollStartRef.current = lastScrollTimeRef.current;
      }
    } else {
      // Broken gap: reset continuous accumulator
      continuousScrollStartRef.current = now;
      directionReversalsRef.current = 0;
      totalScrolledRowsRef.current = 0;
    }

    // Direction reversal detection
    if (Math.abs(deltaY) > 10) {
      const currentDir: 'down' | 'up' = deltaY > 0 ? 'down' : 'up';
      if (lastDirectionRef.current && lastDirectionRef.current !== currentDir) {
        directionReversalsRef.current += 1;
      }
      lastDirectionRef.current = currentDir;
      // Approximate 1 row ≈ 120px
      totalScrolledRowsRef.current += Math.abs(deltaY) / 120;
    }

    lastScrollTimeRef.current = now;
    lastScrollYRef.current = currentY;

    // Trigger evaluation: continuous scrolling >= 10s
    const continuousMs = continuousScrollStartRef.current ? now - continuousScrollStartRef.current : 0;
    const isContinuousEnough = continuousMs >= 10000;

    // At least one hunting signal:
    // 1) >= 3 reversals OR 2) >= 40 rows scrolled
    const hasHuntingSignal =
      directionReversalsRef.current >= 3 || totalScrolledRowsRef.current >= 40;

    if (isContinuousEnough && hasHuntingSignal) {
      shownInSessionRef.current = true;
      setShowNudge(true);
      trackEvent('nudge_shown', {
        continuous_seconds: Math.round(continuousMs / 1000),
        reversals: directionReversalsRef.current,
        rows_scrolled: Math.round(totalScrolledRowsRef.current),
      });
    }
  }, [enabled, isViewerOpen, hasFoundRecently, isSuppressed]);

  useEffect(() => {
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [onScroll]);

  return {
    showNudge,
    handleDismiss,
    handleAccept,
  };
}
