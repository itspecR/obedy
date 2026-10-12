<script setup lang="ts">
export type BadgeKind = "success" | "refused" | "farewell";

withDefaults(defineProps<{ kind: BadgeKind; leaving?: boolean }>(), { leaving: false });
</script>

<template>
  <div class="auth-badge" :class="[`auth-badge--${kind}`, { 'auth-badge--leaving': leaving }]" aria-hidden="true">
    <svg v-if="kind === 'success'" viewBox="0 0 24 24">
      <path class="auth-badge__stroke" pathLength="1" d="M5 12.5l4.5 4.5L19 7.5" />
    </svg>
    <svg v-else-if="kind === 'refused'" viewBox="0 0 24 24">
      <path class="auth-badge__stroke" pathLength="1" d="M7 7l10 10" />
      <path class="auth-badge__stroke auth-badge__stroke--second" pathLength="1" d="M17 7L7 17" />
    </svg>
    <svg v-else viewBox="0 0 20 20">
      <path class="auth-badge__stroke" pathLength="1" d="M8 3.5H4.75a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1H8" />
      <path class="auth-badge__stroke auth-badge__stroke--second" pathLength="1" d="M8 10h8" />
      <path class="auth-badge__stroke auth-badge__stroke--third" pathLength="1" d="M12.5 6.5 16 10l-3.5 3.5" />
    </svg>
  </div>
</template>

<style scoped>
.auth-badge {
  --tone: var(--green);
  --tone-bg: var(--green-bg);
  --tone-line: var(--green-line);
  --stroke-ms: 360ms;
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  border: 2px solid var(--tone);
  border-radius: 50%;
  background: var(--tone-bg);
  box-shadow: 0 0 32px var(--tone-line);
  animation: auth-badge-pop 380ms cubic-bezier(0.2, 0.8, 0.2, 1) 340ms backwards;
}

.auth-badge--refused {
  --tone: var(--red);
  --tone-bg: var(--red-bg);
  --tone-line: var(--red-line);
  --stroke-ms: 220ms;
}

.auth-badge--farewell {
  --tone: var(--muted);
  --tone-bg: var(--gray-bg);
  --tone-line: var(--gray-line);
  --stroke-ms: 180ms;
}

.auth-badge--leaving {
  animation: auth-badge-vanish 200ms ease-in forwards;
}

.auth-badge--leaving .auth-badge__stroke {
  animation: none;
}

.auth-badge svg {
  width: 44px;
  height: 44px;
  fill: none;
  stroke: var(--tone);
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.auth-badge--farewell svg {
  stroke-width: 2;
}

.auth-badge__stroke {
  stroke-dasharray: 1;
  stroke-dashoffset: 0;
  animation: auth-badge-draw var(--stroke-ms) ease-out 560ms backwards;
}

.auth-badge__stroke--second {
  animation-delay: 760ms;
}

.auth-badge__stroke--third {
  animation-delay: 900ms;
}

.auth-badge--farewell .auth-badge__stroke--second {
  animation-delay: 700ms;
}

.auth-badge--farewell .auth-badge__stroke--third {
  animation-delay: 800ms;
}

@media (prefers-reduced-motion: reduce) {
  .auth-badge--leaving {
    visibility: hidden;
  }
}

@keyframes auth-badge-pop {
  from {
    opacity: 0;
    transform: scale(0.3);
  }
  70% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@keyframes auth-badge-draw {
  from {
    stroke-dashoffset: 1;
  }
}

@keyframes auth-badge-vanish {
  to {
    opacity: 0;
    transform: scale(0.3);
  }
}
</style>
