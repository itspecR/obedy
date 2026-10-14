import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DirectorySettings, SyncReport } from "../src/api/directory";
import { NEVER_RAN, describeSync } from "../src/components/directory/syncReport";
import DirectoryPage from "../src/pages/DirectoryPage.vue";
import { useToasts } from "../src/composables/useToasts";
import { bodySentTo, routeFetch, wasRequested, infoText } from "./helpers";

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

function report(overrides: Partial<SyncReport> = {}): SyncReport {
  return {
    finished_at: "2026-10-08T11:00:00Z",
    status: "done",
    message: "Добавлено 3, обновлено 1, отключено 0",
    created: 3,
    updated: 1,
    deactivated: 0,
    skipped: 0,
    ...overrides,
  };
}

const NO_REPORT = report({ finished_at: null, status: null, message: "", created: 0, updated: 0 });

async function mounted(routes: Record<string, [number, unknown]>) {
  const spy = routeFetch({ "/api/directory": [200, settings()], "/api/directory/sync": [200, NO_REPORT], ...routes });
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

    expect(await infoText(wrapper, "Пароль")).toBe("Пароль сохранён. Оставьте поле пустым, чтобы не менять его");
    expect(await infoText(wrapper, "Порт")).toContain("Пусто — стандартный порт 636");
    expect(await infoText(wrapper, "Контроллеры домена")).toContain("Полные имена через пробел, как в сертификатах контроллеров (для LDAPS не IP)");
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

    expect(wrapper.get(".directory__check").text()).toBe("Контроллер домена не отвечает");
    expect(wrapper.get(".directory__check").classes()).toContain("directory__check--fail");
  });
});

describe("synchronization report", () => {
  it("explains that sync has not run yet", () => {
    expect(describeSync(null)).toEqual({ tone: "neutral", text: NEVER_RAN });
    expect(describeSync(NO_REPORT)).toEqual({ tone: "neutral", text: NEVER_RAN });
  });

  it("shows Moscow time and the status colour", () => {
    expect(describeSync(report())).toEqual({ tone: "ok", text: "08.10.2026, 14:00 — Добавлено 3, обновлено 1, отключено 0" });
    expect(describeSync(report({ status: "skipped" })).tone).toBe("neutral");
    expect(describeSync(report({ status: "guarded" })).tone).toBe("attention");
    expect(describeSync(report({ status: "failed" })).tone).toBe("alarm");
  });
});

describe("DirectoryPage synchronization", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  it("shows the last report and runs the sync on demand", async () => {
    const { spy, wrapper } = await mounted({ "/api/directory/sync": [200, report()] });

    expect(wrapper.get(".sync__result").text()).toBe("08.10.2026, 14:00 — Добавлено 3, обновлено 1, отключено 0");
    expect(wrapper.get(".sync__result").classes()).toContain("sync__result--ok");

    await button(wrapper, "Синхронизировать сейчас").trigger("click");
    await flushPromises();

    expect(wasRequested(spy, "/api/directory/sync", "POST")).toBe(true);
  });

  it("asks to save changes before syncing", async () => {
    const { wrapper } = await mounted({});
    await wrapper.findAll("input").find((input) => input.attributes("type") === "number")?.setValue("3269");

    expect(button(wrapper, "Синхронизировать сейчас").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Сохраните изменения, чтобы синхронизировать сотрудников");
  });

  it("asks to enable domain login before syncing", async () => {
    const { wrapper } = await mounted({ "/api/directory": [200, settings({ enabled: false })] });

    expect(button(wrapper, "Синхронизировать сейчас").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Включите вход через домен и сохраните, чтобы синхронизировать сотрудников");
  });

  it("reports a sync that is already running", async () => {
    const { wrapper } = await mounted({});
    routeFetch({ "/api/directory/sync": [409, { detail: "Синхронизация уже идёт. Подождите минуту и обновите страницу" }] });

    await button(wrapper, "Синхронизировать сейчас").trigger("click");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Синхронизация уже идёт. Подождите минуту и обновите страницу");
  });
});
