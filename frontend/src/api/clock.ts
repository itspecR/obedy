import { request } from "./http";

export interface LunchWindow {
  start: string;
  end: string;
}

export interface ClockInfo {
  server_time: string;
  time_zone: string;
  lunch_window: LunchWindow | null;
}

export const fetchClock = () => request<ClockInfo>("GET", "/clock");
