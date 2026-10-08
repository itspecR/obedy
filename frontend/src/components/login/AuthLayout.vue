<script setup lang="ts">
import BrandMark from "../ui/BrandMark.vue";

defineProps<{ title: string }>();
</script>

<template>
  <main class="auth">
    <section class="auth__card glass-card" :aria-label="title">
      <BrandMark class="auth__brand" />
      <h1 class="auth__title">{{ title }}</h1>
      <slot />
    </section>
  </main>
</template>

<style scoped>
.auth {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 16px;
}

.auth__card {
  width: min(440px, 100%);
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
