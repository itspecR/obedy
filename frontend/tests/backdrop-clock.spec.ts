import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { arcOf, hourAngle, minuteAngle, turnTowards, wallTime } from "../src/clock/dial";
import BackdropClock from "../src/components/ui/BackdropClock.vue";
import { routeFetch } from "./helpers";

const MOSCOW = "Europe/Moscow";
const HALF_PAST_ONE_IN_MOSCOW = "2026-10-12T10:30:00Z";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("clock dial math", () => {
  it("reads the wall time in the server's zone, not the device's", () => {
    expect(wallTime(Date.parse(HALF_PAST_ONE_IN_MOSCOW), MOSCOW)).toEqual({ hours: 13, minutes: 30 });
    expect(wallTime(Date.parse("2026-10-12T21:05:00Z"), MOSCOW)).toEqual({ hours: 0, minutes: 5 });
  });

  it("turns the hour hand between the marks and the minute hand by six degrees a minute", () => {
    expect(hourAngle({ hours: 13, minutes: 30 })).toBe(45);
    expect(hourAngle({ hours: 0, minutes: 0 })).toBe(0);
    expect(minuteAngle({ hours: 13, minutes: 30 })).toBe(180);
    expect(minuteAngle({ hours: 13, minutes: 59 })).toBe(354);
  });

  it("always takes the short way round, so the hour change never spins the hand backwards", () => {
    expect(turnTowards(354, 0)).toBe(360);
    expect(turnTowards(360, 6)).toBe(366);
    expect(turnTowards(10, 350)).toBe(-10);
    expect(turnTowards(45, 45)).toBe(45);
  });

  it("spans the lunch window on the twelve-hour dial", () => {
    expect(arcOf({ hours: 12, minutes: 30 }, { hours: 14, minutes: 0 })).toEqual({ start: 15, end: 60 });
    expect(arcOf({ hours: 11, minutes: 0 }, { hours: 15, minutes: 0 })).toEqual({ start: 330, end: 450 });
  });
});

describe("BackdropClock", () => {
  const turn = (style: string | undefined) => (((Number(/rotate\((-?[\d.]+)deg\)/.exec(style ?? "")?.[1]) % 360) + 360) % 360);

  async function clock(response: [number, unknown]) {
    routeFetch({ "/api/clock": response });
    const wrapper = mount(BackdropClock);
    await flushPromises();
    return wrapper;
  }

  it("shows the server's Moscow time and the lunch window from the rules", async () => {
    const wrapper = await clock([200, { server_time: HALF_PAST_ONE_IN_MOSCOW, time_zone: MOSCOW, lunch_window: { start: "12:30:00", end: "14:00:00" } }]);
    const [hour, minute] = wrapper.findAll(".backdrop-clock__hand");

    expect(turn(hour.attributes("style"))).toBe(45);
    expect(turn(minute.attributes("style"))).toBe(180);
    expect(wrapper.find(".backdrop-clock__window").exists()).toBe(true);
    expect(wrapper.attributes("aria-hidden")).toBe("true");
    wrapper.unmount();
  });

  it("draws no lunch arc when the window is switched off", async () => {
    const wrapper = await clock([200, { server_time: HALF_PAST_ONE_IN_MOSCOW, time_zone: MOSCOW, lunch_window: null }]);

    expect(wrapper.find(".backdrop-clock__window").exists()).toBe(false);
    wrapper.unmount();
  });

  it("keeps ticking on the device clock when the server cannot be asked", async () => {
    const wrapper = await clock([503, { detail: "Сервер недоступен" }]);

    expect(wrapper.findAll(".backdrop-clock__hand")).toHaveLength(2);
    expect(wrapper.find(".backdrop-clock__window").exists()).toBe(false);
    wrapper.unmount();
  });
});
