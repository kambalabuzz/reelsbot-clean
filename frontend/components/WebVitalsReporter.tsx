"use client";

import { useEffect } from 'react';
import { reportWebVitals } from '@/lib/web-vitals';

export default function WebVitalsReporter() {
  useEffect(() => {
    // Only report Web Vitals in production
    if (process.env.NODE_ENV === 'production') {
      reportWebVitals();
    }
  }, []);

  return null;
}
