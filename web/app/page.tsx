'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  PhotoItem,
  CueCardItem,
  CognitiveCardItem,
  GroupCardItem,
  QuestionItem,
  ClueItem,
  FollowupProbeItem,
} from '../lib/types';
import {
  fetchPhotos,
  startSearchSession,
  selectCues,
  noneOfThese,
  skipToAlbums,
  answerQuestion,
  removeClue,
  rewindSession,
  almostPivot,
  confirmFound,
  submitSentence,
  triggerFallback,
  addMemoryText,
  fetchPhotoStats,
  fetchSmartCards,
  deletePhoto,
} from '../lib/api';

import CueBoard from '../components/CueBoard';
import SentenceMode from '../components/SentenceMode';
import ClueTrail from '../components/ClueTrail';
import GroupCard from '../components/GroupCard';
import QuestionSheet from '../components/QuestionSheet';
import AlmostSheet from '../components/AlmostSheet';
import FallbackView from '../components/FallbackView';
import FoundView from '../components/FoundView';
import PhotoViewer from '../components/PhotoViewer';
import ScrollNudge from '../components/ScrollNudge';
import PhotoUploadModal from '../components/PhotoUploadModal';
import SafePhotoThumbnail from '../components/SafePhotoThumbnail';
import { useScrollNudge } from '../lib/useScrollNudge';
import { trackEvent } from '../lib/telemetry';

import {
  Search,
  ArrowLeft,
  Moon,
  Sun,
  Sparkles,
  Plus,
  Trash2,
  X,
} from 'lucide-react';

export default function MemoryBoardApp() {
  // Theme State
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Timeline State
  const [timelinePhotos, setTimelinePhotos] = useState<PhotoItem[]>([]);
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [libraryStats, setLibraryStats] = useState<{ total_photos: number; cap: number } | null>(null);

  // Search Flow State
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<
    'cue_board' | 'sentence' | 'groups' | 'question' | 'almost' | 'fallback' | 'found'
  >('cue_board');
  const [cards, setCards] = useState<CueCardItem[]>([]);
  const [cognitiveCards, setCognitiveCards] = useState<CognitiveCardItem[]>([]);
  const [groups, setGroups] = useState<GroupCardItem[]>([]);
  const [clues, setClues] = useState<ClueItem[]>([]);
  const [activeQuestion, setActiveQuestion] = useState<QuestionItem | null>(null);
  const [questionProgress, setQuestionProgress] = useState({ current: 1, total: 3 });

  // Incomplete Memory Search query
  const [vagueMemoryQuery, setVagueMemoryQuery] = useState('');

  // Almost & Pivots
  const [almostModalPhotoId, setAlmostModalPhotoId] = useState<string | null>(null);
  const [pivotedPhotos, setPivotedPhotos] = useState<PhotoItem[]>([]);

  // Fallback State
  const [fallbackData, setFallbackData] = useState<{
    level: number;
    message: string;
    relaxed_clue_ids: string[];
    followup_probes?: FollowupProbeItem[];
    preserved_context?: string[];
  }>({ level: 1, message: '', relaxed_clue_ids: [], followup_probes: [], preserved_context: [] });

  // Found State
  const [foundPhoto, setFoundPhoto] = useState<PhotoItem | null>(null);
  const [otherGroupPhotos, setOtherGroupPhotos] = useState<PhotoItem[]>([]);

  // Modal & Nudge State
  const [inspectedPhoto, setInspectedPhoto] = useState<PhotoItem | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [deleteToast, setDeleteToast] = useState<string | null>(null);

  const handleDeletePhoto = async (photoId: string, e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
    }
    // Optimistic UI updates
    setTimelinePhotos((prev) => prev.filter((p) => p.id !== photoId));
    if (inspectedPhoto?.id === photoId) {
      setInspectedPhoto(null);
    }
    setLibraryStats((prev) =>
      prev ? { ...prev, total_photos: Math.max(0, prev.total_photos - 1) } : null
    );

    setDeleteToast('Photo removed from library');
    setTimeout(() => setDeleteToast(null), 3200);

    try {
      await deletePhoto(photoId);
    } catch (err) {
      console.error('Failed to delete photo on server:', err);
      loadTimeline();
    }
  };

  const handleSkipToAlbums = async () => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await skipToAlbums(currentSessionId);
      setCurrentStep('groups');
      setClues(res.clues);
      setGroups(res.groups || []);
    } catch (err) {
      console.error('Error skipping to albums:', err);
      handleSubmitCues([]);
    } finally {
      setIsActionLoading(false);
    }
  };

  const {
    showNudge: huntingNudge,
    handleDismiss: dismissHuntingNudge,
    handleAccept: acceptHuntingNudge,
  } = useScrollNudge({
    isViewerOpen: inspectedPhoto !== null,
    hasFoundRecently: currentStep === 'found',
    enabled: !isSearchActive,
  });

  // Load photos on mount
  useEffect(() => {
    loadTimeline();
  }, []);

  const isNudgeVisible = huntingNudge && !isSearchActive;

  const toggleDarkMode = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return next;
    });
  };

  const loadTimeline = async () => {
    setIsLoadingTimeline(true);
    try {
      const data = await fetchPhotos(400);
      setTimelinePhotos(data.photos);
      await loadLibraryStats();
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingTimeline(false);
    }
  };

  const loadLibraryStats = async () => {
    try {
      const stats = await fetchPhotoStats();
      setLibraryStats({ total_photos: stats.total_photos, cap: stats.cap });
    } catch {
      // ignore
    }
  };

  const handleGenerateSmartCards = async (queryText?: string) => {
    setIsActionLoading(true);
    try {
      const q = queryText || vagueMemoryQuery;
      const cueVals = clues.map((c) => c.value);
      const res = await fetchSmartCards(q, cueVals);
      if (res.cards && res.cards.length > 0) {
        setCognitiveCards(res.cards);
      }
    } catch (err) {
      console.error('Failed to generate smart cards', err);
    } finally {
      setIsActionLoading(false);
    }
  };

  // Group photos by Month / Year for the clean timeline view
  const groupedTimeline = useMemo(() => {
    const map: Record<string, PhotoItem[]> = {};
    for (const p of timelinePhotos) {
      const date = p.taken_at ? new Date(p.taken_at) : new Date();
      const monthYear = date.toLocaleDateString(undefined, {
        month: 'long',
        year: 'numeric',
      });
      if (!map[monthYear]) {
        map[monthYear] = [];
      }
      map[monthYear].push(p);
    }
    return map;
  }, [timelinePhotos]);

  // ─── Flow Triggers ──────────────────────────────────────────────────────────

  const handleStartSearch = async (initialQuery?: string) => {
    setIsActionLoading(true);
    setIsSearchActive(true);
    try {
      const res = await startSearchSession('search_pill', initialQuery);
      setCurrentSessionId(res.session_id);
      setCards(res.cards || []);
      setCognitiveCards(res.cognitive_cards || []);
      setClues(res.initial_clues || []);

      // Always present the 4 Big Square Cognitive Cards first to complete lost memory
      setCurrentStep('cue_board');

      // Use Groq AI intelligence to personalize the 4 square cards based on the user's search query
      if (initialQuery && initialQuery.trim()) {
        const clueValues = (res.initial_clues || []).map((c) => c.value);
        fetchSmartCards(initialQuery, clueValues)
          .then((smart) => {
            if (smart.cards && smart.cards.length >= 2) {
              setCognitiveCards(smart.cards);
            }
          })
          .catch(() => {});
      }

      trackEvent('session_start', { entry: 'search_pill' }, res.session_id);
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleExitSearch = () => {
    setIsSearchActive(false);
    setCurrentSessionId(null);
    setFoundPhoto(null);
    setVagueMemoryQuery('');
  };

  const handleSubmitCues = async (selectedCueIds: string[]) => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    trackEvent('board_selection', { selected_ids: selectedCueIds }, currentSessionId);
    try {
      const res = await selectCues(currentSessionId, selectedCueIds);
      setCurrentStep('groups');
      setClues(res.clues);
      setGroups(res.groups || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleAddMemoryText = async (text: string) => {
    if (!currentSessionId) {
      await handleStartSearch(text);
      return;
    }
    setIsActionLoading(true);
    try {
      const res = await addMemoryText(currentSessionId, text);
      setClues(res.clues);
      setGroups(res.groups || []);
      setCurrentStep('groups');
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleSubmitSentence = async (blanks: Record<string, string>) => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await submitSentence(currentSessionId, blanks);
      setCurrentStep('groups');
      setClues(res.clues);
      setGroups(res.groups || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleNoneOfThese = async () => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await noneOfThese(currentSessionId);
      setCurrentStep('question');
      setActiveQuestion(res.question);
      setQuestionProgress({ current: 1, total: 3 });
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleAnswerQuestion = async (questionId: string, optionId: string) => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await answerQuestion(currentSessionId, questionId, optionId);
      setClues(res.clues);
      if (res.step === 'groups') {
        setCurrentStep('groups');
        setGroups(res.groups || []);
      } else if (res.step === 'question' && res.question) {
        setCurrentStep('question');
        setActiveQuestion(res.question);
        setQuestionProgress((prev) => ({
          current: Math.min(prev.current + 1, prev.total),
          total: prev.total,
        }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleRemoveClue = async (clueId: string) => {
    if (!currentSessionId) return;
    try {
      const res = await removeClue(currentSessionId, clueId);
      setClues(res.clues);
      if (currentStep === 'groups') {
        const remaining = res.clues.map((c) => c.value);
        if (remaining.length > 0) {
          const updated = await selectCues(currentSessionId, remaining);
          setGroups(updated.groups || []);
        } else {
          setCurrentStep('cue_board');
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRewind = async () => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await rewindSession(currentSessionId);
      setClues(res.clues);
      if (res.step === 'cue_board') {
        setCurrentStep('cue_board');
      } else if (res.step === 'groups') {
        setCurrentStep('groups');
      } else if (res.step === 'question') {
        setCurrentStep('question');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleTriggerAlmost = (photoId: string) => {
    trackEvent('almost_tapped', { photo_id: photoId }, currentSessionId || undefined);
    setAlmostModalPhotoId(photoId);
  };

  const handleSelectAlmostAxis = async (photoId: string, axis: string) => {
    setAlmostModalPhotoId(null);
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await almostPivot(currentSessionId, photoId, axis);
      setPivotedPhotos(res.photos);
      setCurrentStep('almost');
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleTriggerFallback = async () => {
    if (!currentSessionId) return;
    setIsActionLoading(true);
    try {
      const res = await triggerFallback(currentSessionId);
      setFallbackData({
        level: res.level,
        message: res.message,
        relaxed_clue_ids: res.relaxed_clue_ids,
        followup_probes: res.followup_probes || [],
        preserved_context: res.preserved_context || [],
      });
      if (res.clues) {
        setClues(res.clues);
      }
      if (res.cognitive_cards) {
        setCognitiveCards(res.cognitive_cards);
      }
      setCurrentStep('fallback');
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleConfirmFound = async (photoId: string) => {
    trackEvent('found', { photo_id: photoId, step_count: clues.length + 1 }, currentSessionId || undefined);
    if (currentSessionId) {
      try {
        await confirmFound(currentSessionId, photoId);
      } catch (e) {
        console.error(e);
      }
    }

    const matched = timelinePhotos.find((p) => p.id === photoId);
    if (matched) {
      setFoundPhoto(matched);
      const related = groups.flatMap((g) => g.photos).filter((p) => p.id !== photoId);
      setOtherGroupPhotos(related.slice(0, 10));
      setCurrentStep('found');
    }
  };

  return (
    <main className="min-h-screen bg-canvas text-textPrimary flex flex-col antialiased">
      {/* ─── Clean Google Photos Top Navigation Bar ─── */}
      <header
        role="banner"
        className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-borderSubtle py-2.5 px-4 sm:px-6 flex items-center justify-between gap-3"
      >
        <div className="flex items-center gap-2 shrink-0">
          {isSearchActive ? (
            <button
              type="button"
              onClick={handleExitSearch}
              className="p-2 rounded-full hover:bg-surfaceMuted text-textSecondary transition cursor-pointer"
              aria-label="Return to photos"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" style={{ width: 20, height: 20 }}>
                <path d="M12 4.5v7.5H4.5c0-4.14 3.36-7.5 7.5-7.5z" fill="#EA4335" />
                <path d="M19.5 12c0-4.14-3.36-7.5-7.5-7.5V12h7.5z" fill="#FBBC05" />
                <path d="M12 19.5v-7.5h7.5c0 4.14-3.36 7.5-7.5 7.5z" fill="#34A853" />
                <path d="M4.5 12c0 4.14 3.36 7.5 7.5 7.5V12H4.5z" fill="#4285F4" />
              </svg>
              <span className="font-bold text-lg text-textPrimary tracking-tight font-sans">
                Photos
              </span>
            </div>
          )}
        </div>

        {/* Sleek Central Google-Style Search Bar */}
        <div className="flex-1 max-w-xl mx-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (vagueMemoryQuery.trim()) {
                handleStartSearch(vagueMemoryQuery.trim());
              } else {
                handleStartSearch();
              }
            }}
            className="relative flex items-center"
          >
            <Search
              className="w-4 h-4 text-textSecondary absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ width: 16, height: 16 }}
            />
            <input
              type="text"
              value={vagueMemoryQuery}
              onChange={(e) => setVagueMemoryQuery(e.target.value)}
              placeholder="Search photos or describe a memory..."
              className="w-full pl-9 pr-24 py-2 rounded-full bg-surfaceMuted border border-transparent hover:border-borderSubtle focus:border-brand focus:bg-surface text-sm text-textPrimary placeholder:text-textSecondary focus:outline-none transition"
              style={{ minHeight: 38 }}
            />
            <button
              type="button"
              onClick={() => handleStartSearch(vagueMemoryQuery.trim() || undefined)}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 px-2.5 py-1 text-xs font-semibold rounded-full bg-brand-soft text-brand hover:bg-brand hover:text-white transition flex items-center gap-1 cursor-pointer"
            >
              <Sparkles className="w-3 h-3" style={{ width: 12, height: 12 }} />
              <span>Memory</span>
            </button>
          </form>
        </div>

        {/* Photo Library Capacity & Add Photos Button */}
        <div className="flex items-center gap-2 shrink-0">
          {libraryStats && (
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(true)}
              title="Click to view library capacity and photo options (Cap: 500)"
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surfaceMuted border border-borderSubtle text-[11px] font-semibold text-textSecondary hover:border-brand hover:text-brand transition cursor-pointer"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>{libraryStats.total_photos} / {libraryStats.cap} photos</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:to-indigo-800 text-white transition shadow-sm hover:shadow-md cursor-pointer shrink-0 border border-white/20 active:scale-95"
            aria-label="Upload photos to library"
            title="Upload personal photos to expand library"
          >
            <Plus className="w-4 h-4 text-white stroke-[2.5]" />
            <span className="font-semibold whitespace-nowrap">Add Photos</span>
          </button>

          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleDarkMode}
            className="p-2 rounded-full hover:bg-surfaceMuted text-textSecondary transition cursor-pointer"
            aria-label="Toggle theme"
          >
            {isDarkMode ? (
              <Sun className="w-4 h-4 text-amber-400" style={{ width: 16, height: 16 }} />
            ) : (
              <Moon className="w-4 h-4" style={{ width: 16, height: 16 }} />
            )}
          </button>
        </div>
      </header>

      {/* ─── Search Mode Active ────────────────────────────────────────────── */}
      {isSearchActive ? (
        <section className="flex-1 w-full max-w-4xl mx-auto px-4 py-4">
          {/* Subtle Clue Trail */}
          {currentStep !== 'found' && (
            <ClueTrail
              clues={clues}
              onRemoveClue={handleRemoveClue}
              onRewind={handleRewind}
              canRewind={clues.length > 0}
            />
          )}

          {/* Step 1: Cue Board (4 Big Square Cards for cognitive memory completion) */}
          {currentStep === 'cue_board' && (
            <CueBoard
              cards={cards}
              cognitiveCards={cognitiveCards}
              initialSelected={clues.map((c) => c.value)}
              searchQuery={vagueMemoryQuery}
              onSubmitCues={handleSubmitCues}
              onAddMemoryText={handleAddMemoryText}
              onNoneOfThese={handleNoneOfThese}
              onSkipToAlbums={handleSkipToAlbums}
              onGenerateSmartCards={handleGenerateSmartCards}
              isLoading={isActionLoading}
            />
          )}

          {/* Alternative: Fill-the-Sentence Mode */}
          {currentStep === 'sentence' && (
            <SentenceMode
              onBackToCards={() => setCurrentStep('cue_board')}
              onSubmitSentence={handleSubmitSentence}
              isLoading={isActionLoading}
            />
          )}

          {/* Step 2: 4 Macro Albums (Clean & Uncluttered) */}
          {currentStep === 'groups' && (
            <div className="w-full mx-auto">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <div>
                  <h2 className="text-xl font-bold text-textPrimary tracking-tight">
                    4 Macro Albums
                  </h2>
                  <p className="text-xs text-textSecondary">
                    Clustered by your completed memory cues with calibrated confidence scores.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep('cue_board')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-soft text-brand hover:bg-brand hover:text-white transition cursor-pointer border border-brand/20 shadow-2xs"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Adjust Memory Cards</span>
                </button>
              </div>

              {/* 4 Macro Albums */}
              <div className="space-y-4">
                {groups.slice(0, 4).map((group, idx) => (
                  <GroupCard
                    key={group.id}
                    group={group}
                    rank={idx + 1}
                    onPhotoClick={(p) => setInspectedPhoto(p)}
                    onFound={(pid) => handleConfirmFound(pid)}
                    onAlmost={(pid) => handleTriggerAlmost(pid)}
                    onNotHere={handleTriggerFallback}
                  />
                ))}
              </div>

              <div className="pt-4 pb-6 text-center border-t border-borderSubtle mt-4">
                <button
                  type="button"
                  onClick={handleTriggerFallback}
                  className="text-xs font-semibold text-textSecondary hover:text-textPrimary py-2 px-4 rounded-xl hover:bg-surfaceMuted transition cursor-pointer"
                >
                  Not in these 4 albums? Let&apos;s probe deeper (keeps context)
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Guided Recall Question Sheet */}
          {currentStep === 'question' && activeQuestion && (
            <QuestionSheet
              question={activeQuestion}
              stepIndex={questionProgress.current}
              totalSteps={questionProgress.total}
              onSelectOption={handleAnswerQuestion}
              isLoading={isActionLoading}
            />
          )}

          {/* Step 4: Almost! Pivoted Results View */}
          {currentStep === 'almost' && (
            <div className="w-full max-w-lg mx-auto">
              <header className="mb-4">
                <h2 className="text-xl font-bold text-textPrimary leading-tight mb-1">
                  Adjusted From Your Anchor
                </h2>
                <p className="text-xs text-textSecondary">
                  Surfacing photos matching your distinction.
                </p>
              </header>

              <div className="grid grid-cols-3 gap-2 mb-4">
                {pivotedPhotos.map((p) => (
                  <div
                    key={p.id}
                    className="aspect-square rounded-xl overflow-hidden bg-surfaceMuted border border-borderSubtle relative group cursor-pointer"
                    onClick={() => setInspectedPhoto(p)}
                  >
                    <SafePhotoThumbnail
                      src={p.thumb_256}
                      photoId={p.id}
                      palette={p.palette ? (() => { try { return JSON.parse(p.palette); } catch { return undefined; } })() : undefined}
                      alt="Pivoted photo"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-1">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleConfirmFound(p.id);
                        }}
                        className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-600 text-white shadow-xs"
                      >
                        Found it
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={() => setCurrentStep('groups')}
                className="w-full py-2.5 rounded-xl text-xs font-bold bg-surfaceMuted text-textPrimary hover:bg-borderSubtle transition"
              >
                Back to 4 Macro Albums
              </button>
            </div>
          )}

          {/* Step 5: Fallback View with Context Preservation & Groq AI Probes */}
          {currentStep === 'fallback' && (
            <FallbackView
              message={fallbackData.message}
              level={fallbackData.level}
              relaxedClueIds={fallbackData.relaxed_clue_ids}
              clues={clues}
              followupProbes={fallbackData.followup_probes}
              preservedContext={fallbackData.preserved_context}
              onTryAgain={() => {
                if (clues.length > 0) {
                  handleSubmitCues(clues.map((c) => c.value));
                } else {
                  setCurrentStep('cue_board');
                }
              }}
              onSelectProbeOption={(opt) => handleAddMemoryText(opt)}
              onAddMemoryText={(txt) => handleAddMemoryText(txt)}
              onViewFilteredTimeline={handleExitSearch}
              isLoading={isActionLoading}
            />
          )}

          {/* Step 6: Found Hero View */}
          {currentStep === 'found' && foundPhoto && (
            <FoundView
              photo={foundPhoto}
              otherPhotos={otherGroupPhotos}
              onBackToTimeline={handleExitSearch}
              onSelectOtherPhoto={(p) => setFoundPhoto(p)}
            />
          )}
        </section>
      ) : (
        /* ─── Timeline Gallery Mode: Clean, Simple, Uncluttered ──── */
        <section className="flex-1 max-w-5xl w-full mx-auto px-4 py-4 sm:py-6">
          {/* Month / Date Grouped Photo Grid */}
          {isLoadingTimeline ? (
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="aspect-square rounded-xl bg-surfaceMuted animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedTimeline).map(([monthYear, photos]) => (
                <section key={monthYear} aria-label={`Photos from ${monthYear}`}>
                  <h3 className="text-sm font-bold text-textPrimary mb-2">
                    {monthYear}
                  </h3>
                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
                    {photos.map((photo) => (
                      <div
                        key={photo.id}
                        role="button"
                        tabIndex={0}
                        aria-label="View photo"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setInspectedPhoto(photo);
                          }
                        }}
                        className="relative aspect-square rounded-xl overflow-hidden bg-surfaceMuted border border-borderSubtle hover:border-brand cursor-pointer transition shadow-xs group"
                        onClick={() => setInspectedPhoto(photo)}
                      >
                        <SafePhotoThumbnail
                          src={photo.thumb_256}
                          photoId={photo.id}
                          palette={photo.palette ? (() => { try { return JSON.parse(photo.palette); } catch { return undefined; } })() : undefined}
                          alt="Timeline photo"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                          loading="lazy"
                        />
                        {/* Quick Delete Cross Icon on Photo Tile */}
                        <button
                          type="button"
                          onClick={(e) => handleDeletePhoto(photo.id, e)}
                          title="Delete photo from library"
                          aria-label="Delete this photo"
                          className="absolute top-1.5 right-1.5 p-1 rounded-full bg-black/60 hover:bg-rose-600 text-white/90 hover:text-white transition opacity-0 group-hover:opacity-100 sm:opacity-0 focus:opacity-100 shadow-sm cursor-pointer z-10"
                        >
                          <X className="w-3.5 h-3.5 stroke-[2.5]" />
                        </button>
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ─── Modals & Bottom Sheets ────────────────────────────────────────── */}

      {/* Photo Viewer Modal */}
      {inspectedPhoto && (
        <PhotoViewer
          photo={inspectedPhoto}
          onClose={() => setInspectedPhoto(null)}
          onFound={(pid) => {
            setInspectedPhoto(null);
            handleConfirmFound(pid);
          }}
          onAlmost={(pid) => {
            setInspectedPhoto(null);
            handleTriggerAlmost(pid);
          }}
          onDelete={(pid) => handleDeletePhoto(pid)}
        />
      )}

      {/* Almost! Refinement Bottom Sheet */}
      {almostModalPhotoId && (
        <AlmostSheet
          photoId={almostModalPhotoId}
          onClose={() => setAlmostModalPhotoId(null)}
          onSelectAxis={handleSelectAlmostAxis}
          isLoading={isActionLoading}
        />
      )}

      {/* Scroll Nudge Bottom Sheet */}
      {isNudgeVisible && (
        <ScrollNudge
          onAccept={() => {
            acceptHuntingNudge();
            handleStartSearch();
          }}
          onDismiss={() => {
            dismissHuntingNudge();
          }}
        />
      )}

      {/* Photo Upload Modal (Mobile gallery access & 500-cap) */}
      <PhotoUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={() => {
          loadTimeline();
          loadLibraryStats();
        }}
      />

      {/* Instant Action Toast */}
      {deleteToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900/95 dark:bg-slate-800/95 backdrop-blur-md text-white text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-2xl shadow-xl border border-white/10 flex items-center gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <Trash2 className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{deleteToast}</span>
        </div>
      )}
    </main>
  );
}
