export interface Period {
  from: string;
  to: string;
}

export interface PeriodPreset {
  key: string;
  label: string;
  period: (today: string) => Period;
}

const DAYS_IN_WEEK = 7;
const MONDAY_SHIFT = 6;
const ISO_DAY_LENGTH = 10;

const asDate = (day: string) => new Date(`${day}T00:00:00Z`);
const asDay = (date: Date) => date.toISOString().slice(0, ISO_DAY_LENGTH);

function shifted(day: string, days: number): string {
  const date = asDate(day);
  date.setUTCDate(date.getUTCDate() + days);
  return asDay(date);
}

export function thisWeek(today: string): Period {
  const sinceMonday = (asDate(today).getUTCDay() + MONDAY_SHIFT) % DAYS_IN_WEEK;
  return { from: shifted(today, -sinceMonday), to: today };
}

export function thisMonth(today: string): Period {
  return { from: `${today.slice(0, 8)}01`, to: today };
}

export function lastMonth(today: string): Period {
  const lastDay = shifted(`${today.slice(0, 8)}01`, -1);
  return { from: `${lastDay.slice(0, 8)}01`, to: lastDay };
}

export const PERIOD_PRESETS: PeriodPreset[] = [
  { key: "week", label: "Эта неделя", period: thisWeek },
  { key: "month", label: "Этот месяц", period: thisMonth },
  { key: "last-month", label: "Прошлый месяц", period: lastMonth },
];

export const samePeriod = (left: Period, right: Period) => left.from === right.from && left.to === right.to;
