import type { BoardEntry } from "../../api/board";
import { matchesQuery } from "../../format/search";
import { remainingSeconds } from "../lunch/countdown";
import { VIOLATION_STATUSES } from "../lunch/lunchStatus";

export interface BoardGroups {
  away: BoardEntry[];
  violations: BoardEntry[];
  returned: BoardEntry[];
}

const remainingOf = (entry: BoardEntry, now: number) => remainingSeconds(entry.lunch.started_at, entry.lunch.limit_minutes, now);

export function groupEntries(entries: BoardEntry[], now: number): BoardGroups {
  return {
    away: entries.filter((entry) => entry.lunch.status === "ongoing").sort((left, right) => remainingOf(left, now) - remainingOf(right, now)),
    violations: entries.filter((entry) => VIOLATION_STATUSES.includes(entry.lunch.status)),
    returned: entries.filter((entry) => entry.lunch.status === "on_time"),
  };
}

export function filterEntries(entries: BoardEntry[], query: string): BoardEntry[] {
  return entries.filter(({ person }) => matchesQuery(query, [person.name, person.login]));
}
