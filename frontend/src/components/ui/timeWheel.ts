export interface Clock {
  hours: number;
  minutes: number;
}

const HOURS_IN_DAY = 24;
const MINUTES_IN_HOUR = 60;
const CLOCK_PATTERN = /^(\d{2}):(\d{2})$/;

export const WHEEL_ITEM_HEIGHT = 40;
export const WHEEL_VISIBLE_ITEMS = 5;
export const HOURS = Array.from({ length: HOURS_IN_DAY }, (_, hour) => hour);
export const MINUTES = Array.from({ length: MINUTES_IN_HOUR }, (_, minute) => minute);

export const twoDigits = (value: number) => String(value).padStart(2, "0");

export function parseClock(text: string): Clock | null {
  const matched = CLOCK_PATTERN.exec(text);
  if (!matched) {
    return null;
  }
  const hours = Number(matched[1]);
  const minutes = Number(matched[2]);
  return hours < HOURS_IN_DAY && minutes < MINUTES_IN_HOUR ? { hours, minutes } : null;
}

export function clockText({ hours, minutes }: Clock): string {
  return `${twoDigits(hours)}:${twoDigits(minutes)}`;
}

export function indexAt(scrollTop: number, count: number): number {
  return Math.min(count - 1, Math.max(0, Math.round(scrollTop / WHEEL_ITEM_HEIGHT)));
}
