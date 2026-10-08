import { describe, expect, it } from "vitest";
import { boxOf, isForward, sameBox } from "../src/components/ui/glass";

const track = { clientWidth: 200, clientHeight: 400 };
const item = (offsetTop: number, offsetLeft = 0) => ({ offsetTop, offsetLeft, offsetWidth: 200, offsetHeight: 40 });

describe("glass pill geometry", () => {
  it("measures the item as distances from every edge of the track", () => {
    expect(boxOf(item(80), track)).toEqual({ top: 80, left: 0, right: 0, bottom: 280 });
  });

  it("moves forward when going down or right", () => {
    const top = boxOf(item(0), track);
    const lower = boxOf(item(120), track);
    expect(isForward(top, lower)).toBe(true);
    expect(isForward(lower, top)).toBe(false);
    expect(isForward(null, top)).toBe(true);
  });

  it("recognises the same place", () => {
    expect(sameBox(boxOf(item(40), track), boxOf(item(40), track))).toBe(true);
    expect(sameBox(null, boxOf(item(40), track))).toBe(false);
  });
});

describe("glass pill in a scrolled row", () => {
  it("allows a negative right edge for items beyond the visible width", () => {
    const row = { clientWidth: 286, clientHeight: 49 };
    expect(boxOf({ offsetTop: 0, offsetLeft: 300, offsetWidth: 83, offsetHeight: 49 }, row)).toEqual({ top: 0, left: 300, right: -97, bottom: 0 });
  });
});

import { centerOf, LIFT, nearestIndex, shiftBox, stretchOf } from "../src/components/ui/glass";

describe("glass drag", () => {
  it("stretches along the motion and narrows across it", () => {
    const fast = stretchOf(0, 2);
    expect(fast.y).toBeGreaterThan(LIFT);
    expect(fast.x).toBeLessThan(LIFT);
    const sideways = stretchOf(-2, 0);
    expect(sideways.x).toBeGreaterThan(sideways.y);
  });

  it("stays round when the pointer rests", () => {
    expect(stretchOf(0, 0)).toEqual({ x: LIFT, y: LIFT });
  });

  it("limits the stretch", () => {
    expect(stretchOf(0, 100).y).toBeCloseTo(LIFT * 1.4);
  });

  it("moves the whole box along one axis", () => {
    const box = { top: 40, left: 0, right: 0, bottom: 320 };
    expect(shiftBox(box, "y", 30)).toEqual({ top: 70, left: 0, right: 0, bottom: 290 });
    expect(centerOf(box, { clientWidth: 200, clientHeight: 400 }, "y")).toBe(60);
  });

  it("drops onto the nearest item", () => {
    expect(nearestIndex([20, 60, 100, 140], 88)).toBe(2);
    expect(nearestIndex([20, 60, 100, 140], -50)).toBe(0);
    expect(nearestIndex([20, 60, 100, 140], 999)).toBe(3);
  });
});

import { leanOf, NO_LEAN } from "../src/components/ui/glass";

describe("glass lean", () => {
  const track = { clientWidth: 200, clientHeight: 400 };
  const box = { top: 100, left: 0, right: 0, bottom: 260 };

  it("does nothing when the pointer is far away", () => {
    expect(leanOf({ x: 100, y: 390 }, box, track)).toEqual(NO_LEAN);
  });

  it("leans toward a nearby pointer and stretches that way", () => {
    const lean = leanOf({ x: 100, y: 170 }, box, track);
    expect(lean.offset.y).toBeGreaterThan(0);
    expect(lean.offset.y).toBeLessThanOrEqual(6);
    expect(lean.scale.y).toBeGreaterThan(1);
    expect(lean.scale.x).toBeLessThan(1);
  });
});

import { liftOf } from "../src/components/ui/glass";

describe("glass lift", () => {
  it("grows a wide pill by a few pixels, not by a percentage", () => {
    const lift = liftOf(190, 40);
    expect(190 * lift.x - 190).toBeCloseTo(14);
    expect(40 * lift.y - 40).toBeCloseTo(5.6);
  });
});

import { edgeScrollSpeed, LEAD_SPRING, projectLanding, smoothVelocity, springSettled, springStep, TRAIL_SPRING, type SpringState } from "../src/components/ui/glass";

describe("glass throw and spring", () => {
  it("throws the landing point further with a fast release", () => {
    expect(projectLanding(100, 0)).toBe(100);
    expect(projectLanding(100, 1.5)).toBeGreaterThan(300);
    expect(projectLanding(100, -1)).toBeLessThan(0);
  });

  it("scrolls only near the edges, faster at the very edge", () => {
    expect(edgeScrollSpeed(150, 300)).toBe(0);
    expect(edgeScrollSpeed(2, 300)).toBeLessThan(edgeScrollSpeed(30, 300));
    expect(edgeScrollSpeed(298, 300)).toBeGreaterThan(edgeScrollSpeed(270, 300));
    expect(edgeScrollSpeed(270, 300)).toBeGreaterThan(0);
  });

  it("smooths the pointer speed", () => {
    expect(smoothVelocity(0, 1)).toBeCloseTo(0.4);
    expect(smoothVelocity(1, 1)).toBeCloseTo(1);
  });

  for (const [name, tune] of [["lead", LEAD_SPRING], ["trail", TRAIL_SPRING]] as const) {
    it(`${name} spring overshoots a little and settles on the target`, () => {
      let state: SpringState = { value: 0, velocity: 0 };
      let peak = 0;
      for (let frame = 0; frame < 240 && !springSettled(state, 100); frame++) {
        state = springStep(state, 100, tune, 1 / 60);
        peak = Math.max(peak, state.value);
      }
      expect(springSettled(state, 100)).toBe(true);
      expect(peak).toBeGreaterThan(100);
      expect(peak).toBeLessThan(125);
    });
  }
});

import { releaseVelocity } from "../src/components/ui/glass";

describe("glass release", () => {
  it("forgets the speed after a pause", () => {
    expect(releaseVelocity(2, 20)).toBe(2);
    expect(releaseVelocity(2, 300)).toBe(0);
  });

  it("caps an unrealistic speed", () => {
    expect(projectLanding(0, 50)).toBe(projectLanding(0, 3));
  });
});

import { nextIndex } from "../src/components/ui/glass";

describe("glass keyboard", () => {
  it("moves along the menu with arrows and wraps around", () => {
    expect(nextIndex(0, "ArrowDown", "y", 5)).toBe(1);
    expect(nextIndex(0, "ArrowUp", "y", 5)).toBe(4);
    expect(nextIndex(4, "ArrowDown", "y", 5)).toBe(0);
    expect(nextIndex(2, "ArrowRight", "x", 5)).toBe(3);
  });

  it("jumps to the ends and ignores other keys", () => {
    expect(nextIndex(2, "Home", "y", 5)).toBe(0);
    expect(nextIndex(2, "End", "y", 5)).toBe(4);
    expect(nextIndex(2, "ArrowRight", "y", 5)).toBeNull();
    expect(nextIndex(2, "Enter", "y", 5)).toBeNull();
  });
});

import { CLICK_MOTION, FOLLOW_MOTION } from "../src/components/ui/glass";

function run(motion: typeof CLICK_MOTION, frames = 120) {
  let lead: SpringState = { value: 0, velocity: 0 };
  let trail: SpringState = { value: 0, velocity: 0 };
  let peak = 0;
  let longest = 0;
  let settledAt = -1;
  for (let frame = 0; frame < frames; frame++) {
    lead = springStep(lead, 100, motion.lead, 1 / 60);
    trail = springStep(trail, 100, motion.trail, 1 / 60);
    peak = Math.max(peak, lead.value, trail.value);
    longest = Math.max(longest, lead.value - trail.value);
    if (settledAt < 0 && springSettled(lead, 100) && springSettled(trail, 100)) {
      settledAt = frame;
    }
  }
  return { peak, longest, settledAt };
}

describe("glass motion", () => {
  it("pours like a drop on a click: a clear stretch, a small springy settle, done in under a second", () => {
    const { peak, longest, settledAt } = run(CLICK_MOTION);
    expect(longest).toBeGreaterThan(20);
    expect(peak).toBeLessThan(103);
    expect(settledAt).toBeGreaterThan(15);
    expect(settledAt).toBeLessThan(60);
  });

  it("follows the finger closely while dragging", () => {
    expect(run(FOLLOW_MOTION).settledAt).toBeLessThan(25);
  });
});

import { revealScroll } from "../src/components/ui/glass";

describe("glass reveal", () => {
  it("leaves the menu alone when the item is fully visible", () => {
    expect(revealScroll(40, 80, 0, 300, 500)).toBeNull();
  });

  it("scrolls a hidden item to the middle of the menu", () => {
    expect(revealScroll(400, 80, 0, 300, 500)).toBe(200);
    expect(revealScroll(10, 80, 150, 300, 500)).toBe(0);
  });

  it("never scrolls past the ends", () => {
    expect(revealScroll(440, 60, 0, 300, 500)).toBe(200);
  });
});

import { neckOf } from "../src/components/ui/glass";

describe("glass neck", () => {
  const from = { near: 0, far: 40 };
  const to = { near: 200, far: 260 };

  it("thins the drop while it is stretched between the buttons", () => {
    expect(neckOf({ near: 60, far: 180 }, from, to)).toBeLessThan(0.8);
  });

  it("keeps the full height at rest and when the drop only grows into a wider button", () => {
    expect(neckOf(from, from, to)).toBe(1);
    expect(neckOf(to, from, to)).toBe(1);
  });

  it("never pinches thinner than the floor", () => {
    expect(neckOf({ near: 0, far: 1000 }, from, to)).toBeCloseTo(0.72);
  });
});
