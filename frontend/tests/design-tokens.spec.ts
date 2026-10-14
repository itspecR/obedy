import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const TOKENS = readFileSync(resolve(__dirname, "../src/styles/tokens.css"), "utf8");
const AA_TEXT = 4.5;
const DISTINCT_HUE_DEGREES = 15;

function token(name: string): string {
  const match = new RegExp(`--${name}:\\s*([^;]+);`).exec(TOKENS);
  if (!match) {
    throw new Error(`token --${name} is missing`);
  }
  return match[1].trim();
}

function rgb(hex: string): [number, number, number] {
  const value = Number.parseInt(hex.replace("#", ""), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function luminance(hex: string): number {
  const [r, g, b] = rgb(hex).map((channel) => {
    const unit = channel / 255;
    return unit <= 0.03928 ? unit / 12.92 : ((unit + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(foreground: string, background: string): number {
  const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}

function hue(hex: string): number {
  const [r, g, b] = rgb(hex).map((channel) => channel / 255);
  const max = Math.max(r, g, b);
  const delta = max - Math.min(r, g, b);
  const sector = max === r ? ((g - b) / delta) % 6 : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
  return (sector * 60 + 360) % 360;
}

describe("design tokens", () => {
  it("keeps the accent apart from the green that means a normal status", () => {
    expect(token("accent")).not.toBe(token("green"));
    expect(Math.abs(hue(token("accent")) - hue(token("green")))).toBeGreaterThan(DISTINCT_HUE_DEGREES);
  });

  it("has no blue tokens left", () => {
    expect(TOKENS).not.toMatch(/--blue/);
  });

  it("keeps body, secondary and accent text readable on the darkest and the lightest surface", () => {
    for (const background of [token("canvas"), token("field-solid")]) {
      for (const text of ["ink", "muted", "accent"]) {
        expect(contrast(token(text), background), `${text} on ${background}`).toBeGreaterThanOrEqual(AA_TEXT);
      }
    }
  });

  it("keeps blur within the cost the design skill allows", () => {
    expect(Number(/blur\((\d+)px\)/.exec(token("glass-blur"))?.[1])).toBeLessThanOrEqual(20);
  });
});
