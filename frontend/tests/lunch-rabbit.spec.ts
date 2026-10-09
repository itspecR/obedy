import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import type { Lunch, LunchState } from "../src/api/lunch";
import { lunchProgress } from "../src/components/lunch/countdown";
import LunchControl from "../src/components/lunch/LunchControl.vue";
import LunchRabbit from "../src/components/lunch/LunchRabbit.vue";
import { useToasts } from "../src/composables/useToasts";
import LunchPage from "../src/pages/LunchPage.vue";
import { useSession } from "../src/stores/session";
import { routeFetch } from "./helpers";
import { me } from "./people";

const NOON = "2026-10-08T09:00:00Z";
const at = (minutes: number) => Date.parse(NOON) + minutes * 60_000;
const iso = (minutes: number) => new Date(at(minutes)).toISOString();

function lunch(overrides: Partial<Lunch> = {}): Lunch {
  return { id: 1, day: "2026-10-08", started_at: NOON, ended_at: null, limit_minutes: 40, status: "ongoing", duration_seconds: 0, auto_closed: false, correction: null, ...overrides };
}

function state(overrides: Partial<LunchState> = {}): LunchState {
  return { server_time: NOON, tracked: true, limit_minutes: 40, warning_minutes: 5, undo_seconds: 300, today: null, can_start: true, refusal: "", undo_until: null, ...overrides };
}

const SpriteStub = defineComponent({ name: "RabbitSprite", props: ["scene", "speed", "still", "repeat"], emits: ["ended"], template: "<i :data-scene='scene' :data-still='still' />" });
const stubs = { RabbitSprite: SpriteStub };

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("lunch progress", () => {
  it("is the share of the limit that has passed, kept between start and hole", () => {
    expect(lunchProgress(NOON, 40, at(10))).toBe(0.25);
    expect(lunchProgress(NOON, 40, at(-1))).toBe(0);
    expect(lunchProgress(NOON, 40, at(55))).toBe(1);
  });
});

describe("LunchRabbit", () => {
  const rabbit = (props: Partial<{ progress: number; fresh: boolean; still: boolean; parting: boolean }> = {}) =>
    mount(LunchRabbit, { props: { progress: 0.5, fresh: false, still: false, parting: false, ...props }, global: { stubs } });
  const scene = (wrapper: ReturnType<typeof rabbit>) => wrapper.get("i").attributes("data-scene");
  const end = async (wrapper: ReturnType<typeof rabbit>) => {
    wrapper.findComponent(SpriteStub).vm.$emit("ended");
    await flushPromises();
  };

  it("stands on its share of the path and runs when the page opens mid-lunch", () => {
    const wrapper = rabbit({ progress: 0.25 });

    expect(scene(wrapper)).toBe("run");
    expect(wrapper.get(".lunch-rabbit__runner").attributes("style")).toContain("* 0.25)");
  });

  it("appears from the button, starts and then runs after going to lunch", async () => {
    vi.useFakeTimers();
    const wrapper = rabbit({ fresh: true, progress: 0 });

    expect(wrapper.get(".lunch-rabbit__body").classes()).toContain("lunch-rabbit__body--appear");
    await vi.advanceTimersByTimeAsync(250);
    expect(scene(wrapper)).toBe("start");
    await end(wrapper);
    expect(scene(wrapper)).toBe("run");
  });

  it("nods, closes the hole and melts away after an on-time return", async () => {
    vi.useFakeTimers();
    const wrapper = rabbit();

    await wrapper.setProps({ parting: true });
    expect(scene(wrapper)).toBe("ontime");
    expect(wrapper.get(".lunch-rabbit__hole").classes()).not.toContain("rabbit-hole--open");
    await end(wrapper);
    expect(wrapper.get(".lunch-rabbit__body").classes()).toContain("lunch-rabbit__body--vanish");
    expect(wrapper.emitted("parted")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(350);
    expect(wrapper.emitted("parted")).toHaveLength(1);
  });

  it("stays still on calm devices and leaves at once", async () => {
    const wrapper = rabbit({ still: true, fresh: true });

    expect(scene(wrapper)).toBe("run");
    expect(wrapper.get("i").attributes("data-still")).toBe("true");
    await wrapper.setProps({ parting: true });
    expect(wrapper.emitted("parted")).toHaveLength(1);
  });
});

describe("LunchControl with the rabbit", () => {
  const view = { fresh: false, still: false, parting: false };

  it("shows the rabbit only while on lunch and only when it is switched on", () => {
    const ongoing = state({ today: lunch(), can_start: false });

    expect(mount(LunchControl, { props: { state: ongoing, now: at(10), busy: false, rabbit: view }, global: { stubs } }).find(".lunch-rabbit").exists()).toBe(true);
    expect(mount(LunchControl, { props: { state: ongoing, now: at(10), busy: false, rabbit: null }, global: { stubs } }).find(".lunch-rabbit").exists()).toBe(false);
    expect(mount(LunchControl, { props: { state: state(), now: at(10), busy: false, rabbit: view }, global: { stubs } }).find(".lunch-rabbit").exists()).toBe(false);
  });

  it("says goodbye where the rabbit stopped when the employee came back in time", () => {
    const back = state({ today: lunch({ ended_at: iso(30), status: "on_time", duration_seconds: 1800 }), can_start: false });
    const wrapper = mount(LunchControl, { props: { state: back, now: at(31), busy: false, rabbit: { ...view, parting: true } }, global: { stubs } });

    expect(wrapper.text()).toContain("Вы вернулись вовремя");
    expect(wrapper.get(".lunch-rabbit__runner").attributes("style")).toContain("* 0.75)");
  });
});

describe("LunchPage with the rabbit", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useSession().me = me("employee");
  });
  afterEach(() => {
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(routes: Record<string, [number, unknown]>, rabbit = true) {
    routeFetch({ "/api/lunch/history": [200, { month: "2026-10", lunches: [], summary: { count: 0, violations: 0, average_minutes: null } }], "/api/appearance": [200, { rabbit }], ...routes });
    const wrapper = mount(LunchPage, { global: { stubs } });
    await flushPromises();
    return wrapper;
  }

  it("lets the rabbit out of the button when going to lunch", async () => {
    const wrapper = await mounted({ "/api/lunch/me": [200, state()], "/api/lunch/start": [200, state({ today: lunch(), can_start: false })] });

    await wrapper.get(".control button").trigger("click");
    await flushPromises();

    expect(wrapper.get(".lunch-rabbit__body").classes()).toContain("lunch-rabbit__body--appear");
  });

  it("plays the goodbye only for an on-time return and then shows the summary", async () => {
    const back = state({ today: lunch({ ended_at: iso(30), status: "on_time", duration_seconds: 1800 }), can_start: false });
    const wrapper = await mounted({ "/api/lunch/me": [200, state({ today: lunch(), can_start: false })], "/api/lunch/finish": [200, back] });

    await wrapper.get(".control__main").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Вы вернулись вовремя");

    wrapper.findComponent(LunchRabbit).vm.$emit("parted");
    await flushPromises();
    expect(wrapper.text()).toContain("Сегодня обед уже отмечен");
  });

  it("skips the goodbye after an overrun", async () => {
    const late = state({ today: lunch({ ended_at: iso(50), status: "overrun", duration_seconds: 3000 }), can_start: false });
    const wrapper = await mounted({ "/api/lunch/me": [200, state({ today: lunch(), can_start: false })], "/api/lunch/finish": [200, late] });

    await wrapper.get(".control__main").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Сегодня обед уже отмечен");
    expect(wrapper.find(".lunch-rabbit").exists()).toBe(false);
  });

  it("shows no rabbit when it is switched off", async () => {
    const wrapper = await mounted({ "/api/lunch/me": [200, state({ today: lunch(), can_start: false })] }, false);

    expect(wrapper.find(".lunch-rabbit").exists()).toBe(false);
  });
});
