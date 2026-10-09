import { lightModeOn } from "../composables/useLightMode";

export function stillMotion(): boolean {
  return lightModeOn() || (typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches);
}
