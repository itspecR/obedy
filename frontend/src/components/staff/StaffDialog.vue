<script setup lang="ts">
import { computed, ref } from "vue";
import type { Role } from "../../api/auth";
import { errorMessage } from "../../api/http";
import { changeRole, setBlocked, setTrackLunch, type StaffMember } from "../../api/staff";
import { useConfirm } from "../../composables/useConfirm";
import { useToasts } from "../../composables/useToasts";
import { ROLE_LABELS } from "../../roles";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import ChoiceField from "../ui/ChoiceField.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import SwitchField from "../ui/SwitchField.vue";
import { STATUS_LABELS, STATUS_TONES, displayName } from "./filters";

const props = defineProps<{ member: StaffMember; isSelf: boolean }>();
const emit = defineEmits<{ close: []; updated: [member: StaffMember] }>();

const ROLE_CHOICES = (Object.entries(ROLE_LABELS) as [Role, string][]).map(([value, label]) => ({ value, label }));
const SAVE_FAILED = "Не удалось сохранить. Попробуйте ещё раз";

const busy = ref(false);
const { ask } = useConfirm();
const { notify, fail } = useToasts();

const blocked = computed(() => props.member.status === "blocked");
const role = computed<Role>({
  get: () => props.member.role,
  set: (next) => void run(() => changeRole(props.member.id, next), `Новая роль: ${ROLE_LABELS[next]}`),
});

async function run(action: () => Promise<StaffMember>, success: string): Promise<void> {
  busy.value = true;
  try {
    emit("updated", await action());
    notify(success);
  } catch (error) {
    fail(errorMessage(error, SAVE_FAILED));
  } finally {
    busy.value = false;
  }
}

function toggleLunch(track: boolean): Promise<void> {
  return run(() => setTrackLunch(props.member.id, track), track ? "Обеды учитываются" : "Обеды не учитываются");
}

async function toggleBlock(): Promise<void> {
  if (!blocked.value) {
    const accepted = await ask({
      title: `Заблокировать: ${displayName(props.member)}?`,
      text: "Сотрудник сразу выйдет со всех устройств и не сможет войти, пока его не разблокируют. История обедов сохранится.",
      action: "Заблокировать",
      danger: true,
    });
    if (!accepted) {
      return;
    }
  }
  await run(() => setBlocked(props.member.id, !blocked.value), blocked.value ? "Сотрудник разблокирован" : "Сотрудник заблокирован");
}
</script>

<template>
  <AppModal :title="displayName(member)" :eyebrow="member.login" @close="emit('close')">
    <div class="manage">
      <div class="manage__summary">
        <StatusBadge :tone="STATUS_TONES[member.status]" :label="STATUS_LABELS[member.status]" />
        <span class="manage__details">{{ [member.department, member.position].filter(Boolean).join(" · ") || "Отдел и должность не указаны" }}</span>
      </div>
      <p v-if="member.status === 'gone'" class="manage__note">
        Сотрудника нет в группе доступа в домене или он отключён в AD — войти он не сможет, пока его не вернут.
      </p>

      <ChoiceField v-model="role" label="Роль" :options="ROLE_CHOICES" :disabled="busy || isSelf" />
      <p v-if="isSelf" class="manage__note">Свою роль изменить нельзя — попросите другого администратора.</p>

      <SwitchField
        label="Учитывать обеды"
        hint="Сотрудник отмечает уход на обед и возвращение, его видно на табло HR"
        :checked="member.track_lunch"
        :disabled="busy"
        @change="toggleLunch"
      />

      <div class="manage__block">
        <AppButton :variant="blocked ? 'secondary' : 'danger'" :disabled="busy || isSelf" @click="toggleBlock">
          {{ blocked ? "Разблокировать" : "Заблокировать" }}
        </AppButton>
        <span v-if="isSelf" class="manage__note">Себя заблокировать нельзя.</span>
      </div>
    </div>
  </AppModal>
</template>

<style scoped>
.manage {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.manage__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.manage__details,
.manage__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.manage__block {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}
</style>
