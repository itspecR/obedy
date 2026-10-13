<script setup lang="ts">
import { onMounted, ref } from "vue";
import { errorMessage } from "../../api/http";
import { addCalendarDay, fetchCalendar, removeCalendarDay, type CalendarDay } from "../../api/lunchRules";
import { formatDay, todayIso } from "../../format/dateTime";
import { useToasts } from "../../composables/useToasts";
import AppButton from "../ui/AppButton.vue";
import ChoiceField from "../ui/ChoiceField.vue";
import DateField from "../ui/DateField.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import { KIND_OPTIONS, entryOf, kindLabel, kindTone, yearOf, type DayKind } from "./calendarDays";

const year = ref(yearOf(todayIso()));
const days = ref<CalendarDay[] | null>(null);
const loadError = ref("");
const busy = ref(false);
const newDay = ref("");
const kind = ref<DayKind>("holiday");
const dayError = ref("");
const { notify, fail } = useToasts();

async function load(next: number): Promise<void> {
  busy.value = true;
  loadError.value = "";
  try {
    days.value = await fetchCalendar(next);
    year.value = next;
  } catch (error) {
    loadError.value = errorMessage(error, "Не удалось загрузить календарь");
  } finally {
    busy.value = false;
  }
}

async function change(action: () => Promise<CalendarDay[]>, shownYear: number, done: string): Promise<boolean> {
  busy.value = true;
  try {
    days.value = await action();
    year.value = shownYear;
    notify(done);
    return true;
  } catch (error) {
    fail(errorMessage(error, "Не удалось сохранить. Попробуйте ещё раз"));
    return false;
  } finally {
    busy.value = false;
  }
}

async function add(): Promise<void> {
  dayError.value = newDay.value ? "" : "Выберите дату";
  if (dayError.value) {
    return;
  }
  if (await change(() => addCalendarDay(entryOf(newDay.value, kind.value)), yearOf(newDay.value), "День добавлен в календарь")) {
    newDay.value = "";
  }
}

function remove(entry: CalendarDay): void {
  void change(() => removeCalendarDay(entry.day), year.value, "День убран из календаря");
}

onMounted(() => load(year.value));
</script>

<template>
  <section class="panel calendar" aria-labelledby="calendar-title">
    <header class="calendar__head">
      <div>
        <h2 id="calendar-title" class="calendar__title">Праздники и переносы</h2>
        <p class="calendar__text">Дни, которые отличаются от обычной недели: праздники и рабочие субботы из производственного календаря.</p>
      </div>
      <div class="calendar__years">
        <AppButton variant="ghost" size="small" aria-label="Предыдущий год" :disabled="busy" @click="load(year - 1)">‹</AppButton>
        <span class="calendar__year">{{ year }}</span>
        <AppButton variant="ghost" size="small" aria-label="Следующий год" :disabled="busy" @click="load(year + 1)">›</AppButton>
      </div>
    </header>

    <form class="calendar__form" novalidate @submit.prevent="add">
      <div class="calendar__date">
        <DateField v-model="newDay" label="Дата" :disabled="busy" />
        <p v-if="dayError" class="calendar__error" role="alert">{{ dayError }}</p>
      </div>
      <ChoiceField v-model="kind" label="Этот день" :options="KIND_OPTIONS" :disabled="busy" />
      <AppButton type="submit" variant="primary" class="calendar__add" :disabled="busy">Добавить</AppButton>
    </form>

    <div v-if="loadError" class="calendar__failed" role="alert">
      <p>{{ loadError }}</p>
      <AppButton size="small" @click="load(year)">Повторить</AppButton>
    </div>
    <ul v-else-if="days && days.length" class="calendar__list">
      <li v-for="entry in days" :key="entry.day" class="calendar__row">
        <span class="calendar__day">{{ formatDay(entry.day) }}</span>
        <StatusBadge :tone="kindTone(entry)" :label="kindLabel(entry)" />
        <AppButton size="small" :disabled="busy" :aria-label="`Убрать ${formatDay(entry.day)}`" @click="remove(entry)">Убрать</AppButton>
      </li>
    </ul>
    <div v-else-if="days" class="calendar__empty">
      <p class="calendar__empty-title">На {{ year }} год ничего не добавлено</p>
      <p class="calendar__empty-text">Пока здесь пусто, рабочими считаются дни недели, отмеченные выше.</p>
    </div>
  </section>
</template>

<style scoped>
.calendar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 24px;
}

.calendar__head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.calendar__title {
  font-size: var(--text-h3);
}

.calendar__text {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: var(--text-small);
}

.calendar__years {
  display: flex;
  align-items: center;
  gap: 4px;
}

.calendar__year {
  min-width: 48px;
  font-weight: 600;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.calendar__form {
  display: grid;
  grid-template-columns: minmax(0, 220px) auto auto;
  align-items: end;
  justify-content: start;
  gap: 12px;
}

.calendar__date {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.calendar__add {
  min-height: 46px;
}

.calendar__error,
.calendar__failed p {
  margin: 0;
  color: var(--red);
  font-size: var(--text-small);
}

.calendar__failed {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.calendar__list {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}

.calendar__row {
  display: grid;
  grid-template-columns: minmax(120px, auto) minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 10px 4px;
  border-top: 1px solid var(--line);
}

.calendar__row:first-child {
  border-top: 0;
}

.calendar__day {
  font-variant-numeric: tabular-nums;
}

.calendar__row :deep(.badge) {
  justify-self: start;
}

.calendar__empty {
  padding: 12px 4px 4px;
  text-align: center;
}

.calendar__empty-title {
  margin: 0 0 4px;
  font-weight: 600;
}

.calendar__empty-text {
  margin: 0;
  color: var(--muted);
}

@media (max-width: 650px) {
  .calendar {
    padding: 18px 16px;
  }

  .calendar__form {
    grid-template-columns: minmax(0, 1fr);
  }

  .calendar__row {
    grid-template-columns: minmax(0, 1fr) auto auto;
    gap: 10px;
  }
}
</style>
