<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { addAbsence, changeAbsence, type Absence, type AbsenceForm } from "../../api/absences";
import { fetchBoardPeople, type Person } from "../../api/board";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import AppButton from "../ui/AppButton.vue";
import AppModal from "../ui/AppModal.vue";
import ChoiceField from "../ui/ChoiceField.vue";
import DateField from "../ui/DateField.vue";
import PersonPicker from "../ui/PersonPicker.vue";
import TextField from "../ui/TextField.vue";
import { KIND_OPTIONS, NOTE_LIMIT, blankForm, formOf, formProblem } from "./absences";

const props = withDefaults(defineProps<{ absence?: Absence | null; day: string; personId?: number | null }>(), { absence: null, personId: null });
const emit = defineEmits<{ close: []; saved: [absence: Absence] }>();

const people = ref<Person[]>([]);
const person = ref<number | null>(props.absence?.person_id ?? props.personId);
const form = ref<AbsenceForm>(props.absence ? formOf(props.absence) : blankForm(props.day));
const problem = ref("");
const busy = ref(false);
const { notify, fail } = useToasts();

const editing = computed(() => props.absence !== null);
const noteTooLong = computed(() => form.value.note.length > NOTE_LIMIT);
const ready = computed(() => (editing.value || person.value !== null) && !noteTooLong.value);

async function loadPeople(): Promise<void> {
  if (editing.value) {
    return;
  }
  try {
    people.value = await fetchBoardPeople();
  } catch (error) {
    fail(errorMessage(error, "Не удалось загрузить список сотрудников"));
  }
}

function send(): Promise<Absence> {
  return props.absence ? changeAbsence(props.absence.id, form.value) : addAbsence({ ...form.value, account_id: person.value as number });
}

async function save(): Promise<void> {
  problem.value = formProblem(form.value);
  if (problem.value) {
    return;
  }
  busy.value = true;
  try {
    const saved = await send();
    notify(editing.value ? "Отсутствие изменено" : "Отсутствие отмечено");
    emit("saved", saved);
  } catch (error) {
    fail(errorMessage(error, "Не удалось сохранить. Попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}

onMounted(loadPeople);
</script>

<template>
  <AppModal
    :title="editing ? 'Изменить отсутствие' : 'Отметить отсутствие'"
    :eyebrow="absence?.name"
    info="В эти дни сотрудник не попадёт в «Без обеда»: на табло и в статистике будет виден вид отсутствия."
    @close="emit('close')"
  >
    <form class="absence-form" novalidate @submit.prevent="save">
      <PersonPicker v-if="!editing" v-model="person" label="Сотрудник" :people="people" :disabled="busy" />
      <div class="absence-form__dates">
        <DateField v-model="form.first" label="С" :disabled="busy" />
        <DateField v-model="form.last" label="По" :disabled="busy" />
      </div>
      <p v-if="problem" class="absence-form__problem" role="alert">{{ problem }}</p>
      <ChoiceField v-model="form.kind" label="Вид" :options="KIND_OPTIONS" :disabled="busy" />
      <TextField
        v-model="form.note"
        label="Комментарий"
        placeholder="необязательно, например: приказ № 45"
        :error="noteTooLong ? `Не больше ${NOTE_LIMIT} символов` : ''"
        :disabled="busy"
      />
      <div class="absence-form__actions">
        <AppButton type="submit" variant="primary" :disabled="busy || !ready">{{ editing ? "Сохранить" : "Отметить" }}</AppButton>
        <AppButton :disabled="busy" @click="emit('close')">Отмена</AppButton>
      </div>
    </form>
  </AppModal>
</template>

<style scoped>
.absence-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.absence-form__dates {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.absence-form__problem {
  margin: -6px 0 0;
  color: var(--red);
  font-size: var(--text-small);
}

.absence-form__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
