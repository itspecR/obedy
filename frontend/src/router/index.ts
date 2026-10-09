import { SETUP_ROUTE, decideSetup, setupStatus } from "../components/setup/setupRoute";
import { createRouter, createWebHistory, type RouteLocationRaw, type RouteMeta } from "vue-router";
import type { Role } from "../api/auth";
import { onUnauthorized } from "../api/http";
import { HOME_BY_ROLE } from "../navigation";
import { useSession } from "../stores/session";

const LUNCH_TAKERS: Role[] = ["employee", "hr"];
const ADMIN: Role[] = ["admin"];
const BOARD: Role[] = ["hr", "admin"];
const RESOLVED_BY_GUARD = { render: () => null };

export const routes = [
  { path: "/setup", name: "setup", component: () => import("../pages/SetupPage.vue"), meta: { title: "Подключение базы" } },
  { path: "/login", name: "login", component: () => import("../pages/LoginPage.vue"), meta: { guest: true, title: "Вход" } },
  { path: "/change-password", name: "change-password", component: () => import("../pages/ChangePasswordPage.vue"), meta: { title: "Смена пароля" } },
  {
    path: "/",
    component: () => import("../components/shell/AppShell.vue"),
    children: [
      { path: "", name: "home", component: RESOLVED_BY_GUARD },
      {
        path: "lunch",
        name: "lunch",
        component: () => import("../pages/LunchPage.vue"),
        meta: { roles: LUNCH_TAKERS, title: "Обед" },
      },
      {
        path: "board",
        name: "board",
        component: () => import("../pages/BoardPage.vue"),
        meta: { roles: BOARD, title: "Табло" },
      },
      {
        path: "stats",
        name: "stats",
        component: () => import("../pages/StatsPage.vue"),
        meta: { roles: BOARD, title: "Статистика" },
      },
      {
        path: "staff",
        name: "staff",
        component: () => import("../pages/StaffPage.vue"),
        meta: { roles: ADMIN, title: "Сотрудники" },
      },
      {
        path: "rules",
        name: "rules",
        component: () => import("../pages/RulesPage.vue"),
        meta: { roles: BOARD, title: "Правила обеда" },
      },
      {
        path: "access",
        name: "access",
        component: () => import("../pages/AccessPage.vue"),
        meta: { roles: ADMIN, title: "Доступ" },
      },
      {
        path: "directory",
        name: "directory",
        component: () => import("../pages/DirectoryPage.vue"),
        meta: { roles: ADMIN, title: "Домен" },
      },
      {
        path: "log",
        name: "log",
        component: () => import("../pages/JournalPage.vue"),
        meta: { roles: ADMIN, title: "Log" },
      },
      { path: "journal", redirect: "/log" },
    ],
  },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

interface SessionState {
  isLoggedIn: boolean;
  mustChangePassword: boolean;
  role: Role | null;
}

export function decideRoute(target: { name?: unknown; meta: RouteMeta }, state: SessionState): RouteLocationRaw | true {
  if (!state.isLoggedIn || state.role === null) {
    return target.meta.guest ? true : { name: "login" };
  }
  if (state.mustChangePassword) {
    return target.name === "change-password" ? true : { name: "change-password" };
  }
  const home = { name: HOME_BY_ROLE[state.role] };
  if (target.meta.guest || target.name === "change-password" || target.name === "home") {
    return home;
  }
  if (target.meta.roles && !target.meta.roles.includes(state.role)) {
    return home;
  }
  return true;
}

export const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach(async (to) => {
  const setupRedirect = decideSetup(to.name, await setupStatus());
  if (setupRedirect || to.name === SETUP_ROUTE) {
    return setupRedirect ?? true;
  }
  const session = useSession();
  if (!session.loaded) {
    await session.load();
  }
  return decideRoute(to, { isLoggedIn: session.isLoggedIn, mustChangePassword: session.mustChangePassword, role: session.me?.role ?? null });
});

const APP_TITLE = "Обеды";

export function pageTitle(meta: RouteMeta): string {
  return typeof meta.title === "string" ? `${meta.title} · ${APP_TITLE}` : APP_TITLE;
}

router.afterEach((to) => {
  document.title = pageTitle(to.meta);
});

onUnauthorized(() => {
  useSession().forget();
  void router.replace({ name: "login" });
});
