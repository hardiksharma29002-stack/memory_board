/**
 * Client-side telemetry event logger with local SQLite batching via /api/events.
 * Meets privacy requirements: events are logged strictly locally.
 */

interface QueuedEvent {
  name: string;
  session_id?: string;
  ts: string;
  payload: Record<string, unknown>;
}

class TelemetryLogger {
  private queue: QueuedEvent[] = [];
  private flushTimer: ReturnType<typeof setTimeout> | null = null;
  private maxBatchSize = 10;
  private flushIntervalMs = 3000;

  public track(name: string, payload: Record<string, unknown> = {}, sessionId?: string) {
    const event: QueuedEvent = {
      name,
      session_id: sessionId,
      ts: new Date().toISOString(),
      payload,
    };
    this.queue.push(event);

    if (this.queue.length >= this.maxBatchSize) {
      this.flush();
    } else if (!this.flushTimer) {
      this.flushTimer = setTimeout(() => this.flush(), this.flushIntervalMs);
    }
  }

  public async flush(): Promise<void> {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    if (this.queue.length === 0) return;

    const eventsToSend = [...this.queue];
    this.queue = [];

    try {
      await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: eventsToSend }),
      });
    } catch {
      // Telemetry failures must never disrupt user experience; silent swallow
    }
  }
}

export const telemetry = new TelemetryLogger();

export function trackEvent(name: string, payload: Record<string, unknown> = {}, sessionId?: string) {
  telemetry.track(name, payload, sessionId);
}
