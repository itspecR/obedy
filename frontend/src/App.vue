<script setup lang="ts">
import BackdropClock from "./components/ui/BackdropClock.vue";
import ConfirmDialog from "./components/ui/ConfirmDialog.vue";
import ToastHost from "./components/ui/ToastHost.vue";
</script>

<template>
  <BackdropClock />
  <RouterView />
  <ConfirmDialog />
  <ToastHost />
</template>
