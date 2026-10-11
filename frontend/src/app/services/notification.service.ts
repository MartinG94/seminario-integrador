import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';
export interface UserNotification {
  readonly id: number;
  readonly type: NotificationType;
  readonly message: string;
}

/** Conserva validaciones del servidor sin exponer respuestas técnicas. */
export function httpErrorMessage(error: unknown, fallback: string): string {
  if (!error || typeof error !== 'object') { return fallback; }
  const response = error as { status?: number; error?: unknown };
  if (response.status != null && (response.status < 400 || response.status >= 500)) { return fallback; }
  if (!response.error || typeof response.error !== 'object') { return fallback; }
  const body = response.error as Record<string, unknown>;
  const values = typeof body['detail'] === 'string' ? [body['detail']] : Object.values(body).flat();
  const messages = values.filter((value): value is string => typeof value === 'string' && !!value.trim());
  if (!messages.length || messages.some(value => /[<>]|\b(traceback|stack trace)\b/i.test(value))) {
    return fallback;
  }
  return messages.join(' ');
}

@Injectable({ providedIn: 'root' })
export class NotificationService implements OnDestroy {
  readonly duration = 10000;
  private readonly messages = new BehaviorSubject<readonly UserNotification[]>([]);
  readonly messages$ = this.messages.asObservable();
  private readonly timers = new Map<number, ReturnType<typeof setTimeout>>();
  private nextId = 0;

  success(message: string): number { return this.show('success', message); }
  error(message: string): number { return this.show('error', message); }
  warning(message: string): number { return this.show('warning', message); }
  info(message: string): number { return this.show('info', message); }

  show(type: NotificationType, message: string): number {
    const existing = this.messages.value.find(item => item.type === type && item.message === message);
    if (existing) { return existing.id; }
    const id = ++this.nextId;
    this.messages.next([...this.messages.value, { id, type, message }]);
    this.timers.set(id, setTimeout(() => this.dismiss(id), this.duration));
    return id;
  }

  dismiss(id: number): void {
    clearTimeout(this.timers.get(id));
    this.timers.delete(id);
    this.messages.next(this.messages.value.filter(item => item.id !== id));
  }

  ngOnDestroy(): void {
    this.timers.forEach(timer => clearTimeout(timer));
    this.timers.clear();
    this.messages.next([]);
    this.messages.complete();
  }
}
