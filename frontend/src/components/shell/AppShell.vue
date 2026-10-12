<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { mayLeaveAll } from "../../composables/useLeaveGuard";
import { stillMotion } from "../../device/motion";
import { useSession } from "../../stores/session";
import AuthBadge from "../login/AuthBadge.vue";
import ProfileDialog from "./ProfileDialog.vue";
import SideNav from "./SideNav.vue";

const FAREWELL_MS = 1000;

const session = useSession();
const router = useRouter();
const profileOpen = ref(false);
const leaving = ref(false);
const origin = ref("");
let signingOut = false;

function pause(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waveGoodbye(): Promise<void> {
  origin.value = `50% ${window.scrollY + window.innerHeight / 2}px`;
  leaving.value = true;
  await pause(FAREWELL_MS);
}

async function logout(): Promise<void> {
  if (signingOut || !(await mayLeaveAll())) {
    return;
  }
  signingOut = true;
  const farewell = !stillMotion();
  if (farewell) {
    await waveGoodbye();
  }
  await session.signOut();
  await router.replace({ name: "login", state: { farewell } });
}
</script>

<template>
  <div v-if="session.me" class="shell" :class="{ 'shell--leaving': leaving }" :style="leaving ? { transformOrigin: origin } : undefined">
    <SideNav :me="session.me" @logout="logout" @open-profile="profileOpen = true" />
    <div class="shell__main">
      <main class="shell__content">
        <RouterView />
      </main>
    </div>
    <ProfileDialog v-if="profileOpen" :me="session.me" @close="profileOpen = false" />
  </div>
  <div v-if="leaving" class="farewell">
    <AuthBadge kind="farewell" />
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 224px minmax(0, 1fr);
  min-height: 100vh;
}

.shell--leaving {
  --glass-blur: none;
  --card-fill: var(--surface-glass-strong);
  animation: shell-fold 520ms var(--ease-in-out) forwards;
  pointer-events: none;
  will-change: transform, opacity;
}

.shell--leaving :deep(.glass__warp) {
  backdrop-filter: none;
}

@keyframes shell-fold {
  to {
    opacity: 0;
    transform: scale(0.18);
  }
}

.farewell {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  pointer-events: none;
}

.shell__main {
  min-width: 0;
}

.shell__content {
  max-width: 1672px;
  margin: 0 auto;
  padding: 28px 36px 60px;
}

@media (max-width: 1150px) {
  .shell {
    grid-template-columns: 185px minmax(0, 1fr);
  }
}

@media (max-width: 850px) {
  .shell {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto 1fr;
  }
}

@media (max-width: 650px) {
  .shell__content {
    padding: 20px 14px 40px;
  }
}
</style>
