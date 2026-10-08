<script setup lang="ts">
import { computed } from "vue";
import PageHeader from "../components/ui/PageHeader.vue";
import { shortName } from "../navigation";
import { useSession } from "../stores/session";

const session = useSession();
const greeting = computed(() => `Здравствуйте, ${shortName(session.me?.display_name ?? "")}`);
</script>

<template>
  <section class="lunch">
    <PageHeader title="Обед" :subtitle="greeting" />
    <div class="panel lunch__empty">
      <p class="lunch__empty-title">Отметка обеда пока не включена</p>
      <p class="lunch__empty-text">Кнопки «Ушёл на обед» и «Вернулся» появятся здесь после настройки системы администратором.</p>
    </div>
  </section>
</template>

<style scoped>
.lunch {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lunch__empty {
  padding: 32px 24px;
  text-align: center;
}

.lunch__empty-title {
  margin: 0 0 6px;
  font-size: var(--text-h3);
  font-weight: 600;
}

.lunch__empty-text {
  margin: 0;
  color: var(--muted);
}
</style>
