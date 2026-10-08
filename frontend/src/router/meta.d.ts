import "vue-router";
import type { Role } from "../api/auth";

declare module "vue-router" {
  interface RouteMeta {
    guest?: boolean;
    roles?: Role[];
    title?: string;
  }
}
