import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { StaffMember } from "../src/api/staff";
import { EMPTY_FILTER, filterStaff } from "../src/components/staff/filters";
import StaffPage from "../src/pages/StaffPage.vue";
import { useConfirm } from "../src/composables/useConfirm";
import { useToasts } from "../src/composables/useToasts";
import { useSession } from "../src/stores/session";
import { bodySentTo, routeFetch } from "./helpers";
import { me } from "./people";

function member(overrides: Partial<StaffMember> = {}): StaffMember {
  return {
    id: 1,
    login: "ivanov",
    full_name: "Иванов Иван",
    role: "employee",
    source: "domain",
    status: "active",
    track_lunch: true,
    can_track_lunch: true,
    last_login_at: null,
    ...overrides,
  };
}

const PEOPLE = [
  member(),
  member({ id: 2, login: "petrov", full_name: "Пётр Петров", role: "hr", track_lunch: false }),
  member({ id: 3, login: "sidorov", full_name: "", status: "blocked", source: "local" }),
];

const logins = (members: StaffMember[]) => members.map((item) => item.login);

describe("staff filters", () => {
  it("finds by several words across name and login", () => {
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "иван ivanov" }))).toEqual(["ivanov"]);
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "склад" }))).toEqual([]);
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "SIDOROV" }))).toEqual(["sidorov"]);
  });

  it("treats ё and е as the same letter", () => {
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "петр" }))).toEqual(["petrov"]);
  });

  it("filters by role and status", () => {
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, role: "hr" }))).toEqual(["petrov"]);
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, status: "blocked" }))).toEqual(["sidorov"]);
    expect(logins(filterStaff(PEOPLE, EMPTY_FILTER))).toEqual(["ivanov", "petrov", "sidorov"]);
  });
});

describe("StaffPage", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(response: [number, unknown]) {
    routeFetch({ "/api/staff": response });
    const wrapper = mount(StaffPage);
    await flushPromises();
    return wrapper;
  }

  it("lists everyone with role, lunch tracking and coloured status", async () => {
    const wrapper = await mounted([200, PEOPLE]);
    const rows = wrapper.findAll(".staff__row");

    expect(wrapper.text()).toContain("Всего 3");
    expect(rows).toHaveLength(3);
    expect(rows[1].text()).toContain("Пётр Петров");
    expect(rows[1].text()).toContain("HR");
    expect(rows[1].text()).toContain("Не учитываются");
    expect(rows[2].text()).toContain("sidorov");
    expect(wrapper.text()).not.toContain("Отдел");
    expect(rows[2].get(".badge").classes()).toContain("badge--alarm");
    expect(wrapper.text()).not.toContain("Нет в домене");
  });

  it("counts shown people and explains an empty search", async () => {
    const wrapper = await mounted([200, PEOPLE]);

    await wrapper.get("input").setValue("никого такого");

    expect(wrapper.text()).toContain("Показано 0 из 3");
    expect(wrapper.text()).toContain("Никого не нашли");
  });

  it("explains where people come from when there are none", async () => {
    const wrapper = await mounted([200, []]);

    expect(wrapper.text()).toContain("Сотрудников пока нет");
  });

  it("shows a load error with a retry button", async () => {
    const wrapper = await mounted([500, { detail: "На сервере произошла ошибка" }]);

    expect(wrapper.get('[role="alert"]').text()).toContain("На сервере произошла ошибка");
    expect(wrapper.findAll("button").some((button) => button.text() === "Повторить")).toBe(true);
  });
});

describe("StaffPage management", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useSession().me = { ...me("admin"), login: "boss" };
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function opened(people: StaffMember[], login: string, routes: Record<string, [number, unknown]> = {}) {
    const spy = routeFetch({ "/api/staff": [200, people], ...routes });
    const wrapper = mount(StaffPage, { attachTo: document.body });
    await flushPromises();
    const target = people.find((person) => person.login === login);
    await wrapper.get(`[aria-label="Действия: ${target?.full_name || login}"]`).trigger("click");
    return { spy, wrapper };
  }

  const dialog = () => document.body.querySelector('[role="dialog"]') as HTMLElement;
  const buttonIn = (text: string) => [...dialog().querySelectorAll("button")].find((button) => button.textContent?.trim() === text) as HTMLButtonElement;

  it("changes the role and shows the server answer in the list", async () => {
    const promoted = member({ role: "hr", track_lunch: false });
    const { spy, wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/role": [200, promoted] });

    buttonIn("HR").click();
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/role")).toEqual({ role: "hr" });
    expect(wrapper.findAll(".staff__row")[0].text()).toContain("Не учитываются");
    wrapper.unmount();
  });

  it("switches lunch tracking", async () => {
    const { spy, wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/track-lunch": [200, member({ track_lunch: false })] });

    (dialog().querySelector('[role="switch"]') as HTMLButtonElement).click();
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/track-lunch")).toEqual({ track_lunch: false });
    wrapper.unmount();
  });

  it("does not offer lunch tracking to an administrator", async () => {
    const admin = member({ id: 7, login: "chief", full_name: "Главный Админ", role: "admin", track_lunch: false, can_track_lunch: false });
    const { wrapper } = await opened([...PEOPLE, admin], "chief");

    expect(dialog().querySelector('[role="switch"]')).toBeNull();
    wrapper.unmount();
  });

  it("asks before blocking and blocks after confirmation", async () => {
    const { spy, wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/blocked": [200, member({ status: "blocked" })] });

    buttonIn("Заблокировать").click();
    expect(useConfirm().current.request?.title).toBe("Заблокировать: Иванов Иван?");
    useConfirm().answer(true);
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/blocked")).toEqual({ blocked: true });
    expect(buttonIn("Разблокировать")).toBeTruthy();
    wrapper.unmount();
  });

  it("does not block when the admin changes their mind", async () => {
    const { spy, wrapper } = await opened(PEOPLE, "ivanov");

    buttonIn("Заблокировать").click();
    useConfirm().answer(false);
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/blocked")).toBeUndefined();
    wrapper.unmount();
  });

  it("keeps the admin from changing their own role or blocking themselves", async () => {
    const self = member({ id: 7, login: "boss", full_name: "Начальник", role: "admin" });
    const { wrapper } = await opened([self], "boss");

    expect(buttonIn("Сотрудник").disabled).toBe(true);
    expect(buttonIn("Заблокировать").disabled).toBe(true);
    expect(dialog().textContent).toContain("Свою роль изменить нельзя");
    wrapper.unmount();
  });

  it("shows the server refusal", async () => {
    const { wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/role": [409, { detail: "Нельзя: это последний активный администратор" }] });

    buttonIn("Администратор").click();
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Нельзя: это последний активный администратор");
    wrapper.unmount();
  });
});

describe("StaffPage local accounts", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useSession().me = { ...me("admin"), login: "boss" };
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
    document.body.innerHTML = "";
  });

  const dialog = () => document.body.querySelector('[role="dialog"]') as HTMLElement;
  const buttonIn = (text: string) => [...dialog().querySelectorAll("button")].find((button) => button.textContent?.trim() === text) as HTMLButtonElement | undefined;
  const fieldIn = (label: string) => {
    const labelNode = [...dialog().querySelectorAll("label")].find((node) => node.textContent?.trim() === label) as HTMLLabelElement;
    return document.getElementById(labelNode.htmlFor) as HTMLInputElement;
  };
  const type = (input: HTMLInputElement, value: string) => {
    input.value = value;
    input.dispatchEvent(new Event("input"));
  };

  const LOCAL = member({ id: 9, login: "kassa", full_name: "Кассир Касса", source: "local" });

  async function page(people: StaffMember[], routes: Record<string, [number, unknown]> = {}) {
    const spy = routeFetch({ "/api/staff": [200, people], ...routes });
    const wrapper = mount(StaffPage, { attachTo: document.body });
    await flushPromises();
    return { spy, wrapper };
  }

  it("creates a local account and shows the one-time password", async () => {
    const { wrapper } = await page(PEOPLE);
    const created = routeFetch({ "/api/staff": [201, { member: LOCAL, temporary_password: "Temp12345a" }] });

    await wrapper.findAll("button").find((button) => button.text() === "Добавить сотрудника")?.trigger("click");
    type(fieldIn("Логин"), "kassa");
    type(fieldIn("ФИО"), "Кассир Касса");
    buttonIn("Создать")?.click();
    await flushPromises();

    expect(bodySentTo(created, "/api/staff")).toMatchObject({ login: "kassa", full_name: "Кассир Касса", role: "employee" });
    expect(dialog().textContent).toContain("Учётная запись создана");
    expect((dialog().querySelector('[aria-label="Временный пароль"]') as HTMLInputElement).value).toBe("Temp12345a");
    expect(wrapper.text()).toContain("Всего 4");
    wrapper.unmount();
  });

  it("shows why the account was not created", async () => {
    const { wrapper } = await page(PEOPLE, {});
    routeFetch({ "/api/staff": [409, { detail: "Логин kassa уже занят" }] });

    await wrapper.findAll("button").find((button) => button.text() === "Добавить сотрудника")?.trigger("click");
    buttonIn("Создать")?.click();
    await flushPromises();

    expect(dialog().querySelector('[role="alert"]')?.textContent).toBe("Логин kassa уже занят");
    wrapper.unmount();
  });

  it("edits the profile of a local account", async () => {
    const { spy, wrapper } = await page([LOCAL], { "/api/staff/9/profile": [200, { ...LOCAL, full_name: "Кассирова Анна" }] });
    await wrapper.get('[aria-label="Действия: Кассир Касса"]').trigger("click");

    expect(buttonIn("Сохранить данные")?.disabled).toBe(true);
    type(fieldIn("ФИО"), "Кассирова Анна");
    await flushPromises();
    buttonIn("Сохранить данные")?.click();
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/9/profile")).toEqual({ full_name: "Кассирова Анна" });
    expect(wrapper.text()).toContain("Кассирова Анна");
    wrapper.unmount();
  });

  it("resets the password after confirmation and shows the new one", async () => {
    const { wrapper } = await page([LOCAL], { "/api/staff/9/password": [200, { member: LOCAL, temporary_password: "NewTemp789b" }] });
    await wrapper.get('[aria-label="Действия: Кассир Касса"]').trigger("click");

    buttonIn("Сбросить пароль")?.click();
    expect(useConfirm().current.request?.title).toBe("Сбросить пароль: Кассир Касса?");
    useConfirm().answer(true);
    await flushPromises();

    expect((dialog().querySelector('[aria-label="Временный пароль"]') as HTMLInputElement).value).toBe("NewTemp789b");
    wrapper.unmount();
  });

  it("keeps domain data read-only and offers no password reset", async () => {
    const { wrapper } = await page(PEOPLE);
    await wrapper.get('[aria-label="Действия: Иванов Иван"]').trigger("click");

    expect(dialog().textContent).toContain("ФИО, отдел и должность берутся из Active Directory");
    expect(buttonIn("Сбросить пароль")).toBeUndefined();
    wrapper.unmount();
  });
});
