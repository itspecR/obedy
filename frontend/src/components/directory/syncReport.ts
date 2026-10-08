import type { SyncReport, SyncStatus } from "../../api/directory";
import { formatDateTime } from "../../format/dateTime";
import type { Tone } from "../ui/tone";

export interface SyncView {
  tone: Tone;
  text: string;
}

const TONES: Record<SyncStatus, Tone> = {
  done: "ok",
  skipped: "neutral",
  guarded: "attention",
  failed: "alarm",
};

export const NEVER_RAN = "Синхронизация ещё не выполнялась. Она запускается сама каждый час или по кнопке";

export function describeSync(report: SyncReport | null): SyncView {
  if (!report?.status || !report.finished_at) {
    return { tone: "neutral", text: NEVER_RAN };
  }
  return { tone: TONES[report.status], text: `${formatDateTime(report.finished_at)} — ${report.message}` };
}
