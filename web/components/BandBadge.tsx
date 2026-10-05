'use client';

import React from 'react';
import { GroupConfidence } from '../lib/types';

interface BandBadgeProps {
  confidence: GroupConfidence | number;
}

export default function BandBadge({ confidence }: BandBadgeProps) {
  let label = 'Not sure yet';
  let percentage = 50;
  let band = 'unsure';

  if (typeof confidence === 'object' && confidence !== null) {
    percentage =
      typeof confidence.percentage === 'number'
        ? confidence.percentage
        : Math.round((confidence.calibrated || confidence.raw || 0.5) * 100);
    label = confidence.percentage_label || `${percentage}% Confidence`;
    band = confidence.band || 'unsure';
  } else if (typeof confidence === 'number') {
    percentage = Math.round(confidence * 100);
    if (percentage >= 70) {
      band = 'highest';
      label = `${percentage}% High Confidence`;
    } else if (percentage >= 45) {
      band = 'good';
      label = `${percentage}% Good Match`;
    } else if (percentage >= 25) {
      band = 'possible';
      label = `${percentage}% Possible`;
    } else {
      band = 'unsure';
      label = `${percentage}% Low Confidence`;
    }
  }

  let badgeStyle =
    'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';

  if (band === 'highest' || percentage >= 75) {
    badgeStyle =
      'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-200 border-emerald-300 dark:border-emerald-800';
  } else if (band === 'good' || percentage >= 50) {
    badgeStyle =
      'bg-blue-50 dark:bg-blue-950/60 text-blue-800 dark:text-blue-200 border-blue-300 dark:border-blue-800';
  } else if (band === 'possible' || percentage >= 30) {
    badgeStyle =
      'bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-200 border-amber-300 dark:border-amber-800';
  }

  // Determine clean band label (e.g. 'Highest chance', 'Good chance', 'Possible')
  let bandLabel = 'Possible match';
  if (typeof confidence === 'object' && confidence !== null) {
    bandLabel = confidence.band_label || '';
  } else {
    bandLabel = label.replace(/^Confidence Score\s*=\s*\d+%\s*·?\s*/i, '').replace(/^\d+%\s*/, '');
  }

  // Filter out any redundant 'Confidence Score' text if present in bandLabel
  bandLabel = bandLabel.replace(/^Confidence Score\s*=\s*\d+%\s*·?\s*/i, '').trim();

  return (
    <span
      role="status"
      aria-label={`Confidence Score = ${percentage} percent, status: ${bandLabel || 'Calculated'}`}
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border shadow-2xs ${badgeStyle}`}
    >
      <span className="font-bold">Confidence Score = {percentage}%</span>
      {bandLabel && bandLabel !== `${percentage}%` && (
        <span className="opacity-80 font-normal">· {bandLabel}</span>
      )}
    </span>
  );
}
