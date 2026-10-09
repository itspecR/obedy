<script setup lang="ts">
import type { SystemInfo } from "../../api/journal";
import BlockTitle from "../ui/BlockTitle.vue";
import { NO_DATA, appMemoryText, freeText, memoryText, momentText, osText } from "./systemText";

defineProps<{ info: SystemInfo }>();
</script>

<template>
  <section class="panel system" aria-labelledby="system-title">
    <BlockTitle title="Сервер" title-id="system-title" info="Релиз — ветка, коммит и время развёртывания. Резервная копия — время последней успешной копии базы." />
    <dl class="system__rows">
      <dt>Релиз</dt>
      <dd class="system__release">{{ info.release || NO_DATA }}</dd>
      <dt>Сайт запущен</dt>
      <dd>{{ momentText(info.site_started_at) }}</dd>
      <dt>База данных запущена</dt>
      <dd>{{ momentText(info.db_started_at) }}</dd>
      <dt>Резервная копия базы</dt>
      <dd>{{ momentText(info.last_backup_at) }}</dd>
      <dt>Система</dt>
      <dd>{{ osText(info) }}</dd>
      <dt>Память сервера</dt>
      <dd>{{ memoryText(info.memory_used, info.memory_total) }}</dd>
      <dt>Свободно</dt>
      <dd>{{ freeText(info) }}</dd>
      <dt>Память приложения</dt>
      <dd>{{ appMemoryText(info) }}</dd>
    </dl>
  </section>
</template>

<style scoped>
.system {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px;
}

.system__rows {
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  gap: 8px 14px;
  margin: 0;
  font-size: var(--text-small);
}

.system__rows dt {
  color: var(--muted);
}

.system__rows dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
  overflow-wrap: anywhere;
}

.system__release {
  font-family: var(--font-mono);
}
</style>
