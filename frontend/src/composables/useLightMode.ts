import { computed, ref, watchEffect } from "vue";
import { prefersLessTransparency, softwareRendering } from "../device/renderer";

export type LightPreference = "auto" | "on" | "off";

const STORAGE_KEY = "obedy.light-mode";
const LIGHT_CLASS = "light-mode";
const PREFERENCES: LightPreference[] = ["auto", "on", "off"];

const preference = ref<LightPreference>(storedPreference());
const weakDevice = ref(false);
const enabled = computed(() => preference.value === "on" || (preference.value === "auto" && weakDevice.value));

function storedPreference(): LightPreference {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return PREFERENCES.find((item) => item === value) ?? "auto";
  } catch {
    return "auto";
  }
}

function store(value: LightPreference): boolean {
  try {
    localStorage.setItem(STORAGE_KEY, value);
    return true;
  } catch {
    return false;
  }
}

function choose(value: LightPreference): void {
  preference.value = value;
  store(value);
}

export function lightModeOn(): boolean {
  return enabled.value;
}

export function initLightMode(): void {
  weakDevice.value = softwareRendering() || prefersLessTransparency();
  watchEffect(() => document.documentElement.classList.toggle(LIGHT_CLASS, enabled.value));
}

export function useLightMode() {
  return { preference: computed(() => preference.value), weakDevice: computed(() => weakDevice.value), enabled, choose };
}
