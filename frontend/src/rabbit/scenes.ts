export type SceneName = "tap" | "start" | "run" | "dive" | "no" | "ontime" | "late";

export type Step = [frame: number, ticks: number];

export interface Scene {
  steps: Step[];
  loop: boolean;
  blend?: boolean;
}

export const FRAMES_PER_SECOND = 24;
export const FEET_LINE = 0.88;

export const SCENES: Record<SceneName, Scene> = {
  tap: { steps: [[1, 6], [2, 3], [3, 3], [4, 3], [5, 3], [6, 6], [1, 12]], loop: false, blend: true },
  start: { steps: [[1, 3], [2, 3], [3, 3]], loop: false },
  run: { steps: [[1, 2], [2, 2], [3, 2], [4, 2], [5, 2], [6, 2], [7, 2], [8, 2]], loop: true },
  dive: { steps: [[1, 3], [2, 3]], loop: false },
  no: { steps: [[1, 3], [2, 3], [3, 3], [4, 12]], loop: false, blend: true },
  ontime: { steps: [[1, 5], [2, 6], [3, 6], [4, 4], [5, 8]], loop: false, blend: true },
  late: { steps: [[1, 8], [2, 4], [3, 4], [4, 4], [5, 4], [6, 4], [7, 8], [8, 8], [1, 4]], loop: true, blend: true },
};

export function sceneLength(scene: Scene): number {
  return scene.steps.reduce((total, [, ticks]) => total + ticks, 0);
}

export function sceneFrames(scene: Scene): number[] {
  return [...new Set(scene.steps.map(([frame]) => frame))];
}

export function sceneEnded(scene: Scene, tick: number): boolean {
  return !scene.loop && tick >= sceneLength(scene);
}

export function frameAt(scene: Scene, tick: number): number {
  const length = sceneLength(scene);
  let rest = scene.loop ? tick % length : Math.min(tick, length - 1);
  for (const [frame, ticks] of scene.steps) {
    if (rest < ticks) {
      return frame;
    }
    rest -= ticks;
  }
  return scene.steps[scene.steps.length - 1][0];
}
