import type { SystemInfo } from "../../api/journal";
import { formatDateTime } from "../../format/dateTime";

const GIB = 1024 ** 3;
const MIB = 1024 ** 2;
const PERCENT = 100;
export const NO_DATA = "нет данных";

export function formatBytes(bytes: number): string {
  if (bytes >= GIB) {
    return `${(bytes / GIB).toFixed(1).replace(".", ",")} ГБ`;
  }
  return `${Math.round(bytes / MIB)} МБ`;
}

export function momentText(iso: string | null): string {
  return iso ? formatDateTime(iso) : NO_DATA;
}

export function memoryText(used: number | null, total: number | null): string {
  if (used === null || total === null || !total) {
    return NO_DATA;
  }
  return `занято ${formatBytes(used)} из ${formatBytes(total)} (${Math.round((used / total) * PERCENT)}%)`;
}

export function freeText(info: SystemInfo): string {
  if (info.memory_used === null || info.memory_total === null) {
    return NO_DATA;
  }
  return formatBytes(info.memory_total - info.memory_used);
}

export function osText(info: SystemInfo): string {
  if (!info.os_name) {
    return NO_DATA;
  }
  return info.os_source === "container" ? `${info.os_name} (контейнер приложения)` : info.os_name;
}

export function appMemoryText(info: SystemInfo): string {
  if (info.app_memory_used === null) {
    return NO_DATA;
  }
  return info.app_memory_limit ? memoryText(info.app_memory_used, info.app_memory_limit) : formatBytes(info.app_memory_used);
}
