const MONTHS_IN_YEAR = 12;

const twoDigits = (value: number) => String(value).padStart(2, "0");

export function shiftMonth(month: string, delta: number): string {
  const index = Number(month.slice(0, 4)) * MONTHS_IN_YEAR + Number(month.slice(5, 7)) - 1 + delta;
  return `${Math.floor(index / MONTHS_IN_YEAR)}-${twoDigits((index % MONTHS_IN_YEAR) + 1)}`;
}
