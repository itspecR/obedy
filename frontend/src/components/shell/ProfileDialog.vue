<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Me } from "../../api/auth";
import { useToasts } from "../../composables/useToasts";
import { initials } from "../../navigation";
import { ROLE_LABELS } from "../../roles";
import ChangePasswordForm from "../login/ChangePasswordForm.vue";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import LightModeChoice from "./LightModeChoice.vue";

const props = defineProps<{ me: Me }>();
const emit = defineEmits<{ close: [] }>();
const { notify } = useToasts();
type Mode = "view" | "password";

const TITLES: Record<Mode, string> = { view: "Профиль", password: "Смена пароля" };
const mode = ref<Mode>("view");
const modal = ref<InstanceType<typeof AppModal> | null>(null);
const isLocal = computed(() => props.me.source === "local");

watch(mode, () => modal.value?.focusFirst());

function passwordChanged(): void {
  notify("Пароль изменён");
  emit("close");
}
</script>

<template>
  <AppModal ref="modal" :title="TITLES[mode]" @close="emit('close')">
    <ChangePasswordForm v-if="mode === 'password'" cancellable ask-current @changed="passwordChanged" @cancel="mode = 'view'" />
    <div v-else class="profile">
      <div class="profile__head">
        <span class="profile__avatar" aria-hidden="true">{{ initials(me.display_name) }}</span>
        <div>
          <p class="profile__name">{{ me.display_name }}</p>
          <p class="profile__role">{{ ROLE_LABELS[me.role] }}</p>
        </div>
      </div>
      <div class="profile__login">
        <span class="profile__label">Логин</span>
        <span class="code profile__value">{{ me.login }}</span>
      </div>
      <LightModeChoice />
      <AppButton v-if="isLocal" variant="primary" block @click="mode = 'password'">Сменить пароль</AppButton>
      <p v-else class="profile__note">Вы входите под учётной записью Windows. Пароль меняется в Windows.</p>
    </div>
  </AppModal>
</template>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.profile__head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.profile__avatar {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  flex: none;
  border-radius: 50%;
  background: var(--blue-tint);
  color: var(--brand);
  font-weight: 700;
}

.profile__name {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.profile__role {
  margin: 2px 0 0;
  color: var(--muted);
}

.profile__login {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px 10px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-panel);
  background: var(--field);
}

.profile__label {
  color: var(--muted);
}

.profile__value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile__note {
  margin: 0;
  color: var(--muted);
}
</style>
