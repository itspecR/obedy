export type AuthState = "idle" | "error" | "success" | "failure" | "recovery";

export function refusing(state: AuthState): boolean {
  return state === "failure" || state === "recovery";
}
