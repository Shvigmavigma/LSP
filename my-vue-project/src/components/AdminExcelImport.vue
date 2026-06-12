<template>
  <section class="excel-import">
    <div class="import-heading">
      <div>
        <h2>{{ $t('excelImport.title') }}</h2>
        <p>{{ $t('excelImport.description') }}</p>
      </div>
      <div class="heading-actions">
        <button class="template-button" type="button" @click="downloadTemplate" :disabled="busy">
          {{ $t('excelImport.downloadTemplate') }}
        </button>
        <button class="template-button" type="button" @click="showTemplateControls = !showTemplateControls">
          {{ $t('excelImport.manageTemplate') }}
        </button>
      </div>
    </div>

    <div v-if="modes.length > 1" class="mode-tabs">
      <button
        v-for="mode in modes"
        :key="mode"
        type="button"
        :class="{ active: selectedMode === mode }"
        @click="selectedMode = mode"
      >
        {{ $t(`excelImport.modes.${mode}`) }}
      </button>
    </div>

    <div class="required-columns">
      <strong>{{ $t('excelImport.requiredColumns') }}</strong>
      <code v-for="column in requiredColumns[selectedMode]" :key="column">{{ column }}</code>
    </div>

    <div v-if="showTemplateControls" class="template-controls">
      <div class="builder-heading">
        <strong>{{ $t('excelImport.builderTitle') }}</strong>
        <span>{{ $t('excelImport.builderHint') }}</span>
      </div>
      <div class="builder-grid">
        <div v-for="(column, index) in builderColumns" :key="`${column}-${index}`" class="builder-column">
          <div class="column-heading">
            <strong v-if="isRequired(column)">{{ column }}</strong>
            <input
              v-else
              :value="column"
              type="text"
              :placeholder="$t('excelImport.columnName')"
              @change="renameColumnFromEvent(index, $event)"
            />
            <button
              v-if="!isRequired(column)"
              type="button"
              class="remove-column"
              :title="$t('excelImport.removeColumn')"
              @click="removeColumn(index)"
            >✕</button>
          </div>
          <input v-model="builderValues[column]" type="text" :placeholder="$t('excelImport.examplePlaceholder')" />
        </div>
      </div>
      <div class="add-column">
        <input v-model="newColumnName" type="text" :placeholder="$t('excelImport.columnName')" @keyup.enter="addColumn" />
        <button class="template-button" type="button" :disabled="!newColumnName.trim()" @click="addColumn">
          {{ $t('excelImport.addColumn') }}
        </button>
      </div>
      <div class="builder-actions">
        <button class="import-button" type="button" @click="generateTemplate" :disabled="busy || !builderComplete">
          {{ $t('excelImport.generateTemplate') }}
        </button>
        <button class="reset-template-button" type="button" @click="resetTemplate" :disabled="busy">
          {{ $t('excelImport.resetTemplate') }}
        </button>
      </div>
    </div>

    <div
      class="drop-zone"
      :class="{ dragging, selected: !!file }"
      @dragenter.prevent="dragging = true"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="dropFile"
      @click="fileInput?.click()"
    >
      <input
        ref="fileInput"
        class="hidden-input"
        type="file"
        accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        @change="selectFile"
      />
      <template v-if="file">
        <strong>{{ file.name }}</strong>
        <span>{{ formatFileSize(file.size) }}</span>
        <button class="remove-file" type="button" @click.stop="removeFile">
          {{ $t('excelImport.removeFile') }}
        </button>
      </template>
      <template v-else>
        <strong>{{ $t('excelImport.dropTitle') }}</strong>
        <span>{{ $t('excelImport.dropHint') }}</span>
      </template>
    </div>

    <div class="upload-row">
      <button type="button" class="import-button" :disabled="!file || busy" @click="upload">
        {{ busy ? $t('excelImport.importing') : $t('excelImport.import') }}
      </button>
    </div>

    <p v-if="message" class="result" :class="{ error: isError }">{{ message }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/utils/api';

type ImportMode = 'student_emails' | 'teacher_emails' | 'students' | 'teachers' | 'projects';

const props = defineProps<{ modes: ImportMode[] }>();
const emit = defineEmits<{ imported: [] }>();
const { t } = useI18n();

const requiredColumns: Record<ImportMode, string[]> = {
  student_emails: ['email'],
  teacher_emails: ['email'],
  students: ['fullname', 'email', 'password', 'class'],
  teachers: ['fullname', 'email', 'password'],
  projects: ['title', 'body', 'customer_email'],
};
const modes = computed(() => props.modes);
const selectedMode = ref<ImportMode>(props.modes[0]);
const file = ref<File | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const busy = ref(false);
const message = ref('');
const isError = ref(false);
const dragging = ref(false);
const showTemplateControls = ref(false);
const builderValues = ref<Record<string, string>>({});
const builderColumns = ref<string[]>([]);
const newColumnName = ref('');

watch(
  () => props.modes,
  (value) => {
    if (!value.includes(selectedMode.value)) selectedMode.value = value[0];
    resetResult();
  },
);
watch(selectedMode, loadBuilder, { immediate: true });

function resetResult() {
  file.value = null;
  message.value = '';
  isError.value = false;
  if (fileInput.value) fileInput.value.value = '';
}

function selectFile(event: Event) {
  setFile((event.target as HTMLInputElement).files?.[0] || null);
}

function dropFile(event: DragEvent) {
  dragging.value = false;
  setFile(event.dataTransfer?.files?.[0] || null);
}

function setFile(selected: File | null) {
  if (selected && !selected.name.toLowerCase().endsWith('.xlsx')) {
    isError.value = true;
    message.value = t('excelImport.xlsxOnly');
    return;
  }
  file.value = selected;
  message.value = '';
  isError.value = false;
}

function removeFile() {
  file.value = null;
  if (fileInput.value) fileInput.value.value = '';
}

function formatFileSize(bytes: number) {
  return bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function resetBuilder() {
  builderColumns.value = [...requiredColumns[selectedMode.value]];
  builderValues.value = Object.fromEntries(builderColumns.value.map((column) => [column, '']));
}

const builderComplete = computed(() =>
  builderColumns.value.length > 0
  && new Set(builderColumns.value).size === builderColumns.value.length
  && builderColumns.value.every(
    (column) => column.trim() && String(builderValues.value[column] || '').trim(),
  ),
);

async function loadBuilder() {
  resetBuilder();
  try {
    const response = await api.get(`/admin/excel-import/template/${selectedMode.value}/config`);
    builderColumns.value = response.data.columns || [...requiredColumns[selectedMode.value]];
    builderValues.value = Object.fromEntries(
      builderColumns.value.map((column) => [
        column,
        String(response.data.example_values?.[column] ?? ''),
      ]),
    );
  } catch (error: any) {
    isError.value = true;
    message.value = error.response?.data?.detail || t('excelImport.templateConfigError');
  }
}

function isRequired(column: string) {
  return requiredColumns[selectedMode.value].includes(column);
}

function addColumn() {
  const column = newColumnName.value.trim();
  if (!column || builderColumns.value.includes(column)) {
    isError.value = true;
    message.value = t('excelImport.columnDuplicate');
    return;
  }
  builderColumns.value.push(column);
  builderValues.value[column] = '';
  newColumnName.value = '';
  message.value = '';
}

function removeColumn(index: number) {
  const column = builderColumns.value[index];
  if (isRequired(column)) return;
  builderColumns.value.splice(index, 1);
  delete builderValues.value[column];
}

function renameColumn(index: number, rawName: string) {
  const oldName = builderColumns.value[index];
  const newName = rawName.trim();
  if (!newName || (newName !== oldName && builderColumns.value.includes(newName))) {
    isError.value = true;
    message.value = t('excelImport.columnDuplicate');
    return;
  }
  builderColumns.value[index] = newName;
  builderValues.value[newName] = builderValues.value[oldName] || '';
  if (newName !== oldName) delete builderValues.value[oldName];
}

function renameColumnFromEvent(index: number, event: Event) {
  renameColumn(index, (event.target as HTMLInputElement).value);
}

async function downloadTemplate() {
  busy.value = true;
  try {
    const response = await api.get(`/admin/excel-import/template/${selectedMode.value}`, {
      responseType: 'blob',
    });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${selectedMode.value}_template.xlsx`;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error: any) {
    isError.value = true;
    message.value = error.response?.data?.detail || t('excelImport.templateError');
  } finally {
    busy.value = false;
  }
}

async function generateTemplate() {
  busy.value = true;
  try {
    await api.put(`/admin/excel-import/template/${selectedMode.value}/generate`, {
      example_values: builderValues.value,
      columns: builderColumns.value,
    });
    isError.value = false;
    message.value = t('excelImport.templateGenerated');
    await loadBuilder();
  } catch (error: any) {
    isError.value = true;
    message.value = error.response?.data?.detail || t('excelImport.templateGenerateError');
  } finally {
    busy.value = false;
  }
}

async function resetTemplate() {
  busy.value = true;
  try {
    await api.delete(`/admin/excel-import/template/${selectedMode.value}`);
    isError.value = false;
    message.value = t('excelImport.templateReset');
    await loadBuilder();
  } catch (error: any) {
    isError.value = true;
    message.value = error.response?.data?.detail || t('excelImport.templateResetError');
  } finally {
    busy.value = false;
  }
}

async function upload() {
  if (!file.value) return;
  busy.value = true;
  message.value = '';
  const form = new FormData();
  form.append('file', file.value);
  try {
    const response = await api.post(`/admin/excel-import/${selectedMode.value}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    isError.value = false;
    message.value = t('excelImport.success', {
      count: response.data.imported_count,
      skipped: response.data.skipped_count || 0,
    });
    emit('imported');
    file.value = null;
    if (fileInput.value) fileInput.value.value = '';
  } catch (error: any) {
    isError.value = true;
    message.value = error.response?.data?.detail || t('excelImport.importError');
  } finally {
    busy.value = false;
  }
}
</script>

<style scoped>
.excel-import {
  max-width: 1200px;
  margin: 0 auto 20px;
  padding: 18px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow);
}
.import-heading, .upload-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
}
.heading-actions, .builder-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.import-heading h2 { margin: 0 0 4px; color: var(--heading-color); font-size: 1.2rem; }
.import-heading p { margin: 0; color: var(--text-secondary); }
.mode-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; }
.mode-tabs button, .template-button, .import-button, .reset-template-button {
  border: 1px solid var(--accent-color);
  background: var(--bg-card);
  color: var(--accent-color);
  padding: 9px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.mode-tabs button.active, .import-button {
  background: var(--accent-color);
  color: var(--button-text);
}
.reset-template-button { border-color: var(--danger-color); color: var(--danger-color); }
.template-controls {
  margin: 14px 0;
  padding: 14px;
  border: 1px solid var(--border-color);
  background: var(--bg-column);
}
.builder-heading { display: flex; flex-direction: column; gap: 3px; margin-bottom: 12px; }
.builder-heading span { color: var(--text-secondary); font-size: .9rem; }
.builder-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }
.builder-column { display: flex; flex-direction: column; gap: 5px; color: var(--text-secondary); }
.builder-grid input, .add-column input, .column-heading input {
  width: 100%;
  padding: 9px;
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--input-border);
  border-radius: 4px;
}
.column-heading { display: flex; align-items: center; gap: 6px; min-height: 34px; }
.column-heading input { min-width: 0; flex: 1; }
.remove-column { border: 0; background: transparent; color: var(--danger-color); cursor: pointer; }
.add-column { display: flex; gap: 8px; margin-top: 12px; }
.add-column input { flex: 1; }
.builder-actions { margin-top: 12px; }
.drop-zone {
  min-height: 132px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px;
  border: 2px dashed var(--border-color);
  background: var(--bg-column);
  color: var(--text-secondary);
  cursor: pointer;
  text-align: center;
  transition: border-color .2s, background .2s;
}
.drop-zone.dragging, .drop-zone.selected { border-color: var(--accent-color); }
.drop-zone strong { color: var(--text-primary); overflow-wrap: anywhere; }
.hidden-input { display: none; }
.remove-file {
  border: 0;
  background: transparent;
  color: var(--danger-color);
  cursor: pointer;
  padding: 6px;
}
.upload-row { justify-content: flex-end; margin-top: 14px; }
button:disabled { opacity: .55; cursor: not-allowed; }
.required-columns { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
.required-columns code { padding: 4px 7px; background: var(--bg-column); border: 1px solid var(--border-color); }
.upload-row input { min-width: 0; flex: 1; color: var(--text-primary); }
.result { margin: 12px 0 0; color: var(--accent-color); }
.result.error { color: var(--danger-color); }
@media (max-width: 700px) {
  .import-heading, .upload-row { align-items: stretch; flex-direction: column; }
  .heading-actions, .builder-actions { flex-direction: column; }
}
</style>
