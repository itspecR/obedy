import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LoginForm from "../src/components/login/LoginForm.vue";
import { bodySentTo, routeFetch } from "./helpers";
import { me } from "./people";

const replace = vi.fn();
vi.mock("vue-router", () => ({ useRouter: () => ({ replace }) }));

const autofill = vi.hoisted(() => ({ filled: false }));
vi.mock("../src/components/login/autofill", () => ({ isAutofilled: () => autofill.filled }));

const DOMAIN_OFF = { "/api/directory/public": [200, { enabled: false }] } as Record<string, [number, unknown]>;
const WRONG = { ...DOMAIN_OFF, "/api/auth/login": [401, { detail: "Неверный логин или пароль" }] } as Record<string, [number, unknown]>;
const RIGHT = { ...DOMAIN_OFF, "/api/auth/login": [200, me("employee")] } as Record<string, [number, unknown]>;

function submitArea(wrapper: ReturnType<typeof mount>) {
  return wrapper.get(".login-form__submit");
}

function shown(wrapper: ReturnType<typeof mount>): boolean {
  return submitArea(wrapper).classes().includes("login-form__submit--shown") && submitArea(wrapper).attributes("inert") === undefined;
}

async function typeIn(wrapper: ReturnType<typeof mount>, login: string, password: string): Promise<void> {
  const [loginInput, passwordInput] = wrapper.findAll("input");
  await loginInput.setValue(login);
  await passwordInput.setValue(password);
}

beforeEach(() => {
  setActivePinia(createPinia());
  replace.mockReset();
  autofill.filled = false;
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("login button", () => {
  it("appears only once the password is being typed", async () => {
    routeFetch(DOMAIN_OFF);
    const wrapper = mount(LoginForm);
    await wrapper.findAll("input")[0].setValue("ivanov.ii");
    expect(shown(wrapper)).toBe(false);

    await wrapper.findAll("input")[1].setValue("s");

    expect(shown(wrapper)).toBe(true);
  });

  it("appears when the browser fills the saved password", async () => {
    vi.useFakeTimers();
    routeFetch(DOMAIN_OFF);
    autofill.filled = true;
    const wrapper = mount(LoginForm);

    await vi.advanceTimersByTimeAsync(600);

    expect(shown(wrapper)).toBe(true);
    wrapper.unmount();
  });

  it("sends a password the browser filled without an input event", async () => {
    const spy = routeFetch(RIGHT);
    const wrapper = mount(LoginForm, { attachTo: document.body });
    const [loginInput, passwordInput] = wrapper.findAll("input").map((input) => input.element as HTMLInputElement);
    loginInput.value = "ivanov.ii";
    passwordInput.value = "saved-password";

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, "/api/auth/login")).toEqual({ login: "ivanov.ii", password: "saved-password" });
    wrapper.unmount();
  });
});

describe("wrong password", () => {
  it("warns, marks and clears the password and puts the cursor back", async () => {
    routeFetch(WRONG);
    const wrapper = mount(LoginForm, { attachTo: document.body });
    await typeIn(wrapper, "ivanov.ii", "wrong-password");

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    const password = wrapper.findAll("input")[1];
    expect(wrapper.emitted("failure")).toHaveLength(1);
    expect(wrapper.get('[role="alert"]').text()).toBe("Неверный логин или пароль");
    expect((password.element as HTMLInputElement).value).toBe("");
    expect(password.attributes("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(password.element);
    expect(shown(wrapper)).toBe(false);

    await password.setValue("n");

    expect(password.attributes("aria-invalid")).toBeUndefined();
    wrapper.unmount();
  });
});

describe("LoginPage", () => {
  async function page() {
    const { default: LoginPage } = await import("../src/pages/LoginPage.vue");
    return mount(LoginPage, { attachTo: document.body });
  }

  it("shakes the card on a wrong password and calms down after", async () => {
    routeFetch(WRONG);
    const wrapper = await page();
    await typeIn(wrapper, "ivanov.ii", "wrong-password");
    vi.useFakeTimers();

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--error");
    await vi.advanceTimersByTimeAsync(450);
    expect(wrapper.get(".auth__card").classes()).not.toContain("auth__card--error");
    wrapper.unmount();
  });

  it("folds into a checkmark and opens the site after the animation", async () => {
    routeFetch(RIGHT);
    const wrapper = await page();
    await typeIn(wrapper, "ivanov.ii", "secret-password");
    vi.useFakeTimers();

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.get(".auth__card").classes()).toContain("auth__card--success");
    expect(wrapper.get('[role="status"]').text()).toBe("Вход выполнен");
    await vi.advanceTimersByTimeAsync(1000);
    expect(replace).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(100);
    expect(replace).toHaveBeenCalledWith({ name: "home" });
    wrapper.unmount();
  });
});
