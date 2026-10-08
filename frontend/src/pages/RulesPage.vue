<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { errorMessage } from "../api/http";
import { fetchLunchRules, saveLunchRules, type LunchRules } from "../api/lunchRules";
import { WEEKDAYS, draftFrom, formFrom, sameDraft, toggleDay, type RulesDraft } from "../components/rules/draft";
import AppButton from "../components/ui/AppButton.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import SwitchField from "../components/ui/SwitchField.vue";
import TextField from "../components/ui/TextField.vue";
import { useToasts } from "../composables/useToasts";
import { formatDateTime } from "../format/dateTime";

const rules = ref<LunchRules | null>(null);
const draft = ref<RulesDraft | null>(null);
const loadError = ref("");
const busy = ref(false);
const { notify, fail } = useToasts();

const dirty = computed(() => Boolean(rules.value && draft.value && !sameDraft(draftFrom(rules.value), draft.value)));
const limitHint = computed(() =>
  rules.value ? `От ${rules.value.min_limit_minutes} до ${rules.value.max_limit_minutes} мин. Уже начатые обеды считаются по прежнему лимиту` : "",
);

function accept(next: LunchRules): void {
  rules.value = next;
  draft.value = draftFrom(next);
}

async function load(): Promise<void> {
  loadError.value = "";
  try {
    accept(await fetchLunchRules());
  } catch (error) {
    loadError.value = errorMessage(error, "Не удалось загрузить правила обеда");
  }
}

async function save(): Promise<void> {
  if (!draft.value) {
    return;
  }
  busy.value = true;
  try {
    accept(await saveLunchRules(formFrom(draft.value)));
    notify("Правила обеда сохранены");
  } catch (error) {
    fail(errorMessage(error, "Не удалось сохранить. Проверьте поля и попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}

function revert(): void {
  if (rules.value) {
    draft.value = draftFrom(rules.value);
  }
}

onMounted(load);
</script>

<template>
  <section class="rules">
    <PageHeader title="Правила обеда" subtitle="Лимит, рабочие дни и время, когда можно уйти на обед" />
    <div v-if="loadError" class="panel rules__card rules__error" role="alert">
      <p>{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <form v-else-if="draft && rules" class="rules__form" novalidate @submit.prevent="save">
      <div class="panel rules__card">
        <h2 class="rules__title">Длительность</h2>
        <TextField v-model="draft.limit_minutes" class="rules__narrow" label="Лимит обеда, минут" type="number" :hint="limitHint" plain :disabled="busy" />
      </div>

      <div class="panel rules__card">
        <h2 class="rules__title">Рабочий день</h2>
        <div class="rules__field">
          <span id="workdays-label" class="rules__label">Рабочие дни</span>
          <div class="rules__days" role="group" aria-labelledby="workdays-label">
            <AppButton
              v-for="day in WEEKDAYS"
              :key="day.value"
              size="small"
              :aria-label="day.name"
              :pressed="draft.workdays.includes(day.value)"
              :disabled="busy"
              @click="draft.workdays = toggleDay(draft.workdays, day.value)"
            >
              {{ day.short }}
            </AppButton>
          </div>
          <span class="rules__note">В нерабочие дни кнопки обеда нет</span>
        </div>
        <TextField
          v-model="draft.day_end"
          class="rules__narrow"
          label="Конец рабочего дня"
          type="time"
          hint="Кто забыл нажать «Вернулся», тому обед закроется в это время со статусом «Возврат не отмечен»"
          plain
          :disabled="busy"
        />
      </div>

      <div class="panel rules__card">
        <SwitchField
          label="Окно обеда"
          hint="Уйти на обед можно только в заданные часы. Выключено — в любое время рабочего дня"
          :checked="draft.window_enabled"
          :disabled="busy"
          @change="draft.window_enabled = $event"
        />
        <div v-if="draft.window_enabled" class="rules__row">
          <TextField v-model="draft.window_start" label="С" type="time" plain :disabled="busy" />
          <TextField v-model="draft.window_end" label="До" type="time" plain :disabled="busy" />
        </div>
      </div>

      <div class="rules__actions">
        <AppButton type="submit" variant="primary" :disabled="busy || !dirty">Сохранить</AppButton>
        <AppButton v-if="dirty" variant="ghost" :disabled="busy" @click="revert">Отменить изменения</AppButton>
        <span class="rules__note">Изменено: {{ formatDateTime(rules.updated_at) }}</span>
      </div>
    </form>
    <div v-else class="panel rules__card rules__loading" aria-busy="true">Загружаем…</div>
  </section>
</template>

<style scoped>
.rules,
.rules__form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 880px;
}

.rules__card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 24px;
}

.rules__title {
  font-size: var(--text-h3);
}

.rules__narrow {
  max-width: 320px;
}

.rules__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rules__label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
}

.rules__days {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rules__days > * {
  min-width: 52px;
}

.rules__row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 200px));
  gap: 12px;
}

.rules__note {
  font-size: var(--text-small);
  color: var(--muted);
}

.rules__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.rules__error {
  align-items: flex-start;
}

.rules__error p {
  margin: 0;
  color: var(--red);
}

.rules__loading {
  color: var(--muted);
}

@media (max-width: 650px) {
  .rules__card {
    padding: 18px 16px;
  }

  .rules__narrow {
    max-width: none;
  }

  .rules__days > * {
    min-width: 0;
    flex: 1 1 0;
  }

  .rules__row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
