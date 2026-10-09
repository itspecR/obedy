import type { SceneName } from "../../rabbit/scenes";

export const FILL_MS = 420;

export type Outcome = "pending" | "success" | "failure";
export type Phase = "appear" | "tap" | "start" | "run" | "dive" | "fill" | "stumble";

export const PHASE_SCENE: Record<Phase, SceneName | null> = {
  appear: "tap",
  tap: "tap",
  start: "start",
  run: "run",
  dive: "dive",
  fill: null,
  stumble: "no",
};

const AFTER_TAP: Record<Outcome, Phase> = { pending: "tap", success: "start", failure: "stumble" };
const AFTER_SUCCESS: Partial<Record<Phase, Phase>> = { start: "run", run: "dive", dive: "fill" };

export function nextPhase(phase: Phase, outcome: Outcome): Phase | null {
  if (phase === "appear") {
    return "tap";
  }
  if (phase === "tap") {
    return AFTER_TAP[outcome];
  }
  return AFTER_SUCCESS[phase] ?? null;
}
