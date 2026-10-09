import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, nextTick } from "vue";
import LoginRabbit from "../src/components/login/LoginRabbit.vue";
import { FILL_MS, nextPhase } from "../src/components/login/rabbitPlot";
import RabbitSprite from "../src/components/rabbit/RabbitSprite.vue";
import { frameUrl } from "../src/rabbit/frames";
import { SCENES, frameAt, sceneEnded, sceneLength, type SceneName } from "../src/rabbit/scenes";
import { routeFetch } from "./helpers";
import { me } from "./people";

const replace = vi.fn();
vi.mock("vue-router", () => ({ useRouter: () => ({ replace }) }));

const TICK_MS = 1000 / 24;

function animationFrames() {
  let now = 0;
  const queue = new Map<number, FrameRequestCallback>();
  let id = 0;
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    queue.set(++id, callback);
    return id;
  });
  vi.stubGlobal("cancelAnimationFrame", (handle: number) => queue.delete(handle));
  return {
    advance(ms: number) {
      const steps = Math.ceil(ms / 16);
      for (let i = 0; i < steps; i += 1) {
        now += 16;
        const callbacks = [...queue.values()];
        queue.clear();
        callbacks.forEach((callback) => callback(now));
      }
    },
  };
}

const SpriteStub = defineComponent({ name: "RabbitSprite", props: ["scene", "speed", "repeat"], emits: ["ended"], template: "<i :data-scene='scene' :data-repeat='repeat' />" });

beforeEach(() => {
  setActivePinia(createPinia());
  replace.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("rabbit scenes", () => {
  it("holds each frame for its number of ticks", () => {
    const scene = { holds: [2, 1, 3], loop: false };

    expect([0, 1, 2, 3, 5, 9].map((tick) => frameAt(scene, tick))).toEqual([1, 1, 2, 3, 3, 3]);
    expect(sceneLength(scene)).toBe(6);
    expect([sceneEnded(scene, 5), sceneEnded(scene, 6)]).toEqual([false, true]);
  });

  it("wraps looping scenes and never ends them", () => {
    const scene = { holds: [2, 2], loop: true };

    expect([0, 3, 4, 7].map((tick) => frameAt(scene, tick))).toEqual([1, 2, 1, 2]);
    expect(sceneEnded(scene, 100)).toBe(false);
  });

  it("has a picture for every frame of every scene", () => {
    for (const [name, scene] of Object.entries(SCENES)) {
      scene.holds.forEach((_, index) => expect(frameUrl(name as SceneName, index + 1), `${name} ${index + 1}`).not.toBe(""));
    }
  });
});

describe("login plot", () => {
  it("taps until the server answers, then runs into the hole or stumbles", () => {
    expect(nextPhase("appear", "pending")).toBe("tap");
    expect(nextPhase("tap", "pending")).toBe("tap");
    expect(["start", "run", "dive", "fill"].map((phase) => nextPhase(phase as never, "success"))).toEqual(["run", "dive", "fill", null]);
    expect(nextPhase("tap", "success")).toBe("start");
    expect(nextPhase("tap", "failure")).toBe("stumble");
    expect(nextPhase("stumble", "failure")).toBeNull();
  });
});

describe("RabbitSprite", () => {
  it("plays the frames at 24 per second and reports the end", async () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "dive" } });
    const first = wrapper.get("img").attributes("src");

    frames.advance(TICK_MS * SCENES.dive.holds[0] + 40);
    await nextTick();
    expect(wrapper.get("img").attributes("src")).not.toBe(first);

    frames.advance(TICK_MS * sceneLength(SCENES.dive));
    await nextTick();
    expect(wrapper.emitted("ended")).toEqual([["dive"]]);
    expect(wrapper.get("img").attributes("src")).toBe(frameUrl("dive", SCENES.dive.holds.length));
  });

  it("starts over while asked to repeat", () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "tap", repeat: true } });

    frames.advance(TICK_MS * sceneLength(SCENES.tap) * 2 + 40);

    expect(wrapper.emitted("ended")?.length).toBe(2);
  });
});

describe("LoginRabbit", () => {
  function rabbit(outcome: "pending" | "success" | "failure") {
    vi.useFakeTimers();
    return mount(LoginRabbit, { props: { outcome }, global: { stubs: { RabbitSprite: SpriteStub } } });
  }

  const shown = (wrapper: ReturnType<typeof rabbit>) => wrapper.find("i").attributes("data-scene");
  const end = async (wrapper: ReturnType<typeof rabbit>) => {
    wrapper.findComponent(SpriteStub).vm.$emit("ended");
    await flushPromises();
  };

  it("keeps tapping the watch while the server thinks", async () => {
    const wrapper = rabbit("pending");
    await vi.advanceTimersByTimeAsync(250);

    expect(wrapper.find("i").attributes("data-repeat")).toBe("true");
    await end(wrapper);
    expect(shown(wrapper)).toBe("tap");
  });

  it("runs to the hole, dives, fills the screen from it and finishes", async () => {
    const wrapper = rabbit("success");
    await vi.advanceTimersByTimeAsync(250);

    await end(wrapper);
    expect(shown(wrapper)).toBe("start");
    expect(wrapper.get(".login-rabbit__hole").classes()).toContain("login-rabbit__hole--open");
    await end(wrapper);
    expect(shown(wrapper)).toBe("run");
    await vi.advanceTimersByTimeAsync(450);
    expect(shown(wrapper)).toBe("dive");
    await end(wrapper);

    expect(wrapper.emitted("fill")).toHaveLength(1);
    expect(wrapper.emitted("done")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(FILL_MS);
    expect(wrapper.emitted("done")).toHaveLength(1);
  });

  it("stumbles and finishes on a wrong password", async () => {
    const wrapper = rabbit("failure");
    await vi.advanceTimersByTimeAsync(250);

    await end(wrapper);
    expect(shown(wrapper)).toBe("no");
    await end(wrapper);

    expect(wrapper.emitted("done")).toHaveLength(1);
    expect(wrapper.emitted("fill")).toBeUndefined();
  });
});

describe("LoginPage with the rabbit", () => {
  const DOMAIN_OFF = { "/api/directory/public": [200, { enabled: false }] } as Record<string, [number, unknown]>;
  const RabbitStub = defineComponent({ name: "LoginRabbit", props: ["outcome"], emits: ["fill", "done"], template: "<b class='rabbit-stub' :data-outcome='outcome' />" });

  function stillDevice(reduced: boolean) {
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: reduced && query.includes("reduced-motion"), addEventListener() {}, removeEventListener() {} }));
  }

  async function page(routes: Record<string, [number, unknown]>, reduced = false) {
    stillDevice(reduced);
    const spy = routeFetch({ ...DOMAIN_OFF, ...routes });
    const { default: LoginPage } = await import("../src/pages/LoginPage.vue");
    const wrapper = mount(LoginPage, { attachTo: document.body, global: { stubs: { LoginRabbit: RabbitStub } } });
    await flushPromises();
    const [login, password] = wrapper.findAll("input");
    await login.setValue("ivanov.ii");
    await password.setValue("secret-password");
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    return { spy, wrapper };
  }

  const RABBIT = { "/api/appearance": [200, { rabbit: true }] } as Record<string, [number, unknown]>;
  const RIGHT = { ...RABBIT, "/api/auth/login": [200, me("employee")] } as Record<string, [number, unknown]>;
  const WRONG = { ...RABBIT, "/api/auth/login": [401, { detail: "Неверный логин или пароль" }] } as Record<string, [number, unknown]>;

  it("opens the site only after the rabbit has fallen into the hole", async () => {
    const { wrapper } = await page(RIGHT);
    const stub = wrapper.findComponent(RabbitStub);

    expect(stub.attributes("data-outcome")).toBe("success");
    expect(wrapper.get(".login-form__submit-inner").classes()).toContain("login-form__submit-inner--melted");
    expect(wrapper.get(".login-form__submit").classes()).toContain("login-form__submit--shown");
    expect(wrapper.get('[role="status"]').text()).toBe("Вход выполнен");
    expect(replace).not.toHaveBeenCalled();

    stub.vm.$emit("fill", { x: 300, y: 400 });
    await flushPromises();
    expect(wrapper.get(".screen-fill").attributes("style")).toContain("left: 300px");

    stub.vm.$emit("done");
    await flushPromises();
    expect(replace).toHaveBeenCalledWith({ name: "home" });
    wrapper.unmount();
  });

  it("shakes the card after the rabbit stumbles on a wrong password", async () => {
    const { wrapper } = await page(WRONG);
    expect(wrapper.findComponent(RabbitStub).attributes("data-outcome")).toBe("failure");
    expect(wrapper.get(".auth__card").classes()).not.toContain("auth__card--error");

    wrapper.findComponent(RabbitStub).vm.$emit("done");
    await flushPromises();

    expect(wrapper.find(".rabbit-stub").exists()).toBe(false);
    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--error");
    wrapper.unmount();
  });

  it("keeps the usual animation when the rabbit is switched off", async () => {
    const { wrapper } = await page({ "/api/appearance": [200, { rabbit: false }], "/api/auth/login": [200, me("employee")] });

    expect(wrapper.find(".rabbit-stub").exists()).toBe(false);
    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--success");
    wrapper.unmount();
  });

  it("does not even ask about the rabbit when motion is reduced", async () => {
    const { spy, wrapper } = await page(RIGHT, true);

    expect(wrapper.find(".rabbit-stub").exists()).toBe(false);
    expect(spy.mock.calls.some(([url]) => url === "/api/appearance")).toBe(false);
    wrapper.unmount();
  });
});
