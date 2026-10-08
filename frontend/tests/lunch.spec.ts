import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Lunch, LunchHistory, LunchState } from "../src/api/lunch";
import { countdownText, countdownTone, formatClock, remainingSeconds, secondsUntil } from "../src/components/lunch/countdown";
import LunchControl from "../src/components/lunch/LunchControl.vue";
import { shiftMonth } from "../src/components/lunch/months";
import { useToasts } from "../src/composables/useToasts";
import { formatDay, formatMonth, formatTime } from "../src/format/dateTime";
import LunchPage from "../src/pages/LunchPage.vue";
import { useSession } from "../src/stores/session";
import { routeFetch, wasRequested } from "./helpers";
import { me } from "./people";

const NOON = "2026-10-08T09:00:00Z";
const at = (minutes: number) => Date.parse(NOON) + minutes * 60_000;
const iso = (minutes: number) => new Date(at(minutes)).toISOString();

function lunch(overrides: Partial<Lunch> = {}): Lunch {
  return {
    id: 1,
    day: "2026-10-08",
    started_at: NOON,
    ended_at: null,
    limit_minutes: 45,
    status: "ongoing",
    duration_seconds: 0,
    auto_closed: false,
    correction: null,
    ...overrides,
  };
}

function state(overrides: Partial<LunchState> = {}): LunchState {
  return {
    server_time: NOON,
    tracked: true,
    limit_minutes: 45,
    warning_minutes: 5,
    undo_seconds: 300,
    today: null,
    can_start: true,
    refusal: "",
    undo_until: null,
    ...overrides,
  };
}

function history(overrides: Partial<LunchHistory> = {}): LunchHistory {
  return { month: "2026-10", lunches: [], summary: { count: 0, violations: 0, average_minutes: null }, ...overrides };
}

describe("lunch countdown", () => {
  it("counts down from the limit and colours the last minutes", () => {
    expect(remainingSeconds(NOON, 45, at(10))).toBe(35 * 60);
    expect(countdownTone(301, 5)).toBe("ok");
    expect(countdownTone(300, 5)).toBe("attention");
    expect(countdownTone(-1, 5)).toBe("alarm");
  });

  it("shows the clock and the overrun in whole minutes", () => {
    expect(formatClock(2100)).toBe("35:00");
    expect(formatClock(3725)).toBe("1:02:05");
    expect(formatClock(-5)).toBe("00:00");
    expect(countdownText(-1)).toBe("Превышение +1 мин");
    expect(countdownText(-61)).toBe("Превышение +2 мин");
  });

  it("never shows negative time to the undo deadline", () => {
    expect(secondsUntil(iso(5), at(3))).toBe(120);
    expect(secondsUntil(iso(5), at(6))).toBe(0);
  });

  it("moves between months across the year", () => {
    expect(shiftMonth("2026-01", -1)).toBe("2025-12");
    expect(shiftMonth("2026-12", 1)).toBe("2027-01");
  });

  it("formats time, day and month in Moscow time", () => {
    expect(formatTime(NOON)).toBe("12:00");
    expect(formatDay("2026-10-08")).toBe("чт, 08.10");
    expect(formatMonth("2026-10")).toBe("Октябрь 2026");
  });
});

describe("LunchControl", () => {
  const control = (current: LunchState, now = at(0)) => mount(LunchControl, { props: { state: current, now, busy: false } });

  it("offers to go to lunch with the limit", async () => {
    const wrapper = control(state());

    expect(wrapper.text()).toContain("Лимит — 45 мин. Отменить отметку можно в первые 5 мин.");
    await wrapper.get("button").trigger("click");
    expect(wrapper.emitted("start")).toHaveLength(1);
  });

  it("counts down an ongoing lunch with undo in the first minutes", async () => {
    const wrapper = control(state({ today: lunch(), can_start: false, undo_until: iso(5) }), at(3));
    const buttons = wrapper.findAll("button");

    expect(wrapper.get("[role=timer]").text()).toBe("42:00");
    expect(wrapper.get("[role=timer]").classes()).toContain("control__clock--ok");
    expect(wrapper.text()).toContain("Ушли в 12:00 · вернуться до 12:45");
    expect(buttons[1].text()).toContain("02:00");
    await buttons[0].trigger("click");
    await buttons[1].trigger("click");
    expect(wrapper.emitted("finish")).toHaveLength(1);
    expect(wrapper.emitted("undo")).toHaveLength(1);
  });

  it("warns in yellow during the last five minutes", () => {
    const wrapper = control(state({ today: lunch(), can_start: false }), at(41));

    expect(wrapper.get("[role=timer]").classes()).toContain("control__clock--attention");
  });

  it("shows overrun in red and hides undo once its time is over", () => {
    const wrapper = control(state({ today: lunch(), can_start: false, undo_until: iso(5) }), at(47));

    expect(wrapper.get("[role=timer]").text()).toBe("Превышение +2 мин");
    expect(wrapper.get("[role=timer]").classes()).toContain("control__clock--alarm");
    expect(wrapper.findAll("button")).toHaveLength(1);
  });

  it("summarises a finished lunch", () => {
    const finished = lunch({ ended_at: iso(40), status: "on_time", duration_seconds: 2400 });
    const wrapper = control(state({ today: finished, can_start: false }));

    expect(wrapper.text()).toContain("Сегодня обед уже отмечен");
    expect(wrapper.text()).toContain("12:00–12:40 · 40 мин");
    expect(wrapper.text()).toContain("В пределах лимита");
    expect(wrapper.find("button").exists()).toBe(false);
  });

  it("explains why lunch cannot be marked", () => {
    const untracked = control(state({ tracked: false, can_start: false, refusal: "Ваши обеды не учитываются — отмечать их не нужно" }));
    const dayOff = control(state({ can_start: false, refusal: "Сегодня нерабочий день" }));

    expect(untracked.text()).toContain("Если это ошибка — обратитесь к администратору");
    expect(dayOff.text()).toContain("Сегодня нерабочий день");
    expect(dayOff.find("button").exists()).toBe(false);
  });
});

describe("LunchPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useSession().me = me("employee");
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(routes: Record<string, [number, unknown]>) {
    const spy = routeFetch({ "/api/lunch/history": [200, history()], ...routes });
    const wrapper = mount(LunchPage);
    await flushPromises();
    return { spy, wrapper };
  }

  it("greets the user and marks the start of lunch", async () => {
    const { spy, wrapper } = await mounted({ "/api/lunch/me": [200, state()], "/api/lunch/start": [200, state({ today: lunch(), can_start: false })] });

    expect(wrapper.text()).toContain("Здравствуйте, Петрова Анна");
    await wrapper.get(".control button").trigger("click");
    await flushPromises();

    expect(wasRequested(spy, "/api/lunch/start", "POST")).toBe(true);
    expect(wrapper.get("[role=timer]").text()).toBe("45:00");
    expect(useToasts().items.map((toast) => toast.text)).toContain("Приятного аппетита! Время пошло");
  });

  it("shows the server refusal and reloads the state", async () => {
    const { spy, wrapper } = await mounted({ "/api/lunch/me": [200, state()], "/api/lunch/start": [409, { detail: "Сегодня обед уже был" }] });

    await wrapper.get(".control button").trigger("click");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Сегодня обед уже был");
    expect(spy.mock.calls.filter(([url]) => url === "/api/lunch/me")).toHaveLength(2);
  });

  it("offers a retry when the state cannot be loaded", async () => {
    const { wrapper } = await mounted({ "/api/lunch/me": [500, { detail: "Ошибка" }] });

    expect(wrapper.text()).toContain("Не удалось загрузить обед");
    expect(wrapper.text()).toContain("Повторить");
  });

  it("shows the month history with summary and corrections", async () => {
    const corrected = lunch({
      id: 2,
      day: "2026-10-07",
      started_at: "2026-10-07T09:00:00Z",
      ended_at: "2026-10-07T09:50:00Z",
      status: "overrun",
      duration_seconds: 3000,
      correction: { by: "Кадрова Ольга", at: "2026-10-07T12:00:00Z", reason: "Забыл нажать", added: false },
    });
    const unreturned = lunch({ id: 3, day: "2026-10-06", ended_at: "2026-10-06T15:00:00Z", status: "unreturned", auto_closed: true });
    const month = history({ lunches: [corrected, unreturned], summary: { count: 2, violations: 2, average_minutes: 50 } });
    const { wrapper } = await mounted({ "/api/lunch/me": [200, state()], "/api/lunch/history": [200, month] });
    const rows = wrapper.findAll(".history__row");

    expect(wrapper.text()).toContain("Октябрь 2026");
    expect(wrapper.get(".history__tile--alarm").text()).toContain("2");
    expect(wrapper.text()).toContain("50 мин");
    expect(rows[0].text()).toContain("12:00–12:50");
    expect(rows[0].text()).toContain("Превышение");
    expect(rows[0].text()).toContain("Исправлено: Кадрова Ольга, 07.10.2026, 15:00. Причина: Забыл нажать");
    expect(rows[1].text()).toContain("Возврат не отмечен");
    expect(rows[1].get(".history__duration").text()).toBe("—");
  });

  it("explains an empty month and moves to the previous one", async () => {
    const { spy, wrapper } = await mounted({
      "/api/lunch/me": [200, state()],
      "/api/lunch/history?month=2026-09": [200, history({ month: "2026-09" })],
    });
    const [previous, next] = wrapper.findAll(".history__months button");

    expect(wrapper.text()).toContain("В этом месяце обедов не отмечено");
    expect(next.attributes("disabled")).toBeDefined();
    await previous.trigger("click");
    await flushPromises();

    expect(wasRequested(spy, "/api/lunch/history?month=2026-09", "GET")).toBe(true);
    expect(wrapper.text()).toContain("Сентябрь 2026");
    expect(wrapper.findAll(".history__months button")[1].attributes("disabled")).toBeUndefined();
  });
});
