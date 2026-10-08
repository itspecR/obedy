<script setup lang="ts">
import BrandMark from "../ui/BrandMark.vue";
import LoginArt from "./LoginArt.vue";

defineProps<{ title: string }>();
</script>

<template>
  <div class="auth">
    <LoginArt class="auth__art" />
    <main class="auth__main">
      <div class="auth__column">
        <BrandMark class="auth__brand" :caption="false" />
        <p class="eyebrow">Учёт обеденных перерывов</p>
        <h1 class="auth__title">{{ title }}</h1>
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  min-height: 100vh;
}

.auth__main {
  display: grid;
  place-items: center;
  padding: 40px 24px;
}

.auth__column {
  width: 100%;
  max-width: 390px;
}

.auth__brand {
  display: none;
  margin-bottom: 28px;
}

.auth__title {
  margin-bottom: 24px;
  font-size: 32px;
}

@media (max-width: 1150px) {
  .auth {
    grid-template-columns: 0.8fr 1fr;
  }
}

@media (max-width: 850px) {
  .auth {
    grid-template-columns: 1fr;
  }

  .auth__art {
    display: none;
  }

  .auth__brand {
    display: flex;
  }

  .auth__main {
    padding: 32px 14px;
  }
}
</style>
