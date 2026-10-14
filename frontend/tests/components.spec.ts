import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { nextTick } from "vue";
import ConfirmDialog from "../src/components/ui/ConfirmDialog.vue";
import AppButton from "../src/components/ui/AppButton.vue";
import TextField from "../src/components/ui/TextField.vue";
import ToastHost from "../src/components/ui/ToastHost.vue";
import { useConfirm } from "../src/composables/useConfirm";
import { useToasts } from "../src/composables/useToasts";

describe("AppButton", () => {
  it("reports pressed state to screen readers", () => {
    const wrapper = mount(AppButton, { props: { pressed: true }, slots: { default: "Фильтр" } });

    expect(wrapper.attributes("aria-pressed")).toBe("true");
  });

  it("has no aria-pressed when it is not a toggle", () => {
    const wrapper = mount(AppButton, { slots: { default: "Сохранить" } });

    expect(wrapper.attributes("aria-pressed")).toBeUndefined();
  });
});

describe("TextField", () => {
  it("links the label and marks the error", () => {
    const wrapper = mount(TextField, { props: { label: "Логин", error: "Неверный логин или пароль" } });
    const input = wrapper.get("input");

    expect(wrapper.get("label").attributes("for")).toBe(input.attributes("id"));
    expect(input.attributes("aria-invalid")).toBe("true");
    expect(wrapper.text()).toContain("Неверный логин или пароль");
  });

  it("updates the bound value", async () => {
    const wrapper = mount(TextField, { props: { label: "Логин", modelValue: "" } });

    await wrapper.get("input").setValue("ivanov.ii");

    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["ivanov.ii"]);
  });
});

describe("ToastHost", () => {
  it("announces errors as alerts with a close button", async () => {
    const wrapper = mount(ToastHost);
    const { fail, items, dismiss } = useToasts();
    fail("Ошибка сохранения");
    await nextTick();

    expect(wrapper.get('[role="alert"]').text()).toContain("Ошибка сохранения");
    expect(wrapper.find('[aria-label="Закрыть уведомление"]').exists()).toBe(true);
    items.forEach((toast) => dismiss(toast.id));
  });
});

describe("ConfirmDialog", () => {
  it("focuses the action button and cancels on Escape", async () => {
    const wrapper = mount(ConfirmDialog, { attachTo: document.body });
    const { ask } = useConfirm();
    const pending = ask({ title: "Удалить?", text: "Нельзя отменить.", action: "Удалить", danger: true });
    await nextTick();
    await nextTick();

    const action = wrapper.findAll("button").find((button) => button.text() === "Удалить");
    expect(document.activeElement).toBe(action?.element);
    expect(action?.classes()).toContain("button--danger");

    await wrapper.get(".overlay").trigger("keydown", { key: "Escape" });

    await expect(pending).resolves.toBe(false);
    wrapper.unmount();
  });
});

describe("TextField password", () => {
  it("shows and hides the password with the eye button", async () => {
    const wrapper = mount(TextField, { props: { label: "Пароль", type: "password", modelValue: "secret-1" } });
    const input = () => wrapper.get("input").element as HTMLInputElement;
    const eye = wrapper.get("button.field__reveal");

    expect(input().type).toBe("password");
    expect(eye.attributes("aria-label")).toBe("Показать пароль");
    expect(eye.attributes("aria-pressed")).toBe("false");

    await eye.trigger("click");
    expect(input().type).toBe("text");
    expect(eye.attributes("aria-label")).toBe("Скрыть пароль");
    expect(eye.attributes("aria-pressed")).toBe("true");

    await eye.trigger("click");
    expect(input().type).toBe("password");
  });

  it("has no eye button on ordinary fields and shows the leading icon", () => {
    const wrapper = mount(TextField, { props: { label: "Логин", icon: "user" } });

    expect(wrapper.find("button.field__reveal").exists()).toBe(false);
    expect(wrapper.find("svg.field__icon").exists()).toBe(true);
  });
});
