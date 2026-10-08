import type { DirectoryForm, DirectoryMode, DirectorySettings } from "../../api/directory";

export interface DirectoryDraft {
  enabled: boolean;
  servers: string;
  mode: DirectoryMode;
  port: string;
  ca_certificate: string;
  bind_user: string;
  bind_password: string;
  base_dn: string;
  group_dn: string;
  session_days: string;
}

export const MODE_OPTIONS: { value: DirectoryMode; label: string }[] = [
  { value: "ldaps", label: "LDAPS" },
  { value: "starttls", label: "StartTLS" },
  { value: "plain", label: "Без шифрования" },
];

export const DEFAULT_PORTS: Record<DirectoryMode, number> = { ldaps: 636, starttls: 389, plain: 389 };

export function draftFrom(settings: DirectorySettings): DirectoryDraft {
  return {
    enabled: settings.enabled,
    servers: settings.servers,
    mode: settings.mode,
    port: settings.port === null ? "" : String(settings.port),
    ca_certificate: settings.ca_certificate,
    bind_user: settings.bind_user,
    bind_password: "",
    base_dn: settings.base_dn,
    group_dn: settings.group_dn,
    session_days: String(settings.session_days),
  };
}

export function formFrom(draft: DirectoryDraft): DirectoryForm {
  const port = String(draft.port ?? "").trim();
  return {
    ...draft,
    port: port ? Number(port) : null,
    session_days: Number(draft.session_days),
  };
}

export function sameDraft(left: DirectoryDraft, right: DirectoryDraft): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}
