import { describe, expect, it } from "vitest";
import type { Role } from "../src/api/auth";
import { decideRoute, pageTitle, routes } from "../src/router";

const login = { name: "login", meta: { guest: true } };
const home = { name: "home", meta: {} };
const change = { name: "change-password", meta: {} };
const lunch = { name: "lunch", meta: { roles: ["employee", "hr", "admin"] as Role[] } };
const adminOnly = { name: "settings", meta: { roles: ["admin"] as Role[] } };

const guest = { isLoggedIn: false, mustChangePassword: false, role: null };
const as = (role: Role, mustChangePassword = false) => ({ isLoggedIn: true, mustChangePassword, role });

describe("decideRoute", () => {
  it("sends guests to the login page", () => {
    expect(decideRoute(home, guest)).toEqual({ name: "login" });
    expect(decideRoute(lunch, guest)).toEqual({ name: "login" });
    expect(decideRoute(login, guest)).toBe(true);
  });

  it("keeps users with a temporary password on the change page", () => {
    expect(decideRoute(lunch, as("admin", true))).toEqual({ name: "change-password" });
    expect(decideRoute(login, as("employee", true))).toEqual({ name: "change-password" });
    expect(decideRoute(change, as("hr", true))).toBe(true);
  });

  it("opens the home page of the role from home, login and change pages", () => {
    expect(decideRoute(home, as("employee"))).toEqual({ name: "lunch" });
    expect(decideRoute(login, as("hr"))).toEqual({ name: "board" });
    expect(decideRoute(change, as("admin"))).toEqual({ name: "lunch" });
  });

  it("lets every role open the lunch page", () => {
    expect(decideRoute(lunch, as("employee"))).toBe(true);
    expect(decideRoute(lunch, as("hr"))).toBe(true);
    expect(decideRoute(lunch, as("admin"))).toBe(true);
  });

  it.each(["staff", "rules"])("opens the %s section to the admin only", (name) => {
    const section = routes.flatMap((route) => ("children" in route ? route.children : [])).find((route) => route?.name === name);

    expect(section?.meta).toMatchObject({ roles: ["admin"] });
  });

  it("leaves the home page to the role check instead of a fixed redirect", () => {
    const homeRoute = routes.flatMap((route) => ("children" in route ? route.children : [])).find((route) => route?.name === "home");

    expect(homeRoute).not.toHaveProperty("redirect");
  });

  it("opens the board to HR and the admin only", () => {
    const board = routes.flatMap((route) => ("children" in route ? route.children : [])).find((route) => route?.name === "board");

    expect(board?.meta).toMatchObject({ roles: ["hr", "admin"] });
  });

  it("keeps other roles out of admin sections", () => {
    expect(decideRoute(adminOnly, as("employee"))).toEqual({ name: "lunch" });
    expect(decideRoute(adminOnly, as("hr"))).toEqual({ name: "board" });
    expect(decideRoute(adminOnly, as("admin"))).toBe(true);
  });
});

describe("pageTitle", () => {
  it("adds the app name after the section name", () => {
    expect(pageTitle({ title: "Обед" })).toBe("Обед · Обеды");
    expect(pageTitle({})).toBe("Обеды");
  });
});
