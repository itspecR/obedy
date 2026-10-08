import { download, request } from "./http";

export interface StatsQuery {
  date_from: string;
  date_to: string;
}

export interface PersonStats {
  id: number;
  name: string;
  login: string;
  count: number;
  violations: number;
  overruns: number;
  unreturned: number;
  average_minutes: number | null;
  overrun_minutes: number;
}

export interface StatsOverview {
  count: number;
  violations: number;
  average_minutes: number | null;
  on_time_percent: number | null;
  people: number;
}

export interface Stats {
  date_from: string;
  date_to: string;
  overview: StatsOverview;
  people: PersonStats[];
}

const EXPORT_NAME = "obedy.xlsx";

function queryOf(query: StatsQuery): string {
  return new URLSearchParams(Object.entries(query).filter(([, value]) => value)).toString();
}

export const fetchStats = (query: StatsQuery) => request<Stats>("GET", `/lunch/stats?${queryOf(query)}`);
export const exportStats = (query: StatsQuery) => download(`/lunch/stats/export?${queryOf(query)}`, EXPORT_NAME);
