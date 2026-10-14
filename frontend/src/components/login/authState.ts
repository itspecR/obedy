import type { BadgeKind } from "./AuthBadge.vue";

export type AuthState = "idle" | "error" | "success" | "failure" | "recovery" | "return";

const BADGES: Partial<Record<AuthState, { kind: BadgeKind; leaving: boolean }>> = {
  success: { kind: "success", leaving: false },
  failure: { kind: "refused", leaving: false },
  recovery: { kind: "refused", leaving: true },
  return: { kind: "farewell", leaving: true },
};

export function refusing(state: AuthState): boolean {
  return state === "failure" || state === "recovery";
}

export function badgeOf(state: AuthState): { kind: BadgeKind; leaving: boolean } | null {
  return BADGES[state] ?? null;
}
