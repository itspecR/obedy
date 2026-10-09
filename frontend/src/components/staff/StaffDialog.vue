<script setup lang="ts">
import { computed, ref } from "vue";
import type { Role } from "../../api/auth";
import { errorMessage } from "../../api/http";
import { changeRole, resetPassword, setBlocked, setTrackLunch, updateProfile, type Issued, type Profile, type StaffMember } from "../../api/staff";
import { useConfirm } from "../../composables/useConfirm";
import { useToasts } from "../../composables/useToasts";
import { ROLE_CHOICES, ROLE_LABELS } from "../../roles";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import ChoiceField from "../ui/ChoiceField.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import SwitchField from "../ui/SwitchField.vue";
import { STATUS_LABELS, STATUS_TONES, displayName } from "./filters";
import ProfileFields from "./ProfileFields.vue";
import TemporaryPassword from "./TemporaryPassword.vue";

const props = defineProps<{ member: StaffMember; isSelf: boolean }>();
const emit = defineEmits<{ close: []; updated: [member: StaffMember] }>();

const SAVE_FAILED = "Не удалось сохранить. Попробуйте ещё раз";

const busy = ref(false);
const { ask } = useConfirm();
const { notify, fail } = useToasts();

const profileOf = (member: StaffMember): Profile => ({ full_name: member.full_name });

const draft = ref<Profile>(profileOf(props.member));
const issued = ref<Issued | null>(null);

const isLocal = computed(() => props.member.source === "local");
const profileChanged = computed(() => JSON.stringify(draft.value) !== JSON.stringify(profileOf(props.member)));
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

function saveProfile(): Promise<void> {
  return run(() => updateProfile(props.member.id, draft.value), "Данные сохранены");
}

async function issuePassword(): Promise<void> {
  const accepted = await ask({
    title: `Сбросить пароль: ${displayName(props.member)}?`,
    text: "Старый пароль перестанет работать, сотрудник выйдет со всех устройств. Новый временный пароль будет показан один раз.",
    action: "Сбросить",
    danger: true,
  });
  if (!accepted) {
    return;
  }
  await run(async () => {
    issued.value = await resetPassword(props.member.id);
    return issued.value.member;
  }, "Временный пароль выдан");
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
      </div>

      <form v-if="isLocal" class="manage__profile" novalidate @submit.prevent="saveProfile">
        <ProfileFields v-model="draft" :disabled="busy" />
        <div>
          <AppButton type="submit" size="small" :disabled="busy || !profileChanged">Сохранить данные</AppButton>
        </div>
      </form>
      <p v-else class="manage__note">ФИО берётся из Active Directory.</p>

      <ChoiceField v-model="role" label="Роль" :options="ROLE_CHOICES" :disabled="busy || isSelf" />
      <p v-if="isSelf" class="manage__note">Свою роль изменить нельзя — попросите другого администратора.</p>

      <SwitchField
        v-if="member.can_track_lunch"
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
        <AppButton v-if="isLocal && !isSelf" :disabled="busy" @click="issuePassword">Сбросить пароль</AppButton>
        <span v-if="isSelf" class="manage__note">Себя заблокировать нельзя. Свой пароль меняйте в профиле.</span>
      </div>
      <TemporaryPassword v-if="issued" :login="issued.member.login" :password="issued.temporary_password" />
    </div>
  </AppModal>
</template>

<style scoped>
.manage {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.manage__profile {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
