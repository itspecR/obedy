import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSession } from "../src/stores/session";
import { mockFetch } from "./helpers";
import { me } from "./people";

describe("session store", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => vi.unstubAllGlobals());

  it("treats 401 from /me as a guest", async () => {
    mockFetch(401, { detail: "Войдите в систему" });
    const session = useSession();

    await session.load();

    expect(session.loaded).toBe(true);
    expect(session.isLoggedIn).toBe(false);
  });

  it("remembers the signed-in user", async () => {
    mockFetch(200, me("employee", { must_change_password: true }));
    const session = useSession();

    await session.load();

    expect(session.isLoggedIn).toBe(true);
    expect(session.mustChangePassword).toBe(true);
  });

  it("reports a network failure instead of logging out silently", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    const session = useSession();

    await expect(session.load()).rejects.toThrow("Нет связи с сервером");
  });
});

describe("expired session", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("calls the unauthorized handler for ordinary requests but not for /auth/me", async () => {
    const { onUnauthorized, request } = await import("../src/api/http");
    const handler = vi.fn();
    onUnauthorized(handler);
    mockFetch(401, { detail: "Войдите в систему" });

    await expect(request("POST", "/auth/change-password", {})).rejects.toThrow("Войдите в систему");
    expect(handler).toHaveBeenCalledTimes(1);

    mockFetch(401, { detail: "Войдите в систему" });
    await expect(request("GET", "/auth/me")).rejects.toThrow();
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
