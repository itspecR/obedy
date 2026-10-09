<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";
import AuthLayout, { type AuthState } from "../components/login/AuthLayout.vue";
import LoginForm from "../components/login/LoginForm.vue";

const SHAKE_MS = 450;
const SUCCESS_PAUSE_MS = 1100;

const router = useRouter();
const state = ref<AuthState>("idle");
let timer = 0;

function after(ms: number, action: () => void): void {
  window.clearTimeout(timer);
  timer = window.setTimeout(action, ms);
}

function failed(): void {
  state.value = "error";
  after(SHAKE_MS, () => (state.value = "idle"));
}

function succeeded(): void {
  state.value = "success";
  after(SUCCESS_PAUSE_MS, () => void router.replace({ name: "home" }));
}

onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<template>
  <AuthLayout title="Вход" :state="state">
    <LoginForm @success="succeeded" @failure="failed" />
  </AuthLayout>
</template>
