export type SceneName = "tap" | "start" | "run" | "dive" | "no" | "ontime";

export interface Scene {
  holds: number[];
  loop: boolean;
}

export const FRAMES_PER_SECOND = 24;

export const SCENES: Record<SceneName, Scene> = {
  tap: { holds: [6, 3, 3, 3, 3, 6, 6, 6], loop: false },
  start: { holds: [3, 3, 3, 3, 3, 3], loop: false },
  run: { holds: [3, 3, 2, 3, 3, 2], loop: true },
  dive: { holds: [3, 3, 3, 3, 3, 3], loop: false },
  no: { holds: [3, 3, 3, 6, 6, 9], loop: false },
  ontime: { holds: [3, 5, 6, 4, 4, 14], loop: false },
};

export function sceneLength(scene: Scene): number {
  return scene.holds.reduce((total, hold) => total + hold, 0);
}

export function sceneEnded(scene: Scene, tick: number): boolean {
  return !scene.loop && tick >= sceneLength(scene);
}

export function frameAt(scene: Scene, tick: number): number {
  const length = sceneLength(scene);
  let rest = scene.loop ? tick % length : Math.min(tick, length - 1);
  for (const [index, hold] of scene.holds.entries()) {
    if (rest < hold) {
      return index + 1;
    }
    rest -= hold;
  }
  return scene.holds.length;
}
