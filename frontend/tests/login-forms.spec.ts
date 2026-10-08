import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ChangePasswordForm from "../src/components/login/ChangePasswordForm.vue";
import LoginForm from "../src/components/login/LoginForm.vue";
import { mockFetch, sentBody } from "./helpers";
import { me } from "./people";

function fill(wrapper: ReturnType<typeof mount>, values: string[]) {
  const inputs = wrapper.findAll("input");
  return Promise.all(values.map((value, index) => inputs[index].setValue(value)));
}

describe("LoginForm", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => vi.unstubAllGlobals());

  it("asks for both fields before calling the server", async () => {
    const spy = mockFetch(200, {});
    const wrapper = mount(LoginForm);

    await wrapper.get("form").trigger("submit");

    expect(wrapper.get('[role="alert"]').text()).toBe("Введите логин и пароль");
    expect(spy).not.toHaveBeenCalled();
  });

  it("sends credentials and reports success", async () => {
    const spy = mockFetch(200, me("employee"));
    const wrapper = mount(LoginForm);
    await fill(wrapper, ["ivanov.ii", "secret-password"]);

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(sentBody(spy)).toEqual({ login: "ivanov.ii", password: "secret-password" });
    expect(wrapper.emitted("success")).toHaveLength(1);
  });

  it("shows the server message on failure", async () => {
    mockFetch(401, { detail: "Неверный логин или пароль" });
    const wrapper = mount(LoginForm);
    await fill(wrapper, ["ivanov.ii", "wrong-password"]);

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toBe("Неверный логин или пароль");
    expect(wrapper.emitted("success")).toBeUndefined();
  });

  it("reveals where to get help", async () => {
    const wrapper = mount(LoginForm);

    await wrapper.get("button.login-form__link").trigger("click");

    expect(wrapper.text()).toContain("Обратитесь к администратору системы");
  });
});

describe("ChangePasswordForm", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => vi.unstubAllGlobals());

  it("asks the current password when changing it from the profile", async () => {
    const spy = mockFetch(200, me("admin"));
    const wrapper = mount(ChangePasswordForm, { props: { askCurrent: true } });
    expect(wrapper.findAll("input")).toHaveLength(3);
    await fill(wrapper, ["old-password-1", "new-password-1", "new-password-1"]);

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(sentBody(spy)).toEqual({ new_password: "new-password-1", current_password: "old-password-1" });
  });

  it("has no old password field on the forced change", () => {
    const wrapper = mount(ChangePasswordForm);

    expect(wrapper.findAll("input")).toHaveLength(2);
    expect(wrapper.text()).not.toContain("Текущий пароль");
  });

  it("rejects mismatched passwords before calling the server", async () => {
    const spy = mockFetch(200, {});
    const wrapper = mount(ChangePasswordForm);
    await fill(wrapper, ["new-password-1", "new-password-2"]);

    await wrapper.get("form").trigger("submit");

    expect(wrapper.get('[role="alert"]').text()).toBe("Пароли не совпадают");
    expect(spy).not.toHaveBeenCalled();
  });

  it("sends the change and reports success", async () => {
    const spy = mockFetch(200, me("admin"));
    const wrapper = mount(ChangePasswordForm);
    await fill(wrapper, ["new-password-1", "new-password-1"]);

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(sentBody(spy)).toEqual({ new_password: "new-password-1" });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });
});
