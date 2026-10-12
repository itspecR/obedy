export interface WallTime {
  hours: number;
  minutes: number;
}

export interface Arc {
  start: number;
  end: number;
}

export const DEGREES_PER_HOUR = 30;
export const DEGREES_PER_MINUTE = 6;
const MINUTES_PER_HOUR = 60;
const FULL_TURN = 360;
const HALF_TURN = 180;
const LONGEST_ARC = 359.9;

export function wallTime(instant: number, timeZone?: string): WallTime {
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(instant);
  const part = (type: string) => Number(parts.find((item) => item.type === type)?.value ?? 0);
  return { hours: part("hour"), minutes: part("minute") };
}

export function hourAngle({ hours, minutes }: WallTime): number {
  return (hours % 12) * DEGREES_PER_HOUR + (minutes * DEGREES_PER_HOUR) / MINUTES_PER_HOUR;
}

export function minuteAngle({ minutes }: WallTime): number {
  return minutes * DEGREES_PER_MINUTE;
}

export function turnTowards(previous: number, target: number): number {
  const forward = (((target - previous) % FULL_TURN) + FULL_TURN) % FULL_TURN;
  return forward <= HALF_TURN ? previous + forward : previous + forward - FULL_TURN;
}

export function clockTimeOf(value: string): WallTime {
  const [hours, minutes] = value.split(":").map(Number);
  return { hours, minutes };
}

export function arcOf(start: WallTime, end: WallTime): Arc {
  const from = hourAngle(start);
  const span = Math.min(LONGEST_ARC, (end.hours - start.hours) * DEGREES_PER_HOUR + ((end.minutes - start.minutes) * DEGREES_PER_HOUR) / MINUTES_PER_HOUR);
  return { start: from, end: from + span };
}
