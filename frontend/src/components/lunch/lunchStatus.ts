import type { Correction, Lunch, LunchStatus } from "../../api/lunch";
import { formatTime } from "../../format/dateTime";
import type { Tone } from "../ui/tone";
import { formatMinutes } from "./countdown";

export interface StatusView {
  label: string;
  tone: Tone;
}

export const LUNCH_STATUS: Record<LunchStatus, StatusView> = {
  ongoing: { label: "На обеде", tone: "neutral" },
  on_time: { label: "В пределах лимита", tone: "ok" },
  overrun: { label: "Превышение", tone: "alarm" },
  unreturned: { label: "Возврат не отмечен", tone: "attention" },
};

export const MEASURED_STATUSES: LunchStatus[] = ["on_time", "overrun"];
export const VIOLATION_STATUSES: LunchStatus[] = ["overrun", "unreturned"];

export const correctionLabel = (correction: Correction) => (correction.added ? "Добавлено" : "Исправлено");

export const lunchRange = (lunch: Lunch) => (lunch.ended_at ? `${formatTime(lunch.started_at)}–${formatTime(lunch.ended_at)}` : `с ${formatTime(lunch.started_at)}`);
export const lunchDuration = (lunch: Lunch) => (MEASURED_STATUSES.includes(lunch.status) ? formatMinutes(lunch.duration_seconds) : "—");
