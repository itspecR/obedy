import type { LunchRules, RulesForm } from "../../api/lunchRules";

export interface Weekday {
  value: string;
  short: string;
  name: string;
}

export const WEEKDAYS: Weekday[] = [
  { value: "1", short: "Пн", name: "Понедельник" },
  { value: "2", short: "Вт", name: "Вторник" },
  { value: "3", short: "Ср", name: "Среда" },
  { value: "4", short: "Чт", name: "Четверг" },
  { value: "5", short: "Пт", name: "Пятница" },
  { value: "6", short: "Сб", name: "Суббота" },
  { value: "7", short: "Вс", name: "Воскресенье" },
];

const CLOCK_LENGTH = 5;

export interface RulesDraft {
  limit_minutes: string;
  workdays: string;
  day_end: string;
  window_enabled: boolean;
  window_start: string;
  window_end: string;
  missing_enabled: boolean;
  missing_since: string;
}

const clock = (value: string) => value.slice(0, CLOCK_LENGTH);

export function draftFrom(rules: LunchRules): RulesDraft {
  return {
    limit_minutes: String(rules.limit_minutes),
    workdays: rules.workdays,
    day_end: clock(rules.day_end),
    window_enabled: rules.window_enabled,
    window_start: clock(rules.window_start),
    window_end: clock(rules.window_end),
    missing_enabled: rules.missing_enabled,
    missing_since: rules.missing_since ?? "",
  };
}

export function formFrom(draft: RulesDraft): RulesForm {
  return { ...draft, limit_minutes: Number(String(draft.limit_minutes).trim()), missing_since: draft.missing_since || null };
}

export function withMissing(draft: RulesDraft, enabled: boolean, today: string): RulesDraft {
  return { ...draft, missing_enabled: enabled, missing_since: draft.missing_since || (enabled ? today : "") };
}

export function toggleDay(workdays: string, day: string): string {
  const days = new Set(workdays);
  if (days.has(day)) {
    days.delete(day);
  } else {
    days.add(day);
  }
  return [...days].sort().join("");
}

export function sameDraft(left: RulesDraft, right: RulesDraft): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}
