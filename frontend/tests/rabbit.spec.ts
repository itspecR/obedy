import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, nextTick } from "vue";
import LoginRabbit from "../src/components/login/LoginRabbit.vue";
import { FILL_MS, nextPhase } from "../src/components/login/rabbitPlot";
import RabbitSprite from "../src/components/rabbit/RabbitSprite.vue";
import ButtonMorph from "../src/components/rabbit/ButtonMorph.vue";
import { frameUrl } from "../src/rabbit/frames";
import { MORPH_MS, SWAP_IN, SWAP_OUT, bodyOf } from "../src/rabbit/morph";
import { SCENES, frameAt, sceneEnded, sceneFrames, sceneLength, type SceneName } from "../src/rabbit/scenes";
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

const BUTTON = { left: 20, top: 300, width: 280, height: 48 };

const SpriteStub = defineComponent({ name: "RabbitSprite", props: ["scene", "speed", "repeat", "still"], emits: ["ended"], template: "<i :data-scene='scene' :data-repeat='repeat' :data-still='still' />" });

enableAutoUnmount(afterEach);

beforeEach(() => {
  setActivePinia(createPinia());
  replace.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("rabbit scenes", () => {
  it("holds each frame for its number of ticks and may return to an earlier frame", () => {
    const scene = { steps: [[1, 2], [2, 1], [3, 3], [1, 2]] as [number, number][], loop: false };

    expect([0, 1, 2, 3, 5, 6, 7, 20].map((tick) => frameAt(scene, tick))).toEqual([1, 1, 2, 3, 3, 1, 1, 1]);
    expect(sceneLength(scene)).toBe(8);
    expect(sceneFrames(scene)).toEqual([1, 2, 3]);
    expect([sceneEnded(scene, 7), sceneEnded(scene, 8)]).toEqual([false, true]);
  });

  it("wraps looping scenes and never ends them", () => {
    const scene = { steps: [[1, 2], [2, 2]] as [number, number][], loop: true };

    expect([0, 3, 4, 7].map((tick) => frameAt(scene, tick))).toEqual([1, 2, 1, 2]);
    expect(sceneEnded(scene, 100)).toBe(false);
  });

  it("has a picture for every frame of every scene", () => {
    for (const [name, scene] of Object.entries(SCENES)) {
      sceneFrames(scene).forEach((frame) => expect(frameUrl(name as SceneName, frame), `${name} ${frame}`).not.toBe(""));
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
    expect(nextPhase("stumble", "failure")).toBe("melt");
    expect(nextPhase("melt", "failure")).toBeNull();
  });
});

describe("RabbitSprite", () => {
  it("plays the frames at 24 per second and reports the end", async () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "dive" } });
    const first = wrapper.get("img").attributes("src");

    frames.advance(TICK_MS * SCENES.dive.steps[0][1] + 40);
    await nextTick();
    expect(wrapper.get("img").attributes("src")).not.toBe(first);

    frames.advance(TICK_MS * sceneLength(SCENES.dive));
    await nextTick();
    expect(wrapper.emitted("ended")).toEqual([["dive"]]);
    expect(wrapper.get("img").attributes("src")).toBe(frameUrl("dive", SCENES.dive.steps[SCENES.dive.steps.length - 1][0]));
  });

  it("fades between poses in slow scenes", async () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "tap" } });
    expect(wrapper.findAll("img")).toHaveLength(1);

    frames.advance(TICK_MS * SCENES.tap.steps[0][1] + 40);
    await nextTick();

    const [previous, current] = wrapper.findAll("img");
    expect(previous.attributes("src")).toBe(frameUrl("tap", 1));
    expect(current.classes()).toContain("rabbit-sprite__frame--blend");
  });

  it("cuts sharply between running frames", async () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "run" } });

    frames.advance(TICK_MS * SCENES.run.steps[0][1] + 40);
    await nextTick();

    expect(wrapper.findAll("img")).toHaveLength(1);
  });

  it("holds the first pose while told to stay still and plays once released", async () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "tap", still: true } });

    frames.advance(TICK_MS * sceneLength(SCENES.tap));
    expect(wrapper.emitted("ended")).toBeUndefined();

    await wrapper.setProps({ still: false });
    frames.advance(TICK_MS * sceneLength(SCENES.tap) + 40);
    expect(wrapper.emitted("ended")).toEqual([["tap"]]);
  });

  it("starts over while asked to repeat", () => {
    const frames = animationFrames();
    const wrapper = mount(RabbitSprite, { props: { scene: "tap", repeat: true } });

    frames.advance(TICK_MS * sceneLength(SCENES.tap) * 2 + 40);

    expect(wrapper.emitted("ended")?.length).toBe(2);
  });
});

describe("ButtonMorph", () => {
  const RABBIT_BOX = { left: 0, top: 0, width: 200, height: 200 };

  function morph(direction: "in" | "out") {
    vi.useFakeTimers();
    return mount(ButtonMorph, { props: { from: BUTTON, to: RABBIT_BOX, frame: "frame.webp", direction, duration: MORPH_MS } });
  }

  it("shows the rabbit at the peak of the silhouette and then finishes", async () => {
    const wrapper = morph("in");
    expect(document.body.querySelector(".button-morph__ghost")?.getAttribute("src")).toBe("frame.webp");

    await vi.advanceTimersByTimeAsync(MORPH_MS * SWAP_IN - 10);
    expect(wrapper.emitted("swap")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(20);
    expect(wrapper.emitted("swap")).toHaveLength(1);
    expect(wrapper.emitted("done")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(MORPH_MS);
    expect(wrapper.emitted("done")).toHaveLength(1);
    wrapper.unmount();
    expect(document.body.querySelector(".button-morph")).toBeNull();
  });

  it("hides the rabbit earlier when it flows back into the button", async () => {
    const wrapper = morph("out");

    await vi.advanceTimersByTimeAsync(MORPH_MS * SWAP_OUT + 10);
    expect(wrapper.emitted("swap")).toHaveLength(1);
  });

  it("narrows the blob to the rabbit's body inside its frame", () => {
    const body = bodyOf(RABBIT_BOX);

    expect(body.left + body.width / 2).toBe(100);
    expect(body.width).toBeLessThan(RABBIT_BOX.width);
    expect(body.top + body.height).toBeLessThanOrEqual(RABBIT_BOX.height);
  });
});

describe("LoginRabbit", () => {
  function rabbit(outcome: "pending" | "success" | "failure", button = () => BUTTON) {
    vi.useFakeTimers();
    return mount(LoginRabbit, { props: { outcome, button }, global: { stubs: { RabbitSprite: SpriteStub } } });
  }

  const hidden = (wrapper: ReturnType<typeof rabbit>) => wrapper.get(".login-rabbit__body").classes().includes("login-rabbit__body--hidden");
  const morphs = () => document.body.querySelectorAll(".button-morph").length;

  const shown = (wrapper: ReturnType<typeof rabbit>) => wrapper.find("i").attributes("data-scene");
  const end = async (wrapper: ReturnType<typeof rabbit>) => {
    wrapper.findComponent(SpriteStub).vm.$emit("ended");
    await flushPromises();
  };

  it("grows out of the button before tapping the watch", async () => {
    const wrapper = rabbit("pending");
    await nextTick();
    expect(hidden(wrapper)).toBe(true);
    expect(morphs()).toBe(1);

    await vi.advanceTimersByTimeAsync(MORPH_MS * SWAP_IN + 10);
    expect(hidden(wrapper)).toBe(false);
    expect(wrapper.find("i").attributes("data-still")).toBe("true");

    await vi.advanceTimersByTimeAsync(MORPH_MS);
    expect(morphs()).toBe(0);
    expect(shown(wrapper)).toBe("tap");
    expect(wrapper.find("i").attributes("data-still")).toBe("false");
  });

  it("keeps tapping the watch while the server thinks", async () => {
    const wrapper = rabbit("pending");
    await vi.advanceTimersByTimeAsync(MORPH_MS);

    expect(wrapper.find("i").attributes("data-repeat")).toBe("true");
    await end(wrapper);
    expect(shown(wrapper)).toBe("tap");
  });

  it("runs to the hole, dives, fills the screen from it and finishes", async () => {
    const wrapper = rabbit("success");
    await vi.advanceTimersByTimeAsync(MORPH_MS);

    await end(wrapper);
    expect(shown(wrapper)).toBe("start");
    expect(wrapper.get(".login-rabbit__hole").classes()).toContain("rabbit-hole--open");
    await end(wrapper);
    expect(shown(wrapper)).toBe("run");
    await vi.advanceTimersByTimeAsync(450);
    expect(shown(wrapper)).toBe("dive");
    await end(wrapper);
    expect(wrapper.emitted("fill")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(450);

    expect(wrapper.emitted("fill")).toHaveLength(1);
    expect(wrapper.emitted("done")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(FILL_MS);
    expect(wrapper.emitted("done")).toHaveLength(1);
  });

  it("stumbles, flows back into the button and finishes on a wrong password", async () => {
    let button = BUTTON;
    const wrapper = rabbit("failure", () => button);
    await vi.advanceTimersByTimeAsync(MORPH_MS);

    await end(wrapper);
    expect(shown(wrapper)).toBe("no");
    button = { ...BUTTON, top: BUTTON.top + 40 };
    await end(wrapper);
    expect(morphs()).toBe(1);
    expect(wrapper.findComponent(ButtonMorph).props("from")).toEqual(button);
    expect(wrapper.emitted("done")).toBeUndefined();

    await vi.advanceTimersByTimeAsync(MORPH_MS * SWAP_OUT + 10);
    expect(hidden(wrapper)).toBe(true);
    await vi.advanceTimersByTimeAsync(MORPH_MS);

    expect(wrapper.emitted("done")).toHaveLength(1);
    expect(wrapper.emitted("fill")).toBeUndefined();
  });
});

describe("LoginPage with the rabbit", () => {
  const DOMAIN_OFF = { "/api/directory/public": [200, { enabled: false }] } as Record<string, [number, unknown]>;
  const RabbitStub = defineComponent({ name: "LoginRabbit", props: ["outcome", "button"], emits: ["fill", "done"], template: "<b class='rabbit-stub' :data-outcome='outcome' :data-measured='typeof button().width' />" });

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
    expect(stub.attributes("data-measured")).toBe("number");
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
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);

    wrapper.findComponent(RabbitStub).vm.$emit("done");
    await flushPromises();

    expect(wrapper.find(".rabbit-stub").exists()).toBe(false);
    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--error");
    expect(wrapper.get('[role="alert"]').text()).toContain("Неверный логин или пароль");
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
