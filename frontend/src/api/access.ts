import { request } from "./http";

export interface AllowedNetwork {
  id: number;
  network: string;
  note: string;
}

export interface AccessState {
  allow_private: boolean;
  private_ranges: string[];
  your_address: string;
  networks: AllowedNetwork[];
}

export const fetchAccess = () => request<AccessState>("GET", "/access");
export const addNetwork = (network: string, note: string) => request<AccessState>("POST", "/access/networks", { network, note });
export const removeNetwork = (id: number) => request<AccessState>("DELETE", `/access/networks/${id}`);
export const setPrivateNetworks = (enabled: boolean) => request<AccessState>("PUT", "/access/private", { enabled });
