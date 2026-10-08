<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { errorMessage } from "../api/http";
import { fetchStaff, type StaffMember } from "../api/staff";
import StaffFilters from "../components/staff/StaffFilters.vue";
import StaffList from "../components/staff/StaffList.vue";
import { EMPTY_FILTER, filterStaff, type StaffFilter } from "../components/staff/filters";
import AppButton from "../components/ui/AppButton.vue";
import PageHeader from "../components/ui/PageHeader.vue";

const members = ref<StaffMember[] | null>(null);
const loadError = ref("");
const filter = ref<StaffFilter>({ ...EMPTY_FILTER });

const shown = computed(() => filterStaff(members.value ?? [], filter.value));
const subtitle = computed(() => {
  const total = members.value?.length ?? 0;
  return shown.value.length === total ? `Всего ${total}` : `Показано ${shown.value.length} из ${total}`;
});

async function load(): Promise<void> {
  loadError.value = "";
  try {
    members.value = await fetchStaff();
  } catch (error) {
    loadError.value = errorMessage(error, "Не удалось загрузить список сотрудников");
  }
}

onMounted(load);
</script>

<template>
  <section class="staff-page">
    <PageHeader title="Сотрудники" :subtitle="members ? subtitle : 'Все, кто может входить на сайт'" />
    <div v-if="loadError" class="panel staff-page__error" role="alert">
      <p>{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <template v-else-if="members">
      <StaffFilters v-model="filter" />
      <StaffList :members="shown" :total="members.length" />
    </template>
    <div v-else class="panel staff-page__loading" aria-busy="true">Загружаем…</div>
  </section>
</template>

<style scoped>
.staff-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1100px;
}

.staff-page__error,
.staff-page__loading {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding: 22px 24px;
}

.staff-page__error p {
  margin: 0;
  color: var(--red);
}

.staff-page__loading {
  color: var(--muted);
}
</style>
