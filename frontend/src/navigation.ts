import type { Role } from "./api/auth";
import type { IconName } from "./components/ui/AppIcon.vue";

export interface Section {
  name: string;
  path: string;
  label: string;
  icon: IconName;
}

const LUNCH: Section = { name: "lunch", path: "/lunch", label: "Обед", icon: "lunch" };
const RULES: Section = { name: "rules", path: "/rules", label: "Правила", icon: "clock" };
const BOARD: Section = { name: "board", path: "/board", label: "Табло", icon: "board" };
const STATS: Section = { name: "stats", path: "/stats", label: "Статистика", icon: "chart" };
const STAFF: Section = { name: "staff", path: "/staff", label: "Сотрудники", icon: "users" };
const ACCESS: Section = { name: "access", path: "/access", label: "Доступ", icon: "shield" };
const DIRECTORY: Section = { name: "directory", path: "/directory", label: "Домен", icon: "server" };

export const SECTIONS_BY_ROLE: Record<Role, Section[]> = {
  employee: [LUNCH],
  hr: [LUNCH, BOARD, STATS],
  admin: [BOARD, STATS, STAFF, RULES, ACCESS, DIRECTORY],
};

export const HOME_BY_ROLE: Record<Role, string> = {
  employee: "lunch",
  hr: "board",
  admin: "board",
};

export function initials(name: string): string {
  const parts = name.split(/\s+/).filter(Boolean);
  const letters = parts.length > 1 ? [parts[0][0], parts[1][0]] : [name[0] ?? "", name[1] ?? ""];
  return letters.join("").toUpperCase();
}

export function shortName(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).join(" ");
}
