import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import AppShell from "../src/components/shell/AppShell.vue";
import { useLightMode } from "../src/composables/useLightMode";
import { reducedMotion, stillMotion } from "../src/device/motion";
import { useSession } from "../src/stores/session";
import { routeFetch } from "./helpers";
import { me } from "./people";

const replace = vi.fn();
vi.mock("vue-router", () => ({ useRouter: () => ({ replace }) }));

const FAREWELL_MS = 1000;
const UNFOLD_MS = 420;
const LOGOUT = { "/api/auth/logout": [200, {}], "/api/directory/public": [200, { enabled: false }], "/api/appearance": [200, { rabbit: false }] } as Record<string, [number, unknown]>;
const NavStub = defineComponent({ name: "SideNav", emits: ["logout", "openProfile"], template: "<nav class='nav-stub' />" });

function device(reduced: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({ matches: reduced && query.includes("reduced-motion"), addEventListener() {}, removeEventListener() {} }));
}

function shell() {
  useSession().me = me("employee");
  return mount(AppShell, { global: { stubs: { SideNav: NavStub, RouterView: true } } });
}

const logoutCalls = (spy: ReturnType<typeof routeFetch>) => spy.mock.calls.filter(([url]) => url === "/api/auth/logout").length;

beforeEach(() => {
  setActivePinia(createPinia());
  replace.mockReset();
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  useLightMode().choose("auto");
  localStorage.clear();
  window.history.replaceState(null, "");
});

describe("leaving the account", () => {
  it("folds the site into a grey exit badge, then signs out and opens the login page", async () => {
    device(false);
    const spy = routeFetch(LOGOUT);
    const wrapper = shell();

    wrapper.findComponent(NavStub).vm.$emit("logout");
    await flushPromises();

    expect(wrapper.get(".shell").classes()).toContain("shell--leaving");
    expect(wrapper.find(".farewell .auth-badge--farewell").exists()).toBe(true);
    expect(logoutCalls(spy)).toBe(0);

    await vi.advanceTimersByTimeAsync(FAREWELL_MS);

    expect(logoutCalls(spy)).toBe(1);
    expect(replace).toHaveBeenCalledWith({ name: "login", state: { farewell: true } });
  });

  it("ignores repeated presses while the farewell plays", async () => {
    device(false);
    const spy = routeFetch(LOGOUT);
    const wrapper = shell();

    wrapper.findComponent(NavStub).vm.$emit("logout");
    await flushPromises();
    wrapper.findComponent(NavStub).vm.$emit("logout");
    await vi.advanceTimersByTimeAsync(FAREWELL_MS * 2);

    expect(logoutCalls(spy)).toBe(1);
    expect(replace).toHaveBeenCalledTimes(1);
  });

  it("keeps the farewell in light mode, which only drops the heavy effects", async () => {
    device(false);
    useLightMode().choose("on");
    const spy = routeFetch(LOGOUT);
    const wrapper = shell();

    wrapper.findComponent(NavStub).vm.$emit("logout");
    await flushPromises();

    expect(wrapper.find(".farewell .auth-badge--farewell").exists()).toBe(true);
    expect(logoutCalls(spy)).toBe(0);

    await vi.advanceTimersByTimeAsync(FAREWELL_MS);

    expect(replace).toHaveBeenCalledWith({ name: "login", state: { farewell: true } });
  });

  it("leaves at once without the farewell on calm devices", async () => {
    device(true);
    const spy = routeFetch(LOGOUT);
    const wrapper = shell();

    wrapper.findComponent(NavStub).vm.$emit("logout");
    await flushPromises();

    expect(wrapper.find(".farewell").exists()).toBe(false);
    expect(logoutCalls(spy)).toBe(1);
    expect(replace).toHaveBeenCalledWith({ name: "login", state: { farewell: false } });
  });
});

describe("motion preferences", () => {
  it("lets light mode still the heavy rabbit but not the light animations", () => {
    device(false);
    useLightMode().choose("on");

    expect(stillMotion()).toBe(true);
    expect(reducedMotion()).toBe(false);
  });

  it("stills everything when the system asks for less motion", () => {
    device(true);

    expect(stillMotion()).toBe(true);
    expect(reducedMotion()).toBe(true);
  });
});

describe("login page after leaving", () => {
  async function loginPage() {
    const { default: LoginPage } = await import("../src/pages/LoginPage.vue");
    const wrapper = mount(LoginPage);
    await flushPromises();
    return wrapper;
  }

  it("unfolds the card out of the grey badge once and then stays still", async () => {
    device(false);
    routeFetch(LOGOUT);
    window.history.replaceState({ farewell: true }, "");
    const wrapper = await loginPage();

    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--return");
    expect(wrapper.get(".auth-badge--farewell").classes()).toEqual(expect.arrayContaining(["auth-badge--leaving", "auth__badge--screen"]));
    expect(window.history.state.farewell).toBe(false);

    await vi.advanceTimersByTimeAsync(UNFOLD_MS);

    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--idle");
    expect(wrapper.find(".auth-badge").exists()).toBe(false);
  });

  it("shows the card plainly when opened directly", async () => {
    device(false);
    routeFetch(LOGOUT);
    const wrapper = await loginPage();

    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--idle");
    expect(wrapper.find(".auth-badge").exists()).toBe(false);
  });
});
