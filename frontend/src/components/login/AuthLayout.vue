<script setup lang="ts">
import BrandMark from "../ui/BrandMark.vue";

export type AuthState = "idle" | "error" | "success";

withDefaults(defineProps<{ title: string; state?: AuthState }>(), { state: "idle" });
</script>

<template>
  <main class="auth">
    <div class="auth__stage">
      <section class="auth__card glass-card" :class="`auth__card--${state}`" :aria-label="title">
        <div class="auth__content">
          <BrandMark class="auth__brand" />
          <h1 class="auth__title">{{ title }}</h1>
          <slot />
        </div>
      </section>
      <div v-if="state === 'success'" class="auth__done" role="status">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
        <span class="visually-hidden">Вход выполнен</span>
      </div>
    </div>
  </main>
</template>

<style scoped>
.auth {
  --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
  --collapse: 420ms;
  --done-size: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 16px;
}

.auth__stage {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  width: min(440px, 100%);
}

.auth__card,
.auth__done {
  grid-area: 1 / 1;
}

.auth__card {
  padding: 36px 36px 32px;
}

.auth__brand {
  margin-bottom: 28px;
}

.auth__title {
  margin-bottom: 24px;
  font-size: 30px;
  letter-spacing: -0.5px;
}

.auth__card--error {
  animation: auth-shake 450ms var(--ease-out);
}

.auth__card--success {
  animation: auth-collapse var(--collapse) cubic-bezier(0.5, 0, 0.2, 1) 120ms forwards;
  pointer-events: none;
}

.auth__card--success .auth__content {
  animation: auth-fade 180ms ease-in forwards;
}

.auth__done {
  display: grid;
  place-items: center;
  place-self: center;
  width: var(--done-size);
  height: var(--done-size);
  border: 2px solid var(--green);
  border-radius: 50%;
  background: var(--green-bg);
  box-shadow: 0 0 32px var(--green-line);
  animation: auth-pop 380ms var(--ease-out) 340ms backwards;
}

.auth__done svg {
  width: 44px;
  height: 44px;
  fill: none;
  stroke: var(--green);
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 24;
  stroke-dashoffset: 0;
  animation: auth-draw 360ms ease-out 560ms backwards;
}

@keyframes auth-shake {
  0%,
  100% {
    transform: translateX(0);
  }
  20%,
  60% {
    transform: translateX(-10px);
  }
  40%,
  80% {
    transform: translateX(10px);
  }
}

@keyframes auth-fade {
  to {
    opacity: 0;
    transform: scale(0.92);
  }
}

@keyframes auth-collapse {
  60% {
    border-radius: 160px;
    opacity: 0.7;
    transform: scale(0.4);
  }
  to {
    border-radius: 240px;
    opacity: 0;
    transform: scale(0.2);
  }
}

@keyframes auth-pop {
  from {
    opacity: 0;
    transform: scale(0.3);
  }
  70% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@keyframes auth-draw {
  from {
    stroke-dashoffset: 24;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth__card--success {
    visibility: hidden;
  }
}

@media (max-width: 650px) {
  .auth {
    align-items: flex-start;
    padding: 24px 12px;
  }

  .auth__card {
    padding: 28px 20px 24px;
    border-radius: 24px;
  }

  .auth__title {
    font-size: 26px;
  }
}
</style>
