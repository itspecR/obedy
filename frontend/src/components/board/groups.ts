import type { BoardEntry } from "../../api/board";
import { matchesQuery } from "../../format/search";
import { remainingSeconds } from "../lunch/countdown";
import { VIOLATION_STATUSES } from "../lunch/lunchStatus";

export interface BoardFilter {
  query: string;
  department: string;
}

export interface BoardGroups {
  away: BoardEntry[];
  violations: BoardEntry[];
  returned: BoardEntry[];
}

export const ALL_DEPARTMENTS = "";
export const EMPTY_BOARD_FILTER: BoardFilter = { query: "", department: ALL_DEPARTMENTS };

const remainingOf = (entry: BoardEntry, now: number) => remainingSeconds(entry.lunch.started_at, entry.lunch.limit_minutes, now);

export function groupEntries(entries: BoardEntry[], now: number): BoardGroups {
  return {
    away: entries.filter((entry) => entry.lunch.status === "ongoing").sort((left, right) => remainingOf(left, now) - remainingOf(right, now)),
    violations: entries.filter((entry) => VIOLATION_STATUSES.includes(entry.lunch.status)),
    returned: entries.filter((entry) => entry.lunch.status === "on_time"),
  };
}

export function filterEntries(entries: BoardEntry[], filter: BoardFilter): BoardEntry[] {
  return entries.filter(
    ({ person }) =>
      (filter.department === ALL_DEPARTMENTS || person.department === filter.department) &&
      matchesQuery(filter.query, [person.name, person.login, person.department, person.position]),
  );
}

export function departmentsOf(entries: BoardEntry[]): string[] {
  return [...new Set(entries.map((entry) => entry.person.department).filter(Boolean))].sort((left, right) => left.localeCompare(right, "ru"));
}
