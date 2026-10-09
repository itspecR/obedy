import type { Person } from "./board";
import { request } from "./http";

export type JournalAction =
  | "login"
  | "login_failed"
  | "logout"
  | "password_changed"
  | "role_changed"
  | "track_lunch_changed"
  | "blocked"
  | "unblocked"
  | "account_created"
  | "profile_changed"
  | "password_issued"
  | "lunch_corrected"
  | "lunch_added"
  | "rules_changed"
  | "network_added"
  | "network_removed"
  | "private_networks_changed"
  | "directory_changed"
  | "directory_checked"
  | "directory_synced";

export type JournalCategory = "logins" | "staff" | "lunches" | "settings";

export interface JournalRow {
  label: string;
  before: string | null;
  after: string | null;
}

export interface JournalEntry {
  id: number;
  created_at: string;
  action: JournalAction;
  actor: Person | null;
  target: Person | null;
  address: string;
  details: JournalRow[];
}

export interface Journal {
  entries: JournalEntry[];
  has_more: boolean;
}

export interface JournalQuery {
  date_from: string;
  date_to: string;
  person: number | null;
  category: JournalCategory | null;
  before?: number;
}

function queryOf(query: JournalQuery): string {
  const pairs = Object.entries(query).filter(([, value]) => value !== null && value !== undefined && value !== "");
  return new URLSearchParams(pairs.map(([key, value]) => [key, String(value)])).toString();
}

export const fetchJournal = (query: JournalQuery) => request<Journal>("GET", `/journal?${queryOf(query)}`);
export const fetchJournalPeople = () => request<Person[]>("GET", "/journal/people");
