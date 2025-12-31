"use client";

import { useEffect } from 'react';
import { registerServiceWorker } from '@/lib/sw-register';

export default function ServiceWorkerInit() {
  useEffect(() => {
    // Register service worker in production only
    if (process.env.NODE_ENV === 'production') {
      registerServiceWorker();
    }
  }, []);

  return null;
}
