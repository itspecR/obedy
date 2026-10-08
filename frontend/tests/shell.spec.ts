import { mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import type { Role } from "../src/api/auth";
import ProfileDialog from "../src/components/shell/ProfileDialog.vue";
import SideNav from "../src/components/shell/SideNav.vue";
import { initials, shortName } from "../src/navigation";
import { me } from "./people";

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });

function navLabels(role: Role): string[] {
  const wrapper = mount(SideNav, { props: { me: me(role) }, global: { plugins: [router] } });
  return wrapper.findAll("nav a").map((link) => link.text());
}

describe("SideNav", () => {
  it("shows the lunch section to everyone and access settings to the admin", () => {
    expect(navLabels("employee")).toEqual(["Обед"]);
    expect(navLabels("hr")).toEqual(["Обед", "Табло"]);
    expect(navLabels("admin")).toEqual(["Табло", "Сотрудники", "Правила", "Доступ", "Домен"]);
  });

  it("shows the app name and emits profile and logout", async () => {
    const wrapper = mount(SideNav, { props: { me: me("admin") }, global: { plugins: [router] } });
    const card = wrapper.get("button.user");

    expect(wrapper.text()).toContain("Обеды");
    expect(card.text()).toBe("ПАПетрова Анна");
    await card.trigger("click");
    await wrapper.get(".side__logout").trigger("click");

    expect(wrapper.emitted("openProfile")).toHaveLength(1);
    expect(wrapper.emitted("logout")).toHaveLength(1);
  });
});

describe("names", () => {
  it("builds initials and a short name from the full name", () => {
    expect(initials("Петрова Анна Андреевна")).toBe("ПА");
    expect(shortName("Петрова Анна Андреевна")).toBe("Петрова Анна");
    expect(initials("admin")).toBe("AD");
  });
});

describe("ProfileDialog", () => {
  it("shows name, role and login, then switches to the password form for local accounts", async () => {
    const wrapper = mount(ProfileDialog, { props: { me: me("admin") }, global: { plugins: [createPinia()] } });

    expect(wrapper.text()).toContain("Петрова Анна Андреевна");
    expect(wrapper.text()).toContain("Администратор");
    expect(wrapper.text()).toContain("petrova.aa");

    await wrapper.findAll("button").find((button) => button.text() === "Сменить пароль")?.trigger("click");

    expect(wrapper.find("form").exists()).toBe(true);
    expect(wrapper.get("h2").text()).toBe("Смена пароля");
  });

  it("explains that domain passwords change in Windows", () => {
    const wrapper = mount(ProfileDialog, { props: { me: me("employee", { source: "domain" }) }, global: { plugins: [createPinia()] } });

    expect(wrapper.text()).toContain("Пароль меняется в Windows");
    expect(wrapper.findAll("button").some((button) => button.text() === "Сменить пароль")).toBe(false);
  });

  it("closes on Escape even when focus has left the dialog", () => {
    const wrapper = mount(ProfileDialog, { props: { me: me("admin") }, global: { plugins: [createPinia()] }, attachTo: document.body });
    (document.activeElement as HTMLElement | null)?.blur();

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));

    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });
});
