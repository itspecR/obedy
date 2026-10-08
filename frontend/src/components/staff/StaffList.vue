<script setup lang="ts">
import type { StaffMember } from "../../api/staff";
import { ROLE_LABELS } from "../../roles";
import StatusBadge from "../ui/StatusBadge.vue";
import { STATUS_LABELS, STATUS_TONES, displayName } from "./filters";

defineProps<{ members: StaffMember[]; total: number }>();

const SOURCE_LABELS = { domain: "Домен", local: "Локальная" } as const;

function details(member: StaffMember): string {
  return [member.department, member.position].filter(Boolean).join(" · ") || "Отдел и должность не указаны";
}
</script>

<template>
  <div class="panel staff">
    <div v-if="members.length" class="staff__head" aria-hidden="true">
      <span>Сотрудник</span>
      <span>Отдел и должность</span>
      <span>Роль</span>
      <span>Обеды</span>
      <span>Статус</span>
    </div>
    <ul v-if="members.length" class="staff__list">
      <li v-for="member in members" :key="member.id" class="staff__row">
        <div class="staff__who">
          <span class="staff__name">{{ displayName(member) }}</span>
          <span class="staff__login"><span class="code">{{ member.login }}</span> · {{ SOURCE_LABELS[member.source] }}</span>
        </div>
        <span class="staff__details">{{ details(member) }}</span>
        <span class="staff__role">{{ ROLE_LABELS[member.role] }}</span>
        <span class="staff__lunch">{{ member.track_lunch ? "Учитываются" : "Не учитываются" }}</span>
        <StatusBadge class="staff__status" :tone="STATUS_TONES[member.status]" :label="STATUS_LABELS[member.status]" />
      </li>
    </ul>
    <div v-else class="staff__empty">
      <template v-if="total">
        <p class="staff__empty-title">Никого не нашли</p>
        <p class="staff__empty-text">Измените поиск или фильтры.</p>
      </template>
      <template v-else>
        <p class="staff__empty-title">Сотрудников пока нет</p>
        <p class="staff__empty-text">Они появятся после синхронизации с доменом или первого входа.</p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.staff {
  --status-column: 136px;
  padding: 8px 20px;
}

.staff__head span:last-child,
.staff__status {
  justify-self: end;
}

.staff__head,
.staff__row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1.4fr) minmax(0, 0.8fr) minmax(0, 0.8fr) var(--status-column);
  align-items: center;
  gap: 16px;
}

.staff__head {
  padding: 10px 4px;
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
}

.staff__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.staff__row {
  padding: 12px 4px;
  border-top: 1px solid var(--line);
}

.staff__who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.staff__name,
.staff__details {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.staff__name {
  font-weight: 600;
}

.staff__login,
.staff__details,
.staff__lunch {
  font-size: var(--text-small);
  color: var(--muted);
}

.staff__empty {
  padding: 28px 4px;
  text-align: center;
}

.staff__empty-title {
  margin: 0 0 4px;
  font-weight: 600;
}

.staff__empty-text {
  margin: 0;
  color: var(--muted);
}

@media (max-width: 900px) {
  .staff__head {
    display: none;
  }

  .staff__row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 4px 12px;
  }

  .staff__who {
    grid-column: 1;
  }

  .staff__status {
    grid-column: 2;
    grid-row: 1;
  }

  .staff__details,
  .staff__role,
  .staff__lunch {
    grid-column: 1 / -1;
  }

  .staff__role,
  .staff__lunch {
    font-size: var(--text-small);
  }
}

@media (max-width: 650px) {
  .staff {
    padding: 4px 16px;
  }
}
</style>
