import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { PersonStats, Stats } from "../src/api/stats";
import { lastMonth, thisMonth, thisWeek } from "../src/components/stats/period";
import { useToasts } from "../src/composables/useToasts";
import StatsPage from "../src/pages/StatsPage.vue";
import { chooseDay, routeFetch, wasRequested } from "./helpers";

const OCTOBER = "/api/lunch/stats?date_from=2026-10-01&date_to=2026-10-08";

function person(overrides: Partial<PersonStats> = {}): PersonStats {
  return {
    id: 1,
    name: "Иванов Иван",
    login: "ivanov",
    count: 3,
    violations: 2,
    overruns: 1,
    unreturned: 1,
    average_minutes: 42,
    overrun_minutes: 10,
    ...overrides,
  };
}

function stats(overrides: Partial<Stats> = {}): Stats {
  return {
    date_from: "2026-10-01",
    date_to: "2026-10-08",
    overview: { count: 5, violations: 2, average_minutes: 40, on_time_percent: 60, people: 2 },
    people: [person(), person({ id: 2, name: "Петрова Анна", login: "petrova", violations: 0, overruns: 0, unreturned: 0, overrun_minutes: 0 })],
    ...overrides,
  };
}

describe("period presets", () => {
  it("starts the week on Monday and the month on the first", () => {
    expect(thisWeek("2026-10-08")).toEqual({ from: "2026-10-05", to: "2026-10-08" });
    expect(thisWeek("2026-10-05")).toEqual({ from: "2026-10-05", to: "2026-10-05" });
    expect(thisWeek("2026-10-11")).toEqual({ from: "2026-10-05", to: "2026-10-11" });
    expect(thisMonth("2026-10-08")).toEqual({ from: "2026-10-01", to: "2026-10-08" });
  });

  it("takes the whole previous month across the year", () => {
    expect(lastMonth("2026-10-08")).toEqual({ from: "2026-09-01", to: "2026-09-30" });
    expect(lastMonth("2026-01-15")).toEqual({ from: "2025-12-01", to: "2025-12-31" });
    expect(lastMonth("2028-03-01")).toEqual({ from: "2028-02-01", to: "2028-02-29" });
  });
});

describe("StatsPage", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-08T09:00:00Z"));
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(routes: Record<string, [number, unknown]> = {}) {
    const spy = routeFetch({ [OCTOBER]: [200, stats()], ...routes });
    const wrapper = mount(StatsPage, { attachTo: document.body });
    await flushPromises();
    return { spy, wrapper };
  }

  it("opens on this month with overview and worst people first", async () => {
    const { wrapper } = await mounted();
    const rows = wrapper.findAll(".stats-table__row");

    expect(wrapper.get(".stats__tile--alarm").text()).toContain("2");
    expect(wrapper.text()).toContain("60%");
    expect(rows[0].text()).toContain("Иванов Иван");
    expect(rows[0].classes()).toContain("stats-table__row--alarm");
    expect(rows[1].classes()).not.toContain("stats-table__row--alarm");
    wrapper.unmount();
  });

  it("filters by search on the page without a department filter", async () => {
    const { wrapper } = await mounted();

    await wrapper.get('input[placeholder="например: Иванов"]').setValue("петр");

    expect(wrapper.findAll(".stats-table__name").map((name) => name.text())).toEqual(["Петрова Анна"]);
    expect(wrapper.find("select").exists()).toBe(false);
    wrapper.unmount();
  });

  it("switches the period with a preset", async () => {
    const lastMonthUrl = "/api/lunch/stats?date_from=2026-09-01&date_to=2026-09-30";
    const { spy, wrapper } = await mounted({ [lastMonthUrl]: [200, stats({ people: [] })] });

    const preset = wrapper.findAll(".stats__presets button").find((button) => button.text() === "Прошлый месяц");
    await preset?.trigger("click");
    await flushPromises();

    expect(wasRequested(spy, lastMonthUrl, "GET")).toBe(true);
    expect(preset?.attributes("aria-pressed")).toBe("true");
    expect(wrapper.text()).toContain("За этот период обедов нет");
    wrapper.unmount();
  });

  it("downloads the Excel file", async () => {
    const exportUrl = "/api/lunch/stats/export?date_from=2026-10-01&date_to=2026-10-08";
    const file = new Response("xlsx", { status: 200, headers: { "Content-Disposition": 'attachment; filename="obedy_2026-10-01_2026-10-08.xlsx"' } });
    const spy = vi.fn((url: string) => Promise.resolve(url === exportUrl ? file : new Response(JSON.stringify(stats()), { status: 200 })));
    vi.stubGlobal("fetch", spy);
    const createObjectURL = vi.fn(() => "blob:excel");
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL, revokeObjectURL: vi.fn() }));
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    const wrapper = mount(StatsPage, { attachTo: document.body });
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Скачать Excel")?.trigger("click");
    await flushPromises();

    expect(wasRequested(spy, exportUrl, "GET")).toBe(true);
    expect(createObjectURL).toHaveBeenCalled();
    expect((click.mock.contexts[0] as HTMLAnchorElement).download).toBe("obedy_2026-10-01_2026-10-08.xlsx");
    click.mockRestore();
    wrapper.unmount();
  });

  it("explains a refused period", async () => {
    const badUrl = "/api/lunch/stats?date_from=2026-10-08&date_to=2026-10-01";
    const { wrapper } = await mounted({ [badUrl]: [400, { detail: "Начало периода позже конца" }] });

    await chooseDay(wrapper, "По", "2026-10-01");
    await chooseDay(wrapper, "С", "2026-10-08");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Начало периода позже конца");
    wrapper.unmount();
  });
});
