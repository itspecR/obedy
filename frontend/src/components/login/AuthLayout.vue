<script setup lang="ts">
import { computed } from "vue";
import BrandMark from "../ui/BrandMark.vue";
import AuthBadge from "./AuthBadge.vue";
import { badgeOf, type AuthState } from "./authState";

const props = withDefaults(defineProps<{ title: string; state?: AuthState }>(), { state: "idle" });

const badge = computed(() => badgeOf(props.state));
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
      <AuthBadge v-if="badge" class="auth__badge" :class="{ 'auth__badge--screen': state === 'return' }" :kind="badge.kind" :leaving="badge.leaving" />
      <span v-if="state === 'success'" class="visually-hidden" role="status">Вход выполнен</span>
    </div>
  </main>
</template>

<style scoped>
.auth {
  --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
  --collapse: 420ms;
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
.auth__badge {
  grid-area: 1 / 1;
}

.auth__badge {
  place-self: center;
}

.auth__badge--screen {
  position: fixed;
  top: 50%;
  left: 50%;
  translate: -50% -50%;
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

.auth__card--success,
.auth__card--failure {
  animation: auth-fold var(--collapse) var(--ease-in-out) 120ms forwards;
  pointer-events: none;
}

.auth__card--success .auth__content,
.auth__card--failure .auth__content {
  animation: auth-fade 180ms ease-in forwards;
}

.auth__card--recovery,
.auth__card--return {
  animation: auth-fold var(--collapse) var(--ease-in-out) reverse backwards;
  pointer-events: none;
}

.auth__card--recovery .auth__content,
.auth__card--return .auth__content {
  animation: auth-fade 180ms ease-out 240ms reverse backwards;
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

@keyframes auth-fold {
  to {
    border-radius: 240px;
    opacity: 0;
    transform: scale(0.2);
  }
}

@keyframes auth-fade {
  to {
    opacity: 0;
    transform: scale(0.92);
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth__card--success,
  .auth__card--failure {
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
    border-radius: var(--radius-card-compact);
  }

  .auth__title {
    font-size: 26px;
  }
}
</style>
