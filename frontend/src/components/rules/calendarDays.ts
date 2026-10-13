import type { CalendarDay } from "../../api/lunchRules";
import type { Tone } from "../ui/tone";

export type DayKind = "holiday" | "working";

export const KIND_OPTIONS: { value: DayKind; label: string }[] = [
  { value: "holiday", label: "Выходной" },
  { value: "working", label: "Рабочий" },
];

export function entryOf(day: string, kind: DayKind): CalendarDay {
  return { day, working: kind === "working" };
}

export function kindLabel(entry: CalendarDay): string {
  return entry.working ? "Рабочий" : "Выходной";
}

export function kindTone(entry: CalendarDay): Tone {
  return entry.working ? "ok" : "neutral";
}

export function yearOf(day: string): number {
  return Number(day.slice(0, 4));
}
