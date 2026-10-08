<script setup lang="ts">
import { ref } from "vue";
import { errorMessage } from "../../api/http";
import { createLocalAccount, type Issued, type LocalAccountForm, type StaffMember } from "../../api/staff";
import { ROLE_CHOICES } from "../../roles";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import ChoiceField from "../ui/ChoiceField.vue";
import TextField from "../ui/TextField.vue";
import ProfileFields from "./ProfileFields.vue";
import TemporaryPassword from "./TemporaryPassword.vue";

const emit = defineEmits<{ close: []; created: [member: StaffMember] }>();

const form = ref<LocalAccountForm>({ login: "", full_name: "", role: "employee" });
const issued = ref<Issued | null>(null);
const error = ref("");
const busy = ref(false);

async function submit(): Promise<void> {
  error.value = "";
  busy.value = true;
  try {
    issued.value = await createLocalAccount(form.value);
    emit("created", issued.value.member);
  } catch (failure) {
    error.value = errorMessage(failure, "Не удалось создать учётную запись. Попробуйте ещё раз");
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <AppModal :title="issued ? 'Учётная запись создана' : 'Новый сотрудник'" eyebrow="Локальная учётная запись" @close="emit('close')">
    <div v-if="issued" class="create">
      <TemporaryPassword :login="issued.member.login" :password="issued.temporary_password" />
      <div class="create__actions">
        <AppButton variant="primary" @click="emit('close')">Готово</AppButton>
      </div>
    </div>
    <form v-else class="create" novalidate @submit.prevent="submit">
      <p class="create__note">Для тех, кого нет в Active Directory. Сотрудники домена появляются на сайте сами.</p>
      <TextField v-model="form.login" label="Логин" placeholder="например: kassa1" hint="Латинские буквы, цифры, точка, дефис или подчёркивание" plain :disabled="busy" />
      <ProfileFields v-model="form" :disabled="busy" />
      <ChoiceField v-model="form.role" label="Роль" :options="ROLE_CHOICES" :disabled="busy" />
      <p v-if="error" class="create__error" role="alert">{{ error }}</p>
      <div class="create__actions">
        <AppButton type="submit" variant="primary" :disabled="busy">Создать</AppButton>
        <AppButton :disabled="busy" @click="emit('close')">Отмена</AppButton>
      </div>
    </form>
  </AppModal>
</template>

<style scoped>
.create {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.create__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.create__error {
  margin: 0;
  color: var(--red);
}

.create__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
