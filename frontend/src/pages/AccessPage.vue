<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { addNetwork, fetchAccess, removeNetwork, setPrivateNetworks, type AccessState, type AllowedNetwork } from "../api/access";
import { errorMessage } from "../api/http";
import AddNetworkForm from "../components/access/AddNetworkForm.vue";
import NetworkList from "../components/access/NetworkList.vue";
import AppButton from "../components/ui/AppButton.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import SwitchField from "../components/ui/SwitchField.vue";
import { useConfirm } from "../composables/useConfirm";
import { useToasts } from "../composables/useToasts";

const LOAD_FAILED = "Не удалось загрузить настройки доступа";
const SAVE_FAILED = "Не удалось сохранить. Попробуйте ещё раз";

const state = ref<AccessState | null>(null);
const loadError = ref("");
const busy = ref(false);
const { ask } = useConfirm();
const { notify, fail } = useToasts();

const lanHint = computed(() => (state.value ? `Любой внутренний адрес: ${state.value.private_ranges.join(", ")}` : ""));

async function load(): Promise<void> {
  loadError.value = "";
  try {
    state.value = await fetchAccess();
  } catch (error) {
    loadError.value = errorMessage(error, LOAD_FAILED);
  }
}

async function save(action: () => Promise<AccessState>, success: string): Promise<boolean> {
  busy.value = true;
  try {
    state.value = await action();
    notify(success);
    return true;
  } catch (error) {
    fail(errorMessage(error, SAVE_FAILED));
    return false;
  } finally {
    busy.value = false;
  }
}

async function toggleLan(enabled: boolean): Promise<void> {
  if (!enabled) {
    const accepted = await ask({
      title: "Закрыть всю локальную сеть?",
      text: "Сайт будет открываться только с адресов из списка. Остальные компьютеры увидят страницу «Доступ закрыт».",
      action: "Закрыть",
      danger: true,
    });
    if (!accepted) {
      return;
    }
  }
  await save(() => setPrivateNetworks(enabled), enabled ? "Вся локальная сеть открыта" : "Локальная сеть закрыта, доступ только по списку");
}

function add(network: string, note: string): Promise<boolean> {
  return save(() => addNetwork(network, note), "Адрес добавлен");
}

async function remove(item: AllowedNetwork): Promise<void> {
  const accepted = await ask({
    title: `Убрать ${item.network}?`,
    text: "С этого адреса сайт перестанет открываться, если он не входит в открытую локальную сеть.",
    action: "Убрать",
    danger: true,
  });
  if (accepted) {
    await save(() => removeNetwork(item.id), "Адрес убран");
  }
}

onMounted(load);
</script>

<template>
  <section class="access">
    <PageHeader title="Доступ" subtitle="С каких компьютеров открывается сайт" />
    <div v-if="loadError" class="panel access__card access__error" role="alert">
      <p>{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <template v-else-if="state">
      <div class="panel access__card">
        <SwitchField label="Вся локальная сеть" :hint="lanHint" :checked="state.allow_private" :disabled="busy" @change="toggleLan" />
        <p class="access__note">
          Ваш адрес: <span class="code">{{ state.your_address }}</span>. Сам сервер открыт всегда. Изменения вступают в силу в течение 5 секунд.
        </p>
      </div>
      <div class="panel access__card">
        <h2 class="access__title">Разрешённые адреса</h2>
        <AddNetworkForm :busy="busy" :submit="add" />
        <NetworkList :networks="state.networks" :busy="busy" @remove="remove" />
      </div>
    </template>
    <div v-else class="panel access__card access__loading" aria-busy="true">Загружаем…</div>
  </section>
</template>

<style scoped>
.access {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 880px;
}

.access__card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 24px;
}

.access__title {
  font-size: var(--text-h3);
}

.access__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.access__error {
  align-items: flex-start;
}

.access__error p {
  margin: 0;
  color: var(--red);
}

.access__loading {
  color: var(--muted);
}

@media (max-width: 650px) {
  .access__card {
    padding: 18px 16px;
  }
}
</style>
