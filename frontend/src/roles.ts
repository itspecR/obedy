import type { Role } from "./api/auth";

export const ROLE_LABELS: Record<Role, string> = {
  employee: "Сотрудник",
  hr: "HR",
  admin: "Администратор",
};
