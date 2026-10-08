<script setup lang="ts">
import { useRouter } from "vue-router";
import AuthLayout from "../components/login/AuthLayout.vue";
import LoginForm from "../components/login/LoginForm.vue";

const router = useRouter();
</script>

<template>
  <AuthLayout title="Вход">
    <LoginForm @success="router.replace({ name: 'home' })" />
  </AuthLayout>
</template>
