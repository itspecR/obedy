<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { rabbitWanted } from "../api/appearance";
import AuthLayout from "../components/login/AuthLayout.vue";
import { refusing, type AuthState } from "../components/login/authState";
import LoginForm from "../components/login/LoginForm.vue";
import LoginRabbit, { type Point } from "../components/login/LoginRabbit.vue";
import { FILL_MS, type Outcome } from "../components/login/rabbitPlot";
import ScreenFill from "../components/login/ScreenFill.vue";
import { markArrival } from "../composables/useArrival";
import { stillMotion } from "../device/motion";
import { preloadScenes } from "../rabbit/frames";

const SHAKE_MS = 450;
const SUCCESS_PAUSE_MS = 1100;
const REFUSAL_PAUSE_MS = 1200;
const UNFOLD_MS = 420;

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

function arrive(): void {
  markArrival();
  enter();
}

function shake(): void {
  state.value = "error";
  after(SHAKE_MS, () => (state.value = "idle"));
}

function refuse(): void {
  state.value = "failure";
  after(REFUSAL_PAUSE_MS, () => {
    state.value = "recovery";
    after(UNFOLD_MS, () => (state.value = "idle"));
  });
}

function greetReturn(): void {
  if (!window.history.state?.farewell) {
    return;
  }
  window.history.replaceState({ ...window.history.state, farewell: false }, "");
  state.value = "return";
  after(UNFOLD_MS, () => (state.value = "idle"));
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
  settle("failure", refuse);
}

function succeeded(): void {
  settle("success", () => {
    state.value = "success";
    after(SUCCESS_PAUSE_MS, arrive);
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
  greetReturn();
  rabbit.value = !stillMotion() && (await rabbitWanted());
  if (rabbit.value) {
    preloadScenes(["tap", "start", "run", "dive", "no"]);
  }
});

onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<template>
  <AuthLayout title="Вход" :state="state">
    <LoginForm :melted="flight !== null" :held="refusing(state)" @attempt="attempt" @success="succeeded" @failure="failed">
      <template #launch="{ button }">
        <LoginRabbit v-if="flight" :outcome="flight.outcome" :button="button" @fill="fillFrom" @done="landed" />
      </template>
    </LoginForm>
  </AuthLayout>
  <span v-if="flight?.outcome === 'success'" class="visually-hidden" role="status">Вход выполнен</span>
  <ScreenFill v-if="flight?.fill" :x="flight.fill.x" :y="flight.fill.y" :duration="FILL_MS" />
</template>

