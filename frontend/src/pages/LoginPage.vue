<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { rabbitWanted } from "../api/appearance";
import AuthLayout, { type AuthState } from "../components/login/AuthLayout.vue";
import LoginForm from "../components/login/LoginForm.vue";
import LoginRabbit, { type Point } from "../components/login/LoginRabbit.vue";
import { FILL_MS, type Outcome } from "../components/login/rabbitPlot";
import ScreenFill from "../components/login/ScreenFill.vue";
import { stillMotion } from "../device/motion";
import { preloadScenes } from "../rabbit/frames";

const SHAKE_MS = 450;
const SUCCESS_PAUSE_MS = 1100;

const router = useRouter();
const state = ref<AuthState>("idle");
const rabbit = ref(false);
const flight = ref<{ outcome: Outcome; fill: Point | null } | null>(null);
let timer = 0;

function after(ms: number, action: () => void): void {
  window.clearTimeout(timer);
  timer = window.setTimeout(action, ms);
}

function enter(): void {
  void router.replace({ name: "home" });
}

function shake(): void {
  state.value = "error";
  after(SHAKE_MS, () => (state.value = "idle"));
}

function attempt(): void {
  if (rabbit.value) {
    flight.value = { outcome: "pending", fill: null };
  }
}

function fillFrom(center: Point): void {
  if (flight.value) {
    flight.value.fill = center;
  }
}

function settle(outcome: Outcome, fallback: () => void): void {
  if (flight.value) {
    flight.value.outcome = outcome;
  } else {
    fallback();
  }
}

function failed(): void {
  settle("failure", shake);
}

function succeeded(): void {
  settle("success", () => {
    state.value = "success";
    after(SUCCESS_PAUSE_MS, enter);
  });
}

function landed(): void {
  if (flight.value?.outcome === "success") {
    enter();
    return;
  }
  flight.value = null;
  shake();
}

onMounted(async () => {
  rabbit.value = !stillMotion() && (await rabbitWanted());
  if (rabbit.value) {
    preloadScenes(["tap", "start", "run", "dive", "no"]);
  }
});

onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<template>
  <AuthLayout title="Вход" :state="state">
    <LoginForm :melted="flight !== null" @attempt="attempt" @success="succeeded" @failure="failed">
      <template #launch>
        <Transition name="rabbit-melt">
          <LoginRabbit v-if="flight" :outcome="flight.outcome" @fill="fillFrom" @done="landed" />
        </Transition>
      </template>
    </LoginForm>
  </AuthLayout>
  <span v-if="flight?.outcome === 'success'" class="visually-hidden" role="status">Вход выполнен</span>
  <ScreenFill v-if="flight?.fill" :x="flight.fill.x" :y="flight.fill.y" :duration="FILL_MS" />
</template>

<style scoped>
.rabbit-melt-leave-active {
  transition:
    opacity 240ms ease,
    filter 240ms ease;
}

.rabbit-melt-leave-to {
  opacity: 0;
  filter: blur(8px) brightness(3);
}
</style>
