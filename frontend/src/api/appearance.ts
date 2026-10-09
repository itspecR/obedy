import { request } from "./http";

export interface Appearance {
  rabbit: boolean;
}

export const fetchAppearance = () => request<Appearance>("GET", "/appearance");
export const switchRabbit = (enabled: boolean) => request<Appearance>("PUT", "/appearance/rabbit", { enabled });

export async function rabbitWanted(): Promise<boolean> {
  try {
    return (await fetchAppearance()).rabbit;
  } catch {
    return false;
  }
}
