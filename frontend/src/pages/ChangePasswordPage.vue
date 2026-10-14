<script setup lang="ts">
import { useRouter } from "vue-router";
import AppButton from "../components/ui/AppButton.vue";
import AuthLayout from "../components/login/AuthLayout.vue";
import ChangePasswordForm from "../components/login/ChangePasswordForm.vue";
import { useToasts } from "../composables/useToasts";
import { useSession } from "../stores/session";

const router = useRouter();
const session = useSession();
const { notify } = useToasts();

async function done(): Promise<void> {
  notify("Пароль изменён");
  await router.replace({ name: "home" });
}

async function leave(): Promise<void> {
  await session.signOut();
  await router.replace("/login");
}
</script>

<template>
  <AuthLayout title="Придумайте свой пароль">
    <p class="lead">
      {{
        session.me?.weak_password
          ? "Ваш пароль слишком простой и больше не подходит по правилам безопасности. Придумайте новый, чтобы продолжить."
          : "Сейчас у вас временный пароль. Прежде чем продолжить, задайте свой."
      }}
    </p>
    <ChangePasswordForm :ask-current="session.me?.weak_password === true" @changed="done" />
    <AppButton variant="ghost" class="leave" @click="leave">Выйти</AppButton>
  </AuthLayout>
</template>

<style scoped>
.lead {
  margin: -10px 0 20px;
  color: var(--muted);
}

.leave {
  margin-top: 16px;
  padding-left: 0;
}
</style>
