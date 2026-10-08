<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { mayLeaveAll } from "../../composables/useLeaveGuard";
import { useSession } from "../../stores/session";
import ProfileDialog from "./ProfileDialog.vue";
import SideNav from "./SideNav.vue";

const session = useSession();
const router = useRouter();
const profileOpen = ref(false);


async function logout(): Promise<void> {
  if (!(await mayLeaveAll())) {
    return;
  }
  await session.signOut();
  await router.replace({ name: "login" });
}
</script>

<template>
  <div v-if="session.me" class="shell">
    <SideNav :me="session.me" @logout="logout" @open-profile="profileOpen = true" />
    <div class="shell__main">
      <main class="shell__content">
        <RouterView />
      </main>
    </div>
    <ProfileDialog v-if="profileOpen" :me="session.me" @close="profileOpen = false" />
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 224px minmax(0, 1fr);
  min-height: 100vh;
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
