import { request } from "./http";

export interface RulesForm {
  limit_minutes: number;
  workdays: string;
  day_end: string;
  window_enabled: boolean;
  window_start: string;
  window_end: string;
}

export interface LunchRules extends RulesForm {
  updated_at: string;
  min_limit_minutes: number;
  max_limit_minutes: number;
}

export const fetchLunchRules = () => request<LunchRules>("GET", "/lunch/rules");
export const saveLunchRules = (form: RulesForm) => request<LunchRules>("PUT", "/lunch/rules", form);

export interface CalendarDay {
  day: string;
  working: boolean;
}

export const fetchCalendar = (year: number) => request<CalendarDay[]>("GET", `/lunch/rules/calendar?year=${year}`);
export const addCalendarDay = (entry: CalendarDay) => request<CalendarDay[]>("POST", "/lunch/rules/calendar", entry);
export const removeCalendarDay = (day: string) => request<CalendarDay[]>("DELETE", `/lunch/rules/calendar/${day}`);
