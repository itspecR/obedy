import type { Absence } from "../../api/absences";
import type { Board, BoardEntry, Person } from "../../api/board";
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

export interface RosterRow {
  person: Person;
  absence: Absence | null;
}

export interface BoardRoster {
  pending: RosterRow[];
  missing: RosterRow[];
  absent: RosterRow[];
}

const present = (person: Person): RosterRow => ({ person, absence: null });
const away = (absence: Absence): RosterRow => ({ person: { id: absence.person_id, name: absence.name, login: absence.login }, absence });
const found = (rows: RosterRow[], query: string) => rows.filter(({ person }) => matchesQuery(query, [person.name, person.login]));

export function rosterOf(board: Board, query: string): BoardRoster {
  return {
    pending: found(board.pending.map(present), query),
    missing: found(board.missing.map(present), query),
    absent: found(board.absent.map(away), query),
  };
}

export function filterEntries(entries: BoardEntry[], query: string): BoardEntry[] {
  return entries.filter(({ person }) => matchesQuery(query, [person.name, person.login]));
}
