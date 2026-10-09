<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { addLunch, fetchBoardPeople, type BoardEntry, type Person } from "../../api/board";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import { formatDay } from "../../format/dateTime";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import PersonPicker from "../ui/PersonPicker.vue";
import TextAreaField from "../ui/TextAreaField.vue";
import TimeField from "../ui/TimeField.vue";

const props = defineProps<{ day: string }>();
const emit = defineEmits<{ close: []; saved: [entry: BoardEntry] }>();

const people = ref<Person[]>([]);
const personId = ref<number | null>(null);
const startedAt = ref("");
const endedAt = ref("");
const reason = ref("");
const busy = ref(false);
const { notify, fail } = useToasts();

const ready = computed(() => Boolean(personId.value !== null && startedAt.value && endedAt.value && reason.value.trim()));

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
      account_id: personId.value as number,
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
  <AppModal title="Добавить обед" :eyebrow="formatDay(day)" info="Для сотрудника, который забыл нажать «Ушёл на обед». Он увидит, кто и почему добавил обед." @close="emit('close')">
    <form class="add-lunch" novalidate @submit.prevent="save">
      <PersonPicker v-model="personId" label="Сотрудник" :people="people" :disabled="busy" />
      <div class="add-lunch__times">
        <TimeField v-model="startedAt" label="Ушёл" :disabled="busy" />
        <TimeField v-model="endedAt" label="Вернулся" :disabled="busy" />
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
