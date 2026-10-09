<script setup lang="ts">
import { computed, ref } from "vue";
import { deleteLunch, type BoardEntry } from "../../api/board";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import { formatDay } from "../../format/dateTime";
import { LUNCH_STATUS, lunchRange } from "../lunch/lunchStatus";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import TextAreaField from "../ui/TextAreaField.vue";

const props = defineProps<{ entry: BoardEntry }>();
const emit = defineEmits<{ close: []; deleted: [lunchId: number] }>();

const lunch = props.entry.lunch;
const reason = ref("");
const busy = ref(false);
const { notify, fail } = useToasts();

const ready = computed(() => Boolean(reason.value.trim()));
const status = computed(() => LUNCH_STATUS[lunch.status]);

async function remove(): Promise<void> {
  busy.value = true;
  try {
    await deleteLunch(lunch.id, reason.value);
    notify("Обед удалён");
    emit("deleted", lunch.id);
  } catch (error) {
    fail(errorMessage(error, "Не удалось удалить обед. Попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <AppModal :title="entry.person.name" eyebrow="Удалить обед" info="Удаление нельзя отменить. В журнале останется запись: кто удалил, чей обед, время и причина." @close="emit('close')">
    <form class="delete-lunch" novalidate @submit.prevent="remove">
      <div class="delete-lunch__now">
        <span>{{ formatDay(lunch.day) }} · <span class="numeric">{{ lunchRange(lunch) }}</span></span>
        <StatusBadge :tone="status.tone" :label="status.label" />
      </div>
      <TextAreaField v-model="reason" label="Причина" placeholder="например: добавлен по ошибке" :rows="3" :code="false" :disabled="busy" />
      <div class="delete-lunch__actions">
        <AppButton type="submit" variant="danger" :disabled="busy || !ready">Удалить</AppButton>
        <AppButton :disabled="busy" @click="emit('close')">Отмена</AppButton>
      </div>
    </form>
  </AppModal>
</template>

<style scoped>
.delete-lunch {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.delete-lunch__now {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
}

.delete-lunch__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
