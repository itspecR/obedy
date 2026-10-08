import { request } from "./http";

export type LunchStatus = "ongoing" | "on_time" | "overrun" | "unreturned";

export interface Correction {
  by: string;
  at: string;
  reason: string;
  added: boolean;
}

export interface Lunch {
  id: number;
  day: string;
  started_at: string;
  ended_at: string | null;
  limit_minutes: number;
  status: LunchStatus;
  duration_seconds: number;
  auto_closed: boolean;
  correction: Correction | null;
}

export interface LunchState {
  server_time: string;
  tracked: boolean;
  limit_minutes: number;
  warning_minutes: number;
  undo_seconds: number;
  today: Lunch | null;
  can_start: boolean;
  refusal: string;
  undo_until: string | null;
}

export interface LunchSummary {
  count: number;
  violations: number;
  average_minutes: number | null;
}

export interface LunchHistory {
  month: string;
  lunches: Lunch[];
  summary: LunchSummary;
}

export const fetchLunchState = () => request<LunchState>("GET", "/lunch/me");
export const startLunch = () => request<LunchState>("POST", "/lunch/start");
export const finishLunch = () => request<LunchState>("POST", "/lunch/finish");
export const undoLunch = () => request<LunchState>("POST", "/lunch/undo");
export const fetchLunchHistory = (month: string) => request<LunchHistory>("GET", month ? `/lunch/history?month=${encodeURIComponent(month)}` : "/lunch/history");
