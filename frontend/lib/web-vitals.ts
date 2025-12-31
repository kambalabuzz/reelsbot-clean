import { onCLS, onFCP, onINP, onLCP, onTTFB } from 'web-vitals';

type MetricName = 'CLS' | 'FCP' | 'INP' | 'LCP' | 'TTFB';

interface Metric {
  name: MetricName;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
}

function sendToAnalytics(metric: Metric) {
  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.log('[Web Vitals]', metric);
  }

  // Send to Google Analytics if available
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', metric.name, {
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      metric_id: metric.id,
      metric_value: metric.value,
      metric_delta: metric.delta,
      metric_rating: metric.rating,
    });
  }

  // Send to custom analytics endpoint if configured
  if (process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT) {
    const body = JSON.stringify({
      metric: metric.name,
      value: metric.value,
      rating: metric.rating,
      page: window.location.pathname,
      timestamp: Date.now(),
    });

    // Use sendBeacon if available, fallback to fetch
    if (navigator.sendBeacon) {
      navigator.sendBeacon(process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT, body);
    } else {
      fetch(process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT, {
        method: 'POST',
        body,
        headers: { 'Content-Type': 'application/json' },
        keepalive: true,
      }).catch(console.error);
    }
  }
}

export function reportWebVitals() {
  try {
    onCLS(sendToAnalytics);
    onFCP(sendToAnalytics);
    onINP(sendToAnalytics);
    onLCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
  } catch (err) {
    console.error('[Web Vitals] Error:', err);
  }
}

// Helper function to get current Web Vitals snapshot
export async function getWebVitalsSnapshot() {
  const vitals: Record<string, number> = {};

  return new Promise((resolve) => {
    let count = 0;
    const checkComplete = () => {
      count++;
      if (count >= 5) resolve(vitals);
    };

    onCLS((metric) => { vitals.CLS = metric.value; checkComplete(); });
    onFCP((metric) => { vitals.FCP = metric.value; checkComplete(); });
    onINP((metric) => { vitals.INP = metric.value; checkComplete(); });
    onLCP((metric) => { vitals.LCP = metric.value; checkComplete(); });
    onTTFB((metric) => { vitals.TTFB = metric.value; checkComplete(); });

    // Timeout after 5 seconds
    setTimeout(() => resolve(vitals), 5000);
  });
}
