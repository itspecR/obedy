import { afterEach, describe, expect, it, vi } from "vitest";
import { placementFor } from "../src/composables/usePopover";

function screen(width: number, height: number): void {
  vi.spyOn(document.documentElement, "clientWidth", "get").mockReturnValue(width);
  vi.spyOn(document.documentElement, "clientHeight", "get").mockReturnValue(height);
}

afterEach(() => vi.restoreAllMocks());

describe("popover placement", () => {
  it("opens below the field over everything, so a dialog does not scroll", () => {
    screen(1280, 800);
    expect(placementFor(new DOMRect(200, 100, 300, 70), "start")).toEqual({ position: "fixed", top: "176px", bottom: "auto", left: "200px", right: "auto" });
  });

  it("opens upwards when there is no room below", () => {
    screen(1280, 800);
    expect(placementFor(new DOMRect(200, 600, 300, 70), "start")).toMatchObject({ top: "auto", bottom: "206px" });
  });

  it("keeps a short menu below when it fits", () => {
    screen(1280, 600);
    expect(placementFor(new DOMRect(680, 318, 36, 36), "end", 90)).toMatchObject({ top: "360px", bottom: "auto" });
  });

  it("stays below when there is even less room above", () => {
    screen(1280, 400);
    expect(placementFor(new DOMRect(200, 60, 300, 70), "start")).toMatchObject({ top: "136px", bottom: "auto" });
  });

  it("aligns to the right edge near the screen edge or when asked", () => {
    screen(1280, 800);
    expect(placementFor(new DOMRect(1100, 100, 150, 70), "start")).toMatchObject({ left: "auto", right: "30px" });
    expect(placementFor(new DOMRect(500, 100, 36, 36), "end")).toMatchObject({ left: "auto", right: "744px" });
  });

  it("matches the field width for lists", () => {
    screen(1280, 800);
    expect(placementFor(new DOMRect(200, 100, 300, 70), "stretch")).toMatchObject({ left: "200px", width: "300px" });
  });
});
