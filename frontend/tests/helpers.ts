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
