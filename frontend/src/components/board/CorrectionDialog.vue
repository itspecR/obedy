<script setup lang="ts">
import { computed, ref } from "vue";
import { correctLunch, type BoardEntry } from "../../api/board";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import { formatDay, formatTime } from "../../format/dateTime";
import { LUNCH_STATUS } from "../lunch/lunchStatus";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import TextAreaField from "../ui/TextAreaField.vue";
import TextField from "../ui/TextField.vue";

const props = defineProps<{ entry: BoardEntry }>();
const emit = defineEmits<{ close: []; saved: [entry: BoardEntry] }>();

const lunch = props.entry.lunch;
const startedAt = ref(formatTime(lunch.started_at));
const endedAt = ref(lunch.ended_at && !lunch.auto_closed ? formatTime(lunch.ended_at) : "");
const reason = ref("");
const busy = ref(false);
const { notify, fail } = useToasts();

const ready = computed(() => Boolean(startedAt.value && endedAt.value && reason.value.trim()));
const status = computed(() => LUNCH_STATUS[lunch.status]);

async function save(): Promise<void> {
  busy.value = true;
  try {
    const entry = await correctLunch(lunch.id, { started_at: startedAt.value, ended_at: endedAt.value, reason: reason.value });
    notify("Время обеда исправлено");
    emit("saved", entry);
  } catch (error) {
    fail(errorMessage(error, "Не удалось исправить время. Попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <AppModal :title="entry.person.name" eyebrow="Исправить время обеда" @close="emit('close')">
    <form class="correction" novalidate @submit.prevent="save">
      <div class="correction__now">
        <span>{{ formatDay(lunch.day) }}</span>
        <StatusBadge :tone="status.tone" :label="status.label" />
      </div>
      <div class="correction__times">
        <TextField v-model="startedAt" label="Ушёл" type="time" plain :disabled="busy" />
        <TextField v-model="endedAt" label="Вернулся" type="time" plain :disabled="busy" />
      </div>
      <TextAreaField
        v-model="reason"
        label="Причина"
        placeholder="например: забыл нажать «Вернулся», вернулся в 12:50"
        hint="Сотрудник увидит, кто исправил время и почему"
        :rows="3"
        :code="false"
        :disabled="busy"
      />
      <div class="correction__actions">
        <AppButton type="submit" variant="primary" :disabled="busy || !ready">Сохранить</AppButton>
        <AppButton :disabled="busy" @click="emit('close')">Отмена</AppButton>
      </div>
    </form>
  </AppModal>
</template>

<style scoped>
.correction {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.correction__now {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
}

.correction__times {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.correction__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
