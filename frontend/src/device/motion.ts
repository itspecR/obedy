import { lightModeOn } from "../composables/useLightMode";

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

export function reducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia(REDUCED_MOTION_QUERY).matches;
}

export function stillMotion(): boolean {
  return lightModeOn() || reducedMotion();
}
