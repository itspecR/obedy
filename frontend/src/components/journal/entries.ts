import type { Person } from "../../api/board";
import type { JournalAction, JournalCategory, JournalEntry, JournalRow } from "../../api/journal";
import { shiftDay } from "../../format/calendar";
import type { Tone } from "../ui/tone";

export const DEFAULT_PERIOD_DAYS = 7;
export const ALL_CATEGORIES = "all";
export const UNKNOWN_LOGIN = "Неизвестный логин";

export type CategoryChoice = JournalCategory | typeof ALL_CATEGORIES;

interface ActionInfo {
  label: string;
  tone: Tone;
}

export const ACTIONS: Record<JournalAction, ActionInfo> = {
  login: { label: "Вход", tone: "neutral" },
  login_failed: { label: "Неудачный вход", tone: "attention" },
  logout: { label: "Выход", tone: "neutral" },
  password_changed: { label: "Сменил свой пароль", tone: "neutral" },
  role_changed: { label: "Изменена роль", tone: "neutral" },
  track_lunch_changed: { label: "Изменён учёт обеда", tone: "neutral" },
  blocked: { label: "Заблокирован", tone: "alarm" },
  unblocked: { label: "Разблокирован", tone: "neutral" },
  account_created: { label: "Создана учётная запись", tone: "neutral" },
  profile_changed: { label: "Изменено ФИО", tone: "neutral" },
  password_issued: { label: "Выдан временный пароль", tone: "neutral" },
  lunch_corrected: { label: "Исправлен обед", tone: "neutral" },
  lunch_added: { label: "Добавлен обед", tone: "neutral" },
  lunch_deleted: { label: "Удалён обед", tone: "alarm" },
  rules_changed: { label: "Изменены правила обеда", tone: "neutral" },
  network_added: { label: "Добавлен адрес доступа", tone: "neutral" },
  network_removed: { label: "Удалён адрес доступа", tone: "alarm" },
  private_networks_changed: { label: "Изменён доступ из локальной сети", tone: "neutral" },
  directory_changed: { label: "Изменены настройки домена", tone: "neutral" },
  directory_checked: { label: "Проверка связи с доменом", tone: "neutral" },
  directory_synced: { label: "Синхронизация с доменом", tone: "neutral" },
};

export const CATEGORY_OPTIONS: { value: CategoryChoice; label: string }[] = [
  { value: ALL_CATEGORIES, label: "Все" },
  { value: "logins", label: "Входы" },
  { value: "staff", label: "Сотрудники" },
  { value: "lunches", label: "Обеды" },
  { value: "settings", label: "Настройки" },
];

export function recentPeriod(today: string): { from: string; to: string } {
  return { from: shiftDay(today, 1 - DEFAULT_PERIOD_DAYS), to: today };
}

export function categoryOf(choice: CategoryChoice): JournalCategory | null {
  return choice === ALL_CATEGORIES ? null : choice;
}

export function subjectName(entry: JournalEntry): string {
  return (entry.actor ?? entry.target)?.name ?? UNKNOWN_LOGIN;
}

export function objectOf(entry: JournalEntry): Person | null {
  return entry.actor ? entry.target : null;
}

export function rowValue(row: JournalRow): string {
  return row.before !== null && row.after !== null ? `${row.before} → ${row.after}` : (row.after ?? row.before ?? "");
}
