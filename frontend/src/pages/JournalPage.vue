<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import type { Person } from "../api/board";
import { errorMessage } from "../api/http";
import { fetchJournal, fetchJournalPeople, fetchSystem, type JournalEntry, type JournalQuery, type SystemInfo } from "../api/journal";
import { ALL_CATEGORIES, CATEGORY_OPTIONS, categoryOf, recentPeriod, type CategoryChoice } from "../components/journal/entries";
import JournalList from "../components/journal/JournalList.vue";
import SystemPanel from "../components/journal/SystemPanel.vue";
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
const system = ref<SystemInfo | null>(null);
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

async function loadSystem(): Promise<void> {
  try {
    system.value = await fetchSystem();
  } catch (error) {
    fail(errorMessage(error, "Не удалось загрузить сведения о сервере"));
  }
}

watch(query, reload);
onMounted(() => {
  reload();
  void loadPeople();
  void loadSystem();
});
</script>

<template>
  <section class="journal">
    <PageHeader title="Log" subtitle="Кто, когда и что изменил. Записи хранятся 3 года" />

    <div class="journal__layout">
      <div class="journal__main">
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
      </div>
      <aside class="journal__side">
        <SystemPanel v-if="system" :info="system" />
      </aside>
    </div>
  </section>
</template>

<style scoped>
.journal {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.journal__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 20px;
}

.journal__main {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

@media (min-width: 1200px) {
  .journal__layout {
    grid-template-columns: minmax(0, 1fr) minmax(300px, 380px);
  }

  .journal__side {
    position: sticky;
    top: 24px;
  }
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
