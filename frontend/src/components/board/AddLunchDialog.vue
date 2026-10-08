<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { addLunch, fetchBoardPeople, type BoardEntry, type Person } from "../../api/board";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import { formatDay } from "../../format/dateTime";
import { matchesQuery } from "../../format/search";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import SelectField from "../ui/SelectField.vue";
import TextAreaField from "../ui/TextAreaField.vue";
import TextField from "../ui/TextField.vue";

const NOBODY = "";

const props = defineProps<{ day: string }>();
const emit = defineEmits<{ close: []; saved: [entry: BoardEntry] }>();

const people = ref<Person[]>([]);
const query = ref("");
const personId = ref(NOBODY);
const startedAt = ref("");
const endedAt = ref("");
const reason = ref("");
const busy = ref(false);
const { notify, fail } = useToasts();

const options = computed(() => [
  { value: NOBODY, label: "Выберите сотрудника" },
  ...people.value
    .filter((person) => String(person.id) === personId.value || matchesQuery(query.value, [person.name, person.login]))
    .map((person) => ({ value: String(person.id), label: person.name })),
]);
const ready = computed(() => Boolean(personId.value && startedAt.value && endedAt.value && reason.value.trim()));

async function loadPeople(): Promise<void> {
  try {
    people.value = await fetchBoardPeople();
  } catch (error) {
    fail(errorMessage(error, "Не удалось загрузить список сотрудников"));
  }
}

async function save(): Promise<void> {
  busy.value = true;
  try {
    const entry = await addLunch({
      account_id: Number(personId.value),
      day: props.day,
      started_at: startedAt.value,
      ended_at: endedAt.value,
      reason: reason.value,
    });
    notify("Обед добавлен");
    emit("saved", entry);
  } catch (error) {
    fail(errorMessage(error, "Не удалось добавить обед. Попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}

onMounted(loadPeople);
</script>

<template>
  <AppModal title="Добавить обед" :eyebrow="formatDay(day)" @close="emit('close')">
    <form class="add-lunch" novalidate @submit.prevent="save">
      <p class="add-lunch__note">Для сотрудника, который забыл нажать «Ушёл на обед». Он увидит, кто и почему добавил обед.</p>
      <TextField v-model="query" label="Найти сотрудника" icon="search" placeholder="например: Иванов" plain :disabled="busy" />
      <SelectField v-model="personId" label="Сотрудник" :options="options" :disabled="busy" />
      <div class="add-lunch__times">
        <TextField v-model="startedAt" label="Ушёл" type="time" plain :disabled="busy" />
        <TextField v-model="endedAt" label="Вернулся" type="time" plain :disabled="busy" />
      </div>
      <TextAreaField
        v-model="reason"
        label="Причина"
        placeholder="например: забыл нажать «Ушёл на обед», обедал с 12:00 до 12:45"
        :rows="3"
        :code="false"
        :disabled="busy"
      />
      <div class="add-lunch__actions">
        <AppButton type="submit" variant="primary" :disabled="busy || !ready">Добавить</AppButton>
        <AppButton :disabled="busy" @click="emit('close')">Отмена</AppButton>
      </div>
    </form>
  </AppModal>
</template>

<style scoped>
.add-lunch {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.add-lunch__note {
  margin: 0;
  color: var(--muted);
}

.add-lunch__times {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.add-lunch__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
