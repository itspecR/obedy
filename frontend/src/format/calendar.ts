export interface CalendarDay {
  day: string;
  inMonth: boolean;
}

const MONTHS_IN_YEAR = 12;
const DAYS_IN_WEEK = 7;
const WEEKS_IN_GRID = 6;
const MONDAY_SHIFT = 6;
const ISO_DAY_LENGTH = 10;
const ISO_MONTH_LENGTH = 7;

export const WEEKDAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const twoDigits = (value: number) => String(value).padStart(2, "0");
const asDate = (day: string) => new Date(`${day}T00:00:00Z`);
const asDay = (date: Date) => date.toISOString().slice(0, ISO_DAY_LENGTH);

export const monthOf = (day: string) => day.slice(0, ISO_MONTH_LENGTH);
export const firstOfMonth = (month: string) => `${month}-01`;

export function shiftDay(day: string, days: number): string {
  const date = asDate(day);
  date.setUTCDate(date.getUTCDate() + days);
  return asDay(date);
}

export function shiftMonth(month: string, delta: number): string {
  const index = Number(month.slice(0, 4)) * MONTHS_IN_YEAR + Number(month.slice(5, 7)) - 1 + delta;
  return `${Math.floor(index / MONTHS_IN_YEAR)}-${twoDigits((index % MONTHS_IN_YEAR) + 1)}`;
}

export function weekdayIndex(day: string): number {
  return (asDate(day).getUTCDay() + MONDAY_SHIFT) % DAYS_IN_WEEK;
}

export function monthGrid(month: string): CalendarDay[] {
  const first = firstOfMonth(month);
  const start = shiftDay(first, -weekdayIndex(first));
  return Array.from({ length: WEEKS_IN_GRID * DAYS_IN_WEEK }, (_, index) => {
    const day = shiftDay(start, index);
    return { day, inMonth: monthOf(day) === month };
  });
}
