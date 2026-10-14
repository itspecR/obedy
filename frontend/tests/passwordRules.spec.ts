import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { describe, expect, it } from "vitest";
import ChangePasswordForm from "../src/components/login/ChangePasswordForm.vue";
import { firstProblem, passwordRules } from "../src/components/login/passwordRules";

const met = (next: string, repeat = next, login = "ivanov.ii") => passwordRules(next, repeat, login).map((rule) => rule.met);

describe("password rules", () => {
  it("checks length, digits, login and match", () => {
    expect(met("лиса-в-снегу-2026")).toEqual([true, true, true, true]);
    expect(met("short")).toEqual([false, true, true, true]);
    expect(met("x".repeat(129))).toEqual([false, true, true, true]);
    expect(met("8264019375")).toEqual([true, false, true, true]);
    expect(met("my-Ivanov.II-pass")).toEqual([true, true, false, true]);
    expect(met("лиса-в-снегу-2026", "другое")).toEqual([true, true, true, false]);
    expect(met("")).toEqual([false, false, false, false]);
  });

  it("reports the first unmet rule", () => {
    expect(firstProblem(passwordRules("8264019375", "8264019375", ""))).toBe("Пароль не может состоять только из цифр");
    expect(firstProblem(passwordRules("лиса-в-снегу-2026", "лиса-в-снегу-2026", ""))).toBe("");
  });

  it("lights rules green while typing", async () => {
    setActivePinia(createPinia());
    const wrapper = mount(ChangePasswordForm);
    const [next, repeat] = wrapper.findAll('input[type="password"]');
    await next.setValue("лиса-в-снегу-2026");
    await repeat.setValue("лиса-в-снегу-2026");

    expect(wrapper.findAll(".password-form__rule--met")).toHaveLength(4);
  });
});
