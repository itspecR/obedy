<script setup lang="ts">
import type { ConnectionForm } from "../../api/setup";
import SwitchField from "../ui/SwitchField.vue";
import TextField from "../ui/TextField.vue";

const HOST_HINT = "IP или имя сервера SQL. Для именованного экземпляра: 192.168.1.10\\SQLEXPRESS.";
const PORT_HINT = "Пусто — порт по умолчанию или через SQL Server Browser для именованного экземпляра.";
const TRUST_HINT = "Включите, если у SQL Server свой (самоподписанный) сертификат — так обычно у SQL Server Express.";

defineProps<{ disabled?: boolean }>();
const form = defineModel<ConnectionForm>({ required: true });
</script>

<template>
  <div class="connection__row">
    <TextField v-model="form.host" label="Адрес SQL Server" :hint="HOST_HINT" placeholder="192.168.1.10\SQLEXPRESS" plain :disabled="disabled" />
    <TextField v-model="form.port" label="Порт" :hint="PORT_HINT" placeholder="1433" plain :disabled="disabled" />
  </div>
  <TextField v-model="form.name" label="База данных" plain :disabled="disabled" />
  <div class="connection__row connection__row--even">
    <TextField v-model="form.user" label="Логин SQL Server" autocomplete="off" plain :disabled="disabled" />
    <TextField v-model="form.password" label="Пароль" type="password" autocomplete="new-password" :disabled="disabled" />
  </div>
  <SwitchField label="Доверять сертификату сервера" :hint="TRUST_HINT" :checked="form.trust_certificate" :disabled="disabled" @change="form.trust_certificate = $event" />
</template>

<style scoped>
.connection__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 120px);
  gap: 12px;
}

.connection__row--even {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 650px) {
  .connection__row,
  .connection__row--even {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
