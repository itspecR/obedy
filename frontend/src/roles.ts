import type { Role } from "./api/auth";

export const ROLE_LABELS: Record<Role, string> = {
  employee: "Сотрудник",
  hr: "HR",
  admin: "Администратор",
};

export const ROLE_CHOICES = (Object.entries(ROLE_LABELS) as [Role, string][]).map(([value, label]) => ({ value, label }));
