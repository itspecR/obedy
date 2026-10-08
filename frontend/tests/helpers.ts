import { vi } from "vitest";

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
