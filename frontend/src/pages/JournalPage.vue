<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import type { Person } from "../api/board";
import { errorMessage } from "../api/http";
import { fetchJournal, fetchJournalPeople, type JournalEntry, type JournalQuery } from "../api/journal";
import { ALL_CATEGORIES, CATEGORY_OPTIONS, categoryOf, recentPeriod, type CategoryChoice } from "../components/journal/entries";
import JournalList from "../components/journal/JournalList.vue";
import AppButton from "../components/ui/AppButton.vue";
import ChoiceField from "../components/ui/ChoiceField.vue";
import DateField from "../components/ui/DateField.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import PersonPicker from "../components/ui/PersonPicker.vue";
import { useToasts } from "../composables/useToasts";
import { isoDay } from "../format/dateTime";

const today = isoDay(new Date());
const period = ref(recentPeriod(today));
const person = ref<number | null>(null);
const category = ref<CategoryChoice>(ALL_CATEGORIES);
const people = ref<Person[]>([]);
const entries = ref<JournalEntry[]>([]);
const hasMore = ref(false);
const loaded = ref(false);
const loading = ref(false);
const loadError = ref("");
const { fail } = useToasts();
let generation = 0;

const query = computed<JournalQuery>(() => ({
  date_from: period.value.from,
  date_to: period.value.to,
  person: person.value,
  category: categoryOf(category.value),
}));

async function fetchPage(before?: number): Promise<void> {
  const current = ++generation;
  loading.value = true;
  try {
    const page = await fetchJournal({ ...query.value, before });
    if (current !== generation) {
      return;
    }
    entries.value = before ? [...entries.value, ...page.entries] : page.entries;
    hasMore.value = page.has_more;
    loaded.value = true;
    loadError.value = "";
  } catch (error) {
    if (current !== generation) {
      return;
    }
    const message = errorMessage(error, "Не удалось загрузить журнал");
    if (loaded.value) {
      fail(message);
    } else {
      loadError.value = message;
    }
  } finally {
    if (current === generation) {
      loading.value = false;
    }
  }
}

function reload(): void {
  if (period.value.from && period.value.to) {
    void fetchPage();
  }
}

function loadMore(): void {
  const last = entries.value.at(-1);
  if (last) {
    void fetchPage(last.id);
  }
}

async function loadPeople(): Promise<void> {
  try {
    people.value = await fetchJournalPeople();
  } catch (error) {
    fail(errorMessage(error, "Не удалось загрузить список сотрудников"));
  }
}

watch(query, reload);
onMounted(() => {
  reload();
  void loadPeople();
});
</script>

<template>
  <section class="journal">
    <PageHeader title="Журнал действий" subtitle="Кто, когда и что изменил. Записи хранятся 3 года" />

    <div class="panel journal__filters">
      <div class="journal__fields">
        <DateField v-model="period.from" label="С" :max="today" />
        <DateField v-model="period.to" label="По" :max="today" />
        <PersonPicker v-model="person" label="Сотрудник" :people="people" placeholder="Все сотрудники" />
      </div>
      <ChoiceField v-model="category" label="Вид действия" :options="CATEGORY_OPTIONS" />
    </div>

    <div v-if="loadError" class="panel journal__message" role="alert">
      <p class="journal__error">{{ loadError }}</p>
      <AppButton @click="reload">Повторить</AppButton>
    </div>
    <div v-else-if="!loaded" class="panel journal__message" aria-busy="true">Загружаем…</div>
    <JournalList v-else :entries="entries" :has-more="hasMore" :loading="loading" @more="loadMore" />
  </section>
</template>

<style scoped>
.journal {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.journal__filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px;
}

.journal__fields {
  display: grid;
  grid-template-columns: 180px 180px minmax(0, 1fr);
  gap: 12px;
}

.journal__message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 24px;
  color: var(--muted);
}

.journal__message p {
  margin: 0;
}

.journal__error {
  color: var(--red);
}

@media (max-width: 1100px) {
  .journal__fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .journal__fields > :last-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 650px) {
  .journal__filters {
    padding: 16px;
  }
}
</style>
