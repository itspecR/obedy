import { firstOfMonth, monthOf, shiftDay, shiftMonth, weekdayIndex } from "../../format/calendar";

export interface Period {
  from: string;
  to: string;
}

export interface PeriodPreset {
  key: string;
  label: string;
  period: (today: string) => Period;
}

export function thisWeek(today: string): Period {
  return { from: shiftDay(today, -weekdayIndex(today)), to: today };
}

export function thisMonth(today: string): Period {
  return { from: firstOfMonth(monthOf(today)), to: today };
}

export function lastMonth(today: string): Period {
  const month = shiftMonth(monthOf(today), -1);
  return { from: firstOfMonth(month), to: shiftDay(firstOfMonth(monthOf(today)), -1) };
}

export const PERIOD_PRESETS: PeriodPreset[] = [
  { key: "week", label: "Эта неделя", period: thisWeek },
  { key: "month", label: "Этот месяц", period: thisMonth },
  { key: "last-month", label: "Прошлый месяц", period: lastMonth },
];

export const samePeriod = (left: Period, right: Period) => left.from === right.from && left.to === right.to;
