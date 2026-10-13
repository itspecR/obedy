import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import BrandMark from "../src/components/ui/BrandMark.vue";

const ACCENT = "#4fd8c8";
const read = (path: string) => readFileSync(resolve(__dirname, path), "utf8");

describe("brand", () => {
  it("draws a mint clock face with ticks and hands and no tile", () => {
    const wrapper = mount(BrandMark);

    expect(wrapper.find(".brand__rim").exists()).toBe(true);
    expect(wrapper.find(".brand__ticks").exists()).toBe(true);
    expect(wrapper.find(".brand__hands").exists()).toBe(true);
    expect(wrapper.find("rect").exists()).toBe(false);
    expect(wrapper.text()).toContain("Обеды");
  });

  it("uses the same mint clock for the browser tab", () => {
    const favicon = read("../public/favicon.svg");

    expect(favicon).toContain(ACCENT);
    expect(favicon).not.toContain("<rect");
    expect(read("../src/styles/tokens.css")).toContain(`--accent: ${ACCENT}`);
  });

  it("keeps the app name out of the tab title of the closed page", () => {
    expect(read("../public/forbidden.html")).toContain("<title>Доступ закрыт</title>");
  });
});
