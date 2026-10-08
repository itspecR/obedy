import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DirectorySettings } from "../src/api/directory";
import DirectoryPage from "../src/pages/DirectoryPage.vue";
import { useToasts } from "../src/composables/useToasts";
import { bodySentTo, routeFetch } from "./helpers";

function settings(overrides: Partial<DirectorySettings> = {}): DirectorySettings {
  return {
    enabled: true,
    servers: "dc1.co.local",
    mode: "ldaps",
    port: null,
    ca_certificate: "",
    bind_user: "svc-obedy@co.local",
    has_bind_password: true,
    base_dn: "OU=Staff,DC=co,DC=local",
    group_dn: "",
    session_days: 30,
    ...overrides,
  };
}

async function mounted(routes: Record<string, [number, unknown]>) {
  const spy = routeFetch({ "/api/directory": [200, settings()], ...routes });
  const wrapper = mount(DirectoryPage);
  await flushPromises();
  return { spy, wrapper };
}

function button(wrapper: ReturnType<typeof mount>, text: string) {
  const found = wrapper.findAll("button").find((item) => item.text() === text);
  if (!found) {
    throw new Error(`Нет кнопки ${text}`);
  }
  return found;
}

describe("DirectoryPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  it("shows stored settings without the password and keeps saving disabled until something changes", async () => {
    const { wrapper } = await mounted({});

    expect(wrapper.text()).toContain("Пароль сохранён. Оставьте поле пустым, чтобы не менять его");
    expect(wrapper.text()).toContain("Пусто — стандартный порт 636");
    expect(wrapper.text()).toContain("Полные имена через пробел, как в сертификатах контроллеров (для LDAPS не IP)");
    expect(button(wrapper, "Сохранить").attributes("disabled")).toBeDefined();
    expect(button(wrapper, "Проверить подключение").attributes("disabled")).toBeUndefined();
  });

  it("sends numbers for port and days and blocks the check until saved", async () => {
    const { spy, wrapper } = await mounted({});
    const fields = wrapper.findAll("input");
    await fields.find((input) => input.attributes("type") === "number")?.setValue("3269");

    expect(button(wrapper, "Проверить подключение").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Сохраните изменения, чтобы проверить подключение");

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, "/api/directory")).toMatchObject({ port: 3269, session_days: 30, bind_password: "" });
  });

  it("marks every example as an example so it is not mistaken for a stored value", async () => {
    const { wrapper } = await mounted({});
    const examples = [...wrapper.findAll("input"), ...wrapper.findAll("textarea")]
      .map((field) => field.attributes("placeholder"))
      .filter((text): text is string => Boolean(text));

    expect(examples).toHaveLength(5);
    expect(examples.every((text) => text.startsWith("например: ") || text.startsWith("Вставьте текст сертификата"))).toBe(true);
  });

  it("warns about unencrypted LDAP", async () => {
    const { wrapper } = await mounted({});

    await wrapper.findAll('[role="radio"]').find((item) => item.text() === "Без шифрования")?.trigger("click");

    expect(wrapper.text()).toContain("пароли сотрудников передаются по сети открытым текстом");
  });

  it("shows the connection check result", async () => {
    const { wrapper } = await mounted({ "/api/directory/check": [200, { ok: false, message: "Контроллер домена не отвечает" }] });

    await button(wrapper, "Проверить подключение").trigger("click");
    await flushPromises();

    expect(wrapper.get('[role="status"]').text()).toBe("Контроллер домена не отвечает");
    expect(wrapper.get('[role="status"]').classes()).toContain("directory__check--fail");
  });
});
