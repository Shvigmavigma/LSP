<template>
  <div class="admin-default-tasks">
    <header class="page-header">
      <h1>{{ $t('adminDefaultTasks.title') }}</h1>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <button class="home-button" @click="goHome">🏠</button>
        <button class="back-button" @click="goBack">◀</button>
      </div>
    </header>

    <div class="editor-container">
      <div class="tree-panel">
        <h3>{{ $t('adminDefaultTasks.structure') }}</h3>
        <div class="tree">
          <div v-for="(cls, classKey) in data" :key="classKey" class="tree-node">
            <div class="node-header">
              <span class="node-title">{{ cls.label }}</span>
              <button class="add-btn-small" @click="openAddDirectionDialog(String(classKey))">
                + {{ $t('adminDefaultTasks.addDirection') }}
              </button>
              <button class="delete-btn-small" @click="openConfirmDeleteClass(String(classKey))" :title="$t('common.delete')">🗑</button>
            </div>
            <div v-if="cls.directions" class="tree-children">
              <div v-for="(dir, dirKey) in cls.directions" :key="dirKey" class="tree-node child">
                <div class="node-header">
                  <span class="node-title">{{ dir.label }}</span>
                  <button class="edit-direction-btn" @click="openEditDirectionDialog(String(classKey), String(dirKey))" :title="$t('adminDefaultTasks.editDirection')">✎</button>
                  <button class="edit-btn-small" @click="editTasks(String(classKey), String(dirKey))">{{ $t('adminDefaultTasks.editTasks') }}</button>
                  <button class="delete-btn-small" @click="openConfirmDeleteDirection(String(classKey), String(dirKey))" :title="$t('common.delete')">🗑</button>
                </div>
              </div>
            </div>
            <div v-else class="tree-actions">
              <button class="edit-btn-small" @click="editTasks(String(classKey))">{{ $t('adminDefaultTasks.editTasks') }}</button>
            </div>
          </div>
        </div>
        <button class="add-class-btn" @click="openAddClassDialog">+ {{ $t('adminDefaultTasks.addClass') }}</button>
      </div>

      <div class="tasks-editor" v-if="editingTasks !== null">
        <h3>{{ $t('adminDefaultTasks.editingTasksTitle', { path: currentPath }) }}</h3>
        <div class="tasks-list-editor">
          <div v-for="(task, idx) in editingTasks" :key="idx" class="task-editor-card">
            <div class="task-editor-header">
              <div class="task-title-wrapper">
                <span class="task-number">{{ $t('adminDefaultTasks.taskNumber', { number: idx + 1 }) }}</span>
                <input v-model="task.title" :placeholder="$t('adminDefaultTasks.taskTitlePlaceholder')" class="task-title-input" />
              </div>
              <button class="remove-task-btn" @click="removeTask(idx)" :title="$t('common.delete')">✕</button>
            </div>
            
            <div class="form-row">
              <div class="form-field">
                <label>{{ $t('adminDefaultTasks.taskDescriptionLabel') }}</label>
                <textarea v-model="task.body" :placeholder="$t('adminDefaultTasks.taskDescriptionPlaceholder')" rows="3"></textarea>
              </div>
            </div>

            <div class="form-row two-columns">
              <div class="form-field">
                <label>{{ $t('adminDefaultTasks.startDate') }}</label>
                <input v-model="task.timeline" :placeholder="$t('adminDefaultTasks.datePlaceholder')" />
              </div>
              <div class="form-field">
                <label>{{ $t('adminDefaultTasks.endDate') }}</label>
                <input v-model="task.timelinend" :placeholder="$t('adminDefaultTasks.datePlaceholder')" />
              </div>
            </div>

            <div class="required-files-editor">
              <div class="section-header">
                <label>📎 {{ $t('adminDefaultTasks.requiredFiles') }}</label>
                <button class="add-rf-btn" @click="addRequiredFile(idx)">+ {{ $t('common.add') }}</button>
              </div>
              <div v-if="task.required_files?.length === 0" class="empty-files">
                {{ $t('adminDefaultTasks.noRequiredFiles') }}
              </div>
              <div v-else class="rf-list">
                <div v-for="(rf, rfIdx) in task.required_files" :key="rfIdx" class="rf-item">
                  <div class="rf-inputs">
                    <input v-model="rf.name" :placeholder="$t('adminDefaultTasks.fileNamePlaceholder')" class="rf-name" />
                    <input v-model="rf.description" :placeholder="$t('adminDefaultTasks.fileDescriptionPlaceholder')" class="rf-desc" />
                  </div>
                  <button class="remove-rf-btn" @click="removeRequiredFile(idx, Number(rfIdx))" :title="$t('common.delete')">✕</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="editor-footer">
          <button class="add-task-btn" @click="addTask">+ {{ $t('adminDefaultTasks.addTask') }}</button>
          <div class="editor-actions">
            <button class="save-btn" @click="saveTasks">💾 {{ $t('common.save') }}</button>
            <button class="cancel-btn" @click="cancelEdit">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно для ввода текста -->
    <Teleport to="body">
      <div v-if="showInputModal" class="modal-overlay" @click.self="closeInputModal">
        <div class="modal-content">
          <h3>{{ inputModalTitle }}</h3>
          <input
            v-model="inputModalValue"
            type="text"
            class="modal-input"
            :placeholder="inputModalPlaceholder"
            @keyup.enter="confirmInputModal"
            autofocus
          />
          <div class="modal-actions">
            <button class="modal-confirm" @click="confirmInputModal">{{ $t('common.confirm') }}</button>
            <button class="modal-cancel" @click="closeInputModal">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Модальное окно подтверждения -->
    <Teleport to="body">
      <div v-if="showConfirmDialog" class="modal-overlay" @click.self="closeConfirmDialog">
        <div class="modal-content">
          <h3>{{ confirmDialogTitle }}</h3>
          <p>{{ confirmDialogMessage }}</p>
          <div class="modal-actions">
            <button class="modal-confirm danger" @click="executeConfirm">{{ $t('common.confirm') }}</button>
            <button class="modal-cancel" @click="closeConfirmDialog">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const { t } = useI18n();
const router = useRouter();
const data = ref<any>({});
const editingTasks = ref<any[] | null>(null);
const currentClass = ref('');
const currentDirection = ref('');
const currentPath = ref('');

// Состояния для модального окна ввода
const showInputModal = ref(false);
const inputModalTitle = ref('');
const inputModalPlaceholder = ref('');
const inputModalValue = ref('');
let inputModalCallback: ((value: string) => void) | null = null;

// Состояния для модального окна подтверждения
const showConfirmDialog = ref(false);
const confirmDialogTitle = ref('');
const confirmDialogMessage = ref('');
let confirmCallback: (() => void) | null = null;

// Генерация ключа
function generateKey(label: string): string {
  return label
    .toLowerCase()
    .replace(/[а-яё]/g, (c) => {
      const map: Record<string, string> = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
      };
      return map[c] || c;
    })
    .replace(/[^a-z0-9_]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/, '');
}

const loadData = async () => {
  const res = await axios.get('/default-tasks');
  data.value = res.data;
};

const goHome = () => router.push('/main');
const goBack = () => router.push('/admin');

// --- Модальное окно ввода ---
function openInputDialog(title: string, placeholder: string, callback: (value: string) => void, initialValue = '') {
  inputModalTitle.value = title;
  inputModalPlaceholder.value = placeholder;
  inputModalValue.value = initialValue;
  inputModalCallback = callback;
  showInputModal.value = true;
}

function closeInputModal() {
  showInputModal.value = false;
  inputModalValue.value = '';
  inputModalCallback = null;
}

function confirmInputModal() {
  if (inputModalCallback && inputModalValue.value.trim()) {
    inputModalCallback(inputModalValue.value.trim());
  }
  closeInputModal();
}

// --- Модальное окно подтверждения ---
function openConfirmDialog(title: string, message: string, callback: () => void) {
  confirmDialogTitle.value = title;
  confirmDialogMessage.value = message;
  confirmCallback = callback;
  showConfirmDialog.value = true;
}

function closeConfirmDialog() {
  showConfirmDialog.value = false;
  confirmCallback = null;
}

function executeConfirm() {
  if (confirmCallback) confirmCallback();
  closeConfirmDialog();
}

// --- Логика классов и направлений ---
const addClass = async (label: string) => {
  const classKey = generateKey(label);
  if (data.value[classKey]) {
    alert(t('adminDefaultTasks.errorClassExists'));
    return;
  }
  try {
    await axios.post('/admin/default-tasks/class', { class_key: classKey, label });
    await loadData();
  } catch (e) {
    console.error(e);
    alert(t('adminDefaultTasks.errorAddClass'));
  }
};

const openAddClassDialog = () => {
  openInputDialog(
    t('adminDefaultTasks.promptAddClass'),
    t('adminDefaultTasks.classNamePlaceholder'),
    addClass
  );
};

const deleteClass = async (classKey: string) => {
  try {
    await axios.delete(`/admin/default-tasks/class/${classKey}`);
    await loadData();
  } catch (e) {
    alert(t('adminDefaultTasks.errorDeleteClass'));
  }
};

const openConfirmDeleteClass = (classKey: string) => {
  const label = data.value[classKey]?.label || classKey;
  openConfirmDialog(
    t('adminDefaultTasks.confirmDeleteClassTitle'),
    t('adminDefaultTasks.confirmDeleteClassMessage', { label }),
    () => deleteClass(classKey)
  );
};

const addDirection = async (classKey: string, label: string) => {
  const dirKey = generateKey(label);
  const cls = data.value[classKey];
  if (cls?.directions?.[dirKey]) {
    alert(t('adminDefaultTasks.errorDirectionExists'));
    return;
  }
  try {
    await axios.post(`/admin/default-tasks/class/${classKey}/direction`, { direction_key: dirKey, label });
    await loadData();
  } catch (e) {
    console.error(e);
    alert(t('adminDefaultTasks.errorAddDirection'));
  }
};

const openAddDirectionDialog = (classKey: string) => {
  openInputDialog(
    t('adminDefaultTasks.promptAddDirection'),
    t('adminDefaultTasks.directionNamePlaceholder'),
    (label) => addDirection(classKey, label)
  );
};

const deleteDirection = async (classKey: string, dirKey: string) => {
  try {
    await axios.delete(`/admin/default-tasks/class/${classKey}/direction/${dirKey}`);
    await loadData();
  } catch (e) {
    alert(t('adminDefaultTasks.errorDeleteDirection'));
  }
};

const openConfirmDeleteDirection = (classKey: string, dirKey: string) => {
  const cls = data.value[classKey];
  const dirLabel = cls?.directions?.[dirKey]?.label || dirKey;
  openConfirmDialog(
    t('adminDefaultTasks.confirmDeleteDirectionTitle'),
    t('adminDefaultTasks.confirmDeleteDirectionMessage', { label: dirLabel }),
    () => deleteDirection(classKey, dirKey)
  );
};

const editDirection = async (classKey: string, dirKey: string, newLabel: string) => {
  const newKey = generateKey(newLabel);
  if (newKey !== dirKey && data.value[classKey]?.directions?.[newKey]) {
    alert(t('adminDefaultTasks.errorDirectionExists'));
    return;
  }
  try {
    await axios.put(`/admin/default-tasks/class/${classKey}/direction/${dirKey}`, {
      new_label: newLabel,
      new_key: newKey
    });
    await loadData();
    if (currentClass.value === classKey && currentDirection.value === dirKey) {
      currentDirection.value = newKey;
      currentPath.value = `${data.value[classKey].label} → ${newLabel}`;
    }
  } catch (e) {
    console.error(e);
    alert(t('adminDefaultTasks.errorUpdateDirection'));
  }
};

const openEditDirectionDialog = (classKey: string, dirKey: string) => {
  const currentLabel = data.value[classKey]?.directions?.[dirKey]?.label || '';
  openInputDialog(
    t('adminDefaultTasks.promptEditDirection'),
    t('adminDefaultTasks.directionNamePlaceholder'),
    (newLabel) => editDirection(classKey, dirKey, newLabel),
    currentLabel
  );
};

// --- Редактирование задач ---
const editTasks = (classKey: string, directionKey?: string) => {
  currentClass.value = classKey;
  currentDirection.value = directionKey || '';
  if (directionKey) {
    const tasks = data.value[classKey]?.directions?.[directionKey]?.tasks || [];
    editingTasks.value = JSON.parse(JSON.stringify(tasks));
    currentPath.value = `${data.value[classKey].label} → ${data.value[classKey].directions[directionKey].label}`;
  } else {
    const tasks = data.value[classKey]?.tasks || [];
    editingTasks.value = JSON.parse(JSON.stringify(tasks));
    currentPath.value = data.value[classKey].label;
  }
};

const addTask = () => {
  if (!editingTasks.value) return;
  editingTasks.value.push({
    title: '',
    body: '',
    status: 'ожидает',
    timeline: '',
    timelinend: '',
    required_files: []
  });
};

const removeTask = (idx: number) => {
  if (!editingTasks.value) return;
  editingTasks.value.splice(idx, 1);
};

const addRequiredFile = (taskIdx: number) => {
  if (!editingTasks.value) return;
  if (!editingTasks.value[taskIdx].required_files) {
    editingTasks.value[taskIdx].required_files = [];
  }
  editingTasks.value[taskIdx].required_files.push({ name: '', description: '' });
};

const removeRequiredFile = (taskIdx: number, rfIdx: number) => {
  if (!editingTasks.value) return;
  editingTasks.value[taskIdx].required_files.splice(rfIdx, 1);
};

const saveTasks = async () => {
  if (!editingTasks.value) return;
  try {
    if (currentDirection.value) {
      await axios.put(
        `/admin/default-tasks/class/${currentClass.value}/direction/${currentDirection.value}/tasks`,
        editingTasks.value
      );
    } else {
      await axios.put(`/admin/default-tasks/class/${currentClass.value}/tasks`, editingTasks.value);
    }
    await loadData();
    editingTasks.value = null;
    alert(t('adminDefaultTasks.saveSuccess'));
  } catch (e) {
    alert(t('adminDefaultTasks.saveError'));
  }
};

const cancelEdit = () => {
  editingTasks.value = null;
};

onMounted(loadData);
</script>

<style scoped>
/* Основные стили */
.admin-default-tasks {
  min-height: 100vh;
  background: var(--bg-page);
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--heading-color);
  /* градиент убран */
}

.header-actions {
  display: flex;
  gap: 12px;
}

.home-button, .back-button {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 44px;
  height: 44px;
  font-size: 1.6rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border-color 0.2s;
  color: var(--text-primary);
}
.home-button:hover, .back-button:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
  /* scale и translate убраны */
}

.editor-container {
  display: flex;
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Левая панель (дерево) */
.tree-panel {
  flex: 1;
  background: var(--bg-card);
  border-radius: 20px;
  padding: 20px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(4px);
  border: 1px solid var(--border-color);
}
.tree-panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.3rem;
  font-weight: 500;
  color: var(--heading-color);
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 8px;
}
.tree {
  margin-bottom: 20px;
}
.tree-node {
  margin-bottom: 16px;
  padding-left: 16px;
  border-left: 2px solid var(--border-color);
}
.tree-node.child {
  margin-left: 24px;
}
.node-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.node-title {
  font-weight: 600;
  color: var(--heading-color);
  background: rgba(66, 185, 131, 0.1);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
}
.add-btn-small, .edit-btn-small, .delete-btn-small, .edit-direction-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background 0.2s;
  font-weight: 500;
}
.edit-direction-btn {
  background: #2196f3;
}
.edit-direction-btn:hover {
  background: #0b7dda;
}
.delete-btn-small {
  background: var(--danger-color);
}
.delete-btn-small:hover {
  background: #d32f2f;
}
.add-btn-small:hover, .edit-btn-small:hover {
  background: var(--accent-hover);
}
.add-class-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 8px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
  margin-top: 12px;
}
.add-class-btn:hover {
  background: var(--accent-hover);
}

/* Правая панель (редактор задач) */
.tasks-editor {
  flex: 2;
  background: var(--bg-card);
  border-radius: 20px;
  padding: 24px;
  box-shadow: var(--shadow);
  max-height: 85vh;
  overflow-y: auto;
  border: 1px solid var(--border-color);
}
.tasks-editor h3 {
  margin-top: 0;
  margin-bottom: 24px;
  font-size: 1.4rem;
  font-weight: 500;
  color: var(--heading-color);
  border-left: 4px solid var(--accent-color);
  padding-left: 16px;
}
.tasks-list-editor {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 24px;
}
.task-editor-card {
  background: var(--bg-page);
  border-radius: 20px;
  padding: 20px;
  border: 1px solid var(--border-color);
  transition: box-shadow 0.2s;
}
.task-editor-card:hover {
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
}
.task-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.task-title-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}
.task-number {
  font-weight: 600;
  color: var(--accent-color);
  background: rgba(66, 185, 131, 0.15);
  padding: 4px 12px;
  border-radius: 30px;
  font-size: 0.8rem;
}
.task-title-input {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid var(--input-border);
  border-radius: 12px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 500;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.task-title-input:focus {
  border-color: var(--accent-color);
  outline: none;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.remove-task-btn {
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  color: var(--danger-color);
  padding: 6px;
  border-radius: 50%;
  transition: background 0.2s;
}
.remove-task-btn:hover {
  background: rgba(244, 67, 54, 0.1);
}

.form-row {
  margin-bottom: 18px;
}
.form-row.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.form-field label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.form-field input, .form-field textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--input-border);
  border-radius: 12px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-field input:focus, .form-field textarea:focus {
  border-color: var(--accent-color);
  outline: none;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}

.required-files-editor {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px dashed var(--border-color);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header label {
  font-weight: 700;
  color: var(--heading-color);
  font-size: 0.95rem;
}
.add-rf-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 6px 16px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.add-rf-btn:hover {
  background: var(--accent-hover);
}
.empty-files {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 16px;
  background: var(--bg-card);
  border-radius: 12px;
  font-size: 0.85rem;
}
.rf-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rf-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-card);
  padding: 12px 16px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  transition: border-color 0.2s;
}
.rf-item:hover {
  border-color: var(--accent-color);
}
.rf-inputs {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: center;
}
.rf-name {
  flex: 2;
  padding: 8px 12px;
  border: 1px solid var(--input-border);
  border-radius: 10px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.rf-desc {
  flex: 3;
  padding: 8px 12px;
  border: 1px solid var(--input-border);
  border-radius: 10px;
  background: var(--input-bg);
  color: var(--text-primary);
}
.remove-rf-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--danger-color);
  font-size: 1.2rem;
  padding: 6px;
  border-radius: 50%;
  transition: background 0.2s;
}
.remove-rf-btn:hover {
  background: rgba(244, 67, 54, 0.1);
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 2px solid var(--border-color);
}
.add-task-btn {
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 40px;
  padding: 10px 24px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.add-task-btn:hover {
  background: var(--accent-hover);
}
.editor-actions {
  display: flex;
  gap: 15px;
}
.save-btn, .cancel-btn {
  padding: 10px 28px;
  border: none;
  border-radius: 40px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.save-btn {
  background: var(--save-btn-bg, #4caf50);
  color: white;
}
.save-btn:hover {
  filter: brightness(1.05);
}
.cancel-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.cancel-btn:hover {
  background: var(--bg-page);
}

/* Модальные окна */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-content {
  background: var(--modal-bg);
  border-radius: 32px;
  padding: 32px;
  max-width: 420px;
  width: 90%;
  box-shadow: var(--shadow-strong);
  color: var(--modal-text);
  animation: fadeSlideUp 0.2s ease;
}
.modal-content h3 {
  color: var(--heading-color);
  margin-bottom: 20px;
  font-weight: 600;
  font-size: 1.4rem;
}
.modal-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--input-border);
  border-radius: 16px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 1rem;
  margin-bottom: 24px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.modal-input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.2);
}
.modal-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}
.modal-confirm, .modal-cancel {
  padding: 10px 28px;
  border: none;
  border-radius: 40px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.modal-confirm {
  background: var(--accent-color);
  color: var(--button-text);
}
.modal-confirm:hover {
  background: var(--accent-hover);
}
.modal-confirm.danger {
  background: var(--danger-color);
}
.modal-confirm.danger:hover {
  background: #d32f2f;
}
.modal-cancel {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.modal-cancel:hover {
  background: var(--bg-page);
}

@keyframes fadeSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>