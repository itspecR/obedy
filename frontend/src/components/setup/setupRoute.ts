import type { RouteLocationRaw } from "vue-router";
import { fetchSetupStatus, type SetupStatus } from "../../api/setup";

export const SETUP_ROUTE = "setup";

let known: SetupStatus | null = null;

export function needsSetup(status: SetupStatus): boolean {
  return !status.configured || status.needs_admin;
}

export function decideSetup(targetName: unknown, status: SetupStatus): RouteLocationRaw | null {
  if (needsSetup(status)) {
    return targetName === SETUP_ROUTE ? null : { name: SETUP_ROUTE };
  }
  return targetName === SETUP_ROUTE ? { name: "login" } : null;
}

export async function setupStatus(): Promise<SetupStatus> {
  if (known && !needsSetup(known)) {
    return known;
  }
  try {
    known = await fetchSetupStatus();
  } catch {
    known = { configured: true, needs_admin: false };
  }
  return known;
}
