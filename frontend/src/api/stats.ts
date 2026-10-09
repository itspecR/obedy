import { download, request } from "./http";
import type { Lunch } from "./lunch";

export interface StatsQuery {
  date_from: string;
  date_to: string;
  person: number[];
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

export interface PersonLunch {
  person_id: number;
  name: string;
  lunch: Lunch;
}

export interface Stats {
  date_from: string;
  date_to: string;
  overview: StatsOverview;
  people: PersonStats[];
  lunches: PersonLunch[];
}

const EXPORT_NAME = "obedy.xlsx";

function queryOf(query: StatsQuery): string {
  const params = new URLSearchParams({ date_from: query.date_from, date_to: query.date_to });
  query.person.forEach((id) => params.append("person", String(id)));
  return params.toString();
}

export const fetchStats = (query: StatsQuery) => request<Stats>("GET", `/lunch/stats?${queryOf(query)}`);
export const exportStats = (query: StatsQuery) => download(`/lunch/stats/export?${queryOf(query)}`, EXPORT_NAME);
