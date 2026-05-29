import type { SSEEvent } from "../types";

export class SSEManager {
  private es: EventSource | null = null;
  private listeners = new Map<string, Set<(data: any) => void>>();
  private backoffMs = 1000;

  start() {
    this.es = new EventSource("/api/sse");
    this.es.onerror = () => {
      this.es?.close();
      setTimeout(() => this.start(), this.backoffMs);
      this.backoffMs = Math.min(this.backoffMs * 2, 8000);
    };
    this.es.onopen = () => { this.backoffMs = 1000; };
    for (const name of ["session_updated", "gate_reached", "gate_approved", "resume_started", "resume_failed", "session_completed", "project_registered", "phase_started", "phase_completed", "phase_pr_opened"]) {
      this.es.addEventListener(name, (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        for (const cb of this.listeners.get(name) ?? []) cb(data);
      });
    }
  }

  on(type: SSEEvent["type"], cb: (data: any) => void): () => void {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type)!.add(cb);
    return () => this.listeners.get(type)?.delete(cb);
  }

  stop() { this.es?.close(); this.es = null; }
}
