export const TIME_ZONE = "Europe/Moscow";

const formatter = new Intl.DateTimeFormat("ru-RU", {
  timeZone: TIME_ZONE,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatDateTime(iso: string): string {
  return formatter.format(new Date(iso));
}

const timeFormatter = new Intl.DateTimeFormat("ru-RU", { timeZone: TIME_ZONE, hour: "2-digit", minute: "2-digit" });
const dayFormatter = new Intl.DateTimeFormat("ru-RU", { timeZone: "UTC", weekday: "short", day: "2-digit", month: "2-digit" });
const monthFormatter = new Intl.DateTimeFormat("ru-RU", { timeZone: "UTC", month: "long" });
const fullDayFormatter = new Intl.DateTimeFormat("ru-RU", { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric" });

function calendarDate(day: string): Date {
  return new Date(`${day}T00:00:00Z`);
}

export function formatTime(iso: string): string {
  return timeFormatter.format(new Date(iso));
}

export function formatDay(day: string): string {
  return dayFormatter.format(calendarDate(day));
}

export function formatFullDay(day: string): string {
  return fullDayFormatter.format(calendarDate(day));
}

export function formatMonth(month: string): string {
  const name = monthFormatter.format(calendarDate(`${month}-01`));
  return `${name[0].toUpperCase()}${name.slice(1)} ${month.slice(0, 4)}`;
}

const isoDayFormatter = new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" });

export function isoDay(moment: Date): string {
  return isoDayFormatter.format(moment);
}

export function todayIso(): string {
  return isoDay(new Date());
}

export function clockNow(): string {
  return formatTime(new Date().toISOString());
}
