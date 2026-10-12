import type { SceneName } from "./scenes";
import { SCENES, sceneFrames } from "./scenes";

const FILES = import.meta.glob<string>("./frames/*/*.webp", { eager: true, query: "?url", import: "default" });
const NUMBER_WIDTH = 2;

export function frameUrl(scene: SceneName, frame: number): string {
  return FILES[`./frames/${scene}/${scene}-${String(frame).padStart(NUMBER_WIDTH, "0")}.webp`] ?? "";
}

export function preloadScenes(scenes: SceneName[]): void {
  for (const scene of scenes) {
    sceneFrames(SCENES[scene]).forEach((frame) => {
      new Image().src = frameUrl(scene, frame);
    });
  }
}
