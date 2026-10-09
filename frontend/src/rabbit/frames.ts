import type { SceneName } from "./scenes";
import { SCENES } from "./scenes";

const FILES = import.meta.glob<string>("./frames/*/*.webp", { eager: true, query: "?url", import: "default" });
const NUMBER_WIDTH = 2;

export function frameUrl(scene: SceneName, frame: number): string {
  return FILES[`./frames/${scene}/${scene}-${String(frame).padStart(NUMBER_WIDTH, "0")}.webp`] ?? "";
}

export function preloadScenes(scenes: SceneName[]): void {
  for (const scene of scenes) {
    SCENES[scene].holds.forEach((_, index) => {
      new Image().src = frameUrl(scene, index + 1);
    });
  }
}
