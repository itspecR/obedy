import { request } from "./http";
import type { Lunch } from "./lunch";

export interface Person {
  id: number;
  name: string;
  login: string;
  department: string;
  position: string;
}

export interface BoardEntry {
  person: Person;
  lunch: Lunch;
  can_correct: boolean;
}

export interface Board {
  server_time: string;
  day: string;
  today: string;
  warning_minutes: number;
  entries: BoardEntry[];
}

export interface CorrectionForm {
  started_at: string;
  ended_at: string;
  reason: string;
}

export const fetchBoard = (day: string) => request<Board>("GET", day ? `/lunch/board?day=${encodeURIComponent(day)}` : "/lunch/board");
export const correctLunch = (id: number, form: CorrectionForm) => request<BoardEntry>("PUT", `/lunch/board/${id}/correction`, form);
