import { defineStore } from "pinia";
import { computed, ref } from "vue";
import * as auth from "../api/auth";
import { ApiError } from "../api/http";

export const useSession = defineStore("session", () => {
  const me = ref<auth.Me | null>(null);
  const loaded = ref(false);

  const isLoggedIn = computed(() => me.value !== null);
  const mustChangePassword = computed(() => me.value?.must_change_password === true);

  async function load(): Promise<void> {
    try {
      me.value = await auth.fetchMe();
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) {
        throw error;
      }
      me.value = null;
    } finally {
      loaded.value = true;
    }
  }

  async function signIn(credentials: auth.Credentials): Promise<void> {
    me.value = await auth.login(credentials);
  }

  async function changePassword(next: string, current?: string): Promise<void> {
    me.value = await auth.changePassword(next, current);
  }

  async function signOut(): Promise<void> {
    try {
      await auth.logout();
    } finally {
      me.value = null;
    }
  }

  function forget(): void {
    me.value = null;
  }

  return { me, loaded, isLoggedIn, mustChangePassword, load, signIn, changePassword, signOut, forget };
});
