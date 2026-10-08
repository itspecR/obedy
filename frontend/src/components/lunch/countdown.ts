import type { Tone } from "../ui/tone";

const MS_IN_SECOND = 1000;
const SECONDS_IN_MINUTE = 60;
const SECONDS_IN_HOUR = 3600;

const twoDigits = (value: number) => String(value).padStart(2, "0");

export function elapsedSeconds(fromIso: string, nowMs: number): number {
  return Math.floor((nowMs - Date.parse(fromIso)) / MS_IN_SECOND);
}

export function remainingSeconds(startedAt: string, limitMinutes: number, nowMs: number): number {
  return limitMinutes * SECONDS_IN_MINUTE - elapsedSeconds(startedAt, nowMs);
}

export function secondsUntil(iso: string, nowMs: number): number {
  return Math.max(0, Math.ceil((Date.parse(iso) - nowMs) / MS_IN_SECOND));
}

export function countdownTone(remaining: number, warningMinutes: number): Tone {
  if (remaining < 0) {
    return "alarm";
  }
  return remaining <= warningMinutes * SECONDS_IN_MINUTE ? "attention" : "ok";
}

export function formatClock(seconds: number): string {
  const total = Math.max(0, seconds);
  const hours = Math.floor(total / SECONDS_IN_HOUR);
  const minutes = Math.floor((total % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE);
  const clock = `${twoDigits(minutes)}:${twoDigits(total % SECONDS_IN_MINUTE)}`;
  return hours ? `${hours}:${clock}` : clock;
}

export function countdownText(remaining: number): string {
  return remaining < 0 ? `Превышение +${Math.ceil(-remaining / SECONDS_IN_MINUTE)} мин` : formatClock(remaining);
}

export function formatMinutes(seconds: number): string {
  return `${Math.round(seconds / SECONDS_IN_MINUTE)} мин`;
}

export function returnBy(startedAt: string, limitMinutes: number): string {
  return new Date(Date.parse(startedAt) + limitMinutes * SECONDS_IN_MINUTE * MS_IN_SECOND).toISOString();
}
