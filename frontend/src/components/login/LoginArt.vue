<script setup lang="ts">
import BrandMark from "../ui/BrandMark.vue";
</script>

<template>
  <aside class="art">
    <BrandMark on-dark />
    <div class="art__glass">
      <p class="art__title">Ушёл — вернулся</p>
      <p class="art__subtitle">Отметьте начало и конец обеда одной кнопкой</p>
    </div>
    <span aria-hidden="true" />
  </aside>
</template>

<style scoped>
.art {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100vh;
  overflow: hidden;
  padding: 40px 48px;
  background: var(--login-art);
  color: var(--login-art-text);
}

.art::before,
.art::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  filter: blur(8px);
  pointer-events: none;
}

.art::before {
  top: 18%;
  right: -60px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.35), rgba(255, 255, 255, 0));
}

.art::after {
  bottom: 8%;
  left: -40px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle at 60% 40%, rgba(160, 200, 255, 0.4), rgba(160, 200, 255, 0));
}

.art__glass {
  position: relative;
  z-index: 1;
  max-width: 420px;
  padding: 28px 30px;
  border: 1px solid var(--glass-edge);
  border-radius: 28px;
  background: var(--glass-fill);
  box-shadow: 0 20px 50px rgba(8, 20, 50, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(22px) saturate(160%);
  -webkit-backdrop-filter: blur(22px) saturate(160%);
}

.art__title {
  margin: 0 0 8px;
  font-family: var(--font-display);
  font-size: 34px;
  line-height: 1.1;
  font-weight: 600;
  color: #fff;
}

.art__subtitle {
  margin: 0;
  font-size: 15px;
}

@media (max-width: 1150px) {
  .art {
    padding: 32px;
  }
}
</style>
