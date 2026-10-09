import type { DOMWrapper, VueWrapper } from "@vue/test-utils";
import { vi } from "vitest";
import { formatFullDay } from "../src/format/dateTime";

export function mockFetch(status: number, body: unknown) {
  const response = new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
  const spy = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", spy);
  return spy;
}

export function sentBody(spy: ReturnType<typeof vi.fn>): unknown {
  const init = spy.mock.calls[0][1] as RequestInit;
  return JSON.parse(init.body as string);
}

export function routeFetch(routes: Record<string, [number, unknown]>) {
  const spy = vi.fn((url: string) => {
    const [status, body] = routes[url] ?? [404, { detail: "Не найдено" }];
    return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
  });
  vi.stubGlobal("fetch", spy);
  return spy;
}

export function bodySentTo(spy: ReturnType<typeof vi.fn>, url: string): unknown {
  const call = spy.mock.calls.find(([target, init]) => target === url && (init as RequestInit | undefined)?.body);
  return call ? JSON.parse((call[1] as RequestInit).body as string) : undefined;
}

export function wasRequested(spy: ReturnType<typeof vi.fn>, url: string, method: string): boolean {
  return spy.mock.calls.some(([target, init]) => target === url && (init as RequestInit | undefined)?.method === method);
}

type Root = VueWrapper | DOMWrapper<Element>;

function fieldNamed(root: Root, selector: string, label: string): DOMWrapper<Element> {
  const field = root.findAll(selector).find((item) => item.find(".field-label").text() === label);
  if (!field) {
    throw new Error(`Поле «${label}» не найдено`);
  }
  return field;
}

function buttonNamed(root: Root, text: string): DOMWrapper<Element> {
  const button = root.findAll("button").find((item) => item.text() === text);
  if (!button) {
    throw new Error(`Кнопка «${text}» не найдена`);
  }
  return button;
}

export function shownTime(root: Root, label: string): string {
  return fieldNamed(root, ".time-field", label).get(".field-control span").text();
}

export async function chooseTime(root: Root, label: string, clock: string): Promise<void> {
  const field = fieldNamed(root, ".time-field", label);
  await field.get("button.field-control").trigger("click");
  const [hours, minutes] = clock.split(":");
  const [hourWheel, minuteWheel] = field.findAll(".wheel");
  await hourWheel.findAll(".wheel__item").find((item) => item.text() === hours)?.trigger("click");
  await minuteWheel.findAll(".wheel__item").find((item) => item.text() === minutes)?.trigger("click");
  await buttonNamed(field, "Готово").trigger("click");
}

export async function chooseDay(root: Root, label: string, day: string): Promise<void> {
  const field = fieldNamed(root, ".date-field", label);
  await field.get("button.field-control").trigger("click");
  await field.get(`[aria-label="${formatFullDay(day)}"]`).trigger("click");
}

export async function infoText(root: Root, label: string): Promise<string> {
  const button = root.get(`[aria-label="Подсказка: ${label}"]`);
  await button.trigger("click");
  return root.get(`#${button.attributes("aria-controls")}`).text();
}

export async function choosePerson(root: Root, query: string, name: string): Promise<void> {
  await root.get("input[role=combobox]").setValue(query);
  await root
    .findAll("[role=option]")
    .find((option) => option.text().includes(name))
    ?.trigger("mousedown");
}
