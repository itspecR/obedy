import type { LunchStatus } from "../../api/lunch";
import type { Tone } from "../ui/tone";

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
