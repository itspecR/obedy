import type { DayMark, Lunch, LunchHistory } from "../../api/lunch";

export type HistoryRow = { day: string; lunch: Lunch; mark: null } | { day: string; lunch: null; mark: DayMark };

export function historyRows(history: LunchHistory): HistoryRow[] {
  const lunches: HistoryRow[] = history.lunches.map((lunch) => ({ day: lunch.day, lunch, mark: null }));
  const marks: HistoryRow[] = history.marks.map((mark) => ({ day: mark.day, lunch: null, mark }));
  return [...lunches, ...marks].sort((left, right) => right.day.localeCompare(left.day));
}
