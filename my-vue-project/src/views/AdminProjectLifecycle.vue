<template>
  <div class="lifecycle-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">{{ t('adminProjectLifecycle.eyebrow') }}</p>
        <h1>{{ t('adminProjectLifecycle.title') }}</h1>
        <p class="subtitle">{{ t('adminProjectLifecycle.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton />
        <button class="icon-button" type="button" @click="goBack" :title="t('common.back')">&larr;</button>
      </div>
    </header>

    <main class="builder-layout">
      <section class="stages-panel">
        <div class="panel-header">
          <div>
            <h2>{{ t('adminProjectLifecycle.stagesTitle') }}</h2>
            <span>{{ t('adminProjectLifecycle.stagesCount', { count: stages.length }) }}</span>
          </div>
          <button class="primary-btn" type="button" @click="addStage">
            {{ t('adminProjectLifecycle.addStage') }}
          </button>
        </div>

        <div v-if="loading" class="state-message">{{ t('adminProjectLifecycle.loading') }}</div>
        <div v-else-if="stages.length === 0" class="empty-state">
          <strong>{{ t('adminProjectLifecycle.emptyTitle') }}</strong>
          <span>{{ t('adminProjectLifecycle.emptyText') }}</span>
        </div>

        <div v-else class="stage-list">
          <article v-for="(stage, index) in stages" :key="stage.localKey" class="stage-card">
            <div class="stage-order">
              <span>{{ index + 1 }}</span>
              <div class="order-actions">
                <button
                  type="button"
                  @click="moveStage(index, -1)"
                  :disabled="index === 0"
                  :title="t('adminProjectLifecycle.moveUp')"
                >
                  &uarr;
                </button>
                <button
                  type="button"
                  @click="moveStage(index, 1)"
                  :disabled="index === stages.length - 1"
                  :title="t('adminProjectLifecycle.moveDown')"
                >
                  &darr;
                </button>
              </div>
            </div>

            <div class="stage-fields">
              <div class="form-grid">
                <label>
                  <span>{{ t('adminProjectLifecycle.stageId') }}</span>
                  <input
                    v-model.trim="stage.id"
                    type="text"
                    placeholder="review"
                    @input="markDirty"
                  />
                </label>
                <label>
                  <span>{{ t('adminProjectLifecycle.stageTitle') }}</span>
                  <input
                    v-model.trim="stage.title"
                    type="text"
                    :placeholder="t('adminProjectLifecycle.stageTitlePlaceholder')"
                    @input="markDirty"
                  />
                </label>
              </div>

              <label>
                <span>{{ t('adminProjectLifecycle.description') }}</span>
                <textarea
                  v-model.trim="stage.description"
                  rows="3"
                  :placeholder="t('adminProjectLifecycle.descriptionPlaceholder')"
                  @input="markDirty"
                ></textarea>
              </label>

              <div class="roles-block">
                <span class="field-label">{{ t('adminProjectLifecycle.closerRoles') }}</span>
                <div class="role-grid">
                  <label v-for="role in roles" :key="role" class="role-option">
                    <input
                      type="checkbox"
                      :checked="stage.closer_roles.includes(role)"
                      @change="toggleRole(stage, role)"
                    />
                    <span>{{ t(`roles.${role}`) }}</span>
                  </label>
                </div>
              </div>
            </div>

            <button
              class="remove-btn"
              type="button"
              @click="removeStage(index)"
              :title="t('adminProjectLifecycle.removeStage')"
            >
              &times;
            </button>
          </article>
        </div>
      </section>

      <aside class="preview-panel">
        <div class="panel-header compact">
          <div>
            <h2>{{ t('adminProjectLifecycle.schemaTitle') }}</h2>
            <span>{{ t('adminProjectLifecycle.schemaFile') }}</span>
          </div>
        </div>

        <ol class="preview-list">
          <li v-for="stage in stages" :key="stage.localKey">
            <strong>{{ stage.title || t('adminProjectLifecycle.untitled') }}</strong>
            <span>{{ roleSummary(stage.closer_roles) }}</span>
          </li>
        </ol>

        <pre>{{ schemaPreview }}</pre>
      </aside>
    </main>

    <footer class="save-bar">
      <span class="status" :class="{ error: isError }">{{ message || statusText }}</span>
      <div class="save-actions">
        <button class="secondary-btn" type="button" @click="loadLifecycle" :disabled="loading || saving">
          {{ t('adminProjectLifecycle.reset') }}
        </button>
        <button class="primary-btn" type="button" @click="saveLifecycle" :disabled="loading || saving || !isDirty">
          {{ saving ? t('common.saving') : t('adminProjectLifecycle.saveSchema') }}
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import HomeButton from '@/components/HomeButton.vue';
import api from '@/utils/api';
import type { ProjectRole } from '@/types';

type LifecycleStage = {
  localKey: string;
  id: string;
  title: string;
  description: string;
  closer_roles: ProjectRole[];
};

type LifecycleSchema = {
  version: number;
  stages: Array<Omit<LifecycleStage, 'localKey'>>;
};

const router = useRouter();
const { t } = useI18n();
const loading = ref(false);
const saving = ref(false);
const isDirty = ref(false);
const isError = ref(false);
const message = ref('');
const version = ref(1);
const stages = ref<LifecycleStage[]>([]);

const roles: ProjectRole[] = ['customer', 'supervisor', 'expert', 'executor', 'curator'];

const schemaPreview = computed(() => JSON.stringify(buildPayload(), null, 2));
const statusText = computed(() =>
  isDirty.value
    ? t('adminProjectLifecycle.unsavedChanges')
    : t('adminProjectLifecycle.synced')
);

function isProjectRole(role: string): role is ProjectRole {
  return roles.includes(role as ProjectRole);
}

function createLocalKey() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function normalizeStage(stage: any): LifecycleStage {
  return {
    localKey: createLocalKey(),
    id: String(stage?.id || '').trim(),
    title: String(stage?.title || '').trim(),
    description: String(stage?.description || '').trim(),
    closer_roles: Array.isArray(stage?.closer_roles)
      ? stage.closer_roles.filter((role: string) => isProjectRole(role))
      : []
  };
}

function buildPayload(): LifecycleSchema {
  return {
    version: version.value,
    stages: stages.value.map(({ localKey, ...stage }) => ({
      ...stage,
      id: stage.id.trim(),
      title: stage.title.trim(),
      description: stage.description.trim(),
      closer_roles: [...stage.closer_roles]
    }))
  };
}

function markDirty() {
  isDirty.value = true;
  message.value = '';
  isError.value = false;
}

function showMessage(text: string, error = false) {
  message.value = text;
  isError.value = error;
}

function validateBeforeSave() {
  const ids = new Set<string>();
  const idPattern = /^[a-zA-Z0-9_-]+$/;

  for (const [index, stage] of stages.value.entries()) {
    const stageId = stage.id.trim();
    const number = index + 1;
    if (!stageId) return t('adminProjectLifecycle.errors.stageIdRequired', { number });
    if (!idPattern.test(stageId)) return t('adminProjectLifecycle.errors.stageIdInvalid', { id: stageId });
    if (!stage.title.trim()) return t('adminProjectLifecycle.errors.stageTitleRequired', { number });
    if (ids.has(stageId)) return t('adminProjectLifecycle.errors.stageIdDuplicate', { id: stageId });
    ids.add(stageId);
  }

  return '';
}

async function loadLifecycle() {
  loading.value = true;
  showMessage('');

  try {
    const { data } = await api.get<LifecycleSchema>('/admin/project-lifecycle');
    version.value = data.version || 1;
    stages.value = (data.stages || []).map(normalizeStage);
    isDirty.value = false;
  } catch (error) {
    console.error(error);
    showMessage(t('adminProjectLifecycle.loadError'), true);
  } finally {
    loading.value = false;
  }
}

async function saveLifecycle() {
  const validationError = validateBeforeSave();
  if (validationError) {
    showMessage(validationError, true);
    return;
  }

  saving.value = true;
  showMessage('');

  try {
    const { data } = await api.put('/admin/project-lifecycle', buildPayload());
    const schema = data.schema || buildPayload();
    version.value = schema.version || 1;
    stages.value = (schema.stages || []).map(normalizeStage);
    isDirty.value = false;
    showMessage(t('adminProjectLifecycle.saveSuccess'));
  } catch (error: any) {
    console.error(error);
    showMessage(error.response?.data?.detail || t('adminProjectLifecycle.saveError'), true);
  } finally {
    saving.value = false;
  }
}

function addStage() {
  stages.value.push({
    localKey: createLocalKey(),
    id: `stage_${stages.value.length + 1}`,
    title: t('adminProjectLifecycle.newStage'),
    description: '',
    closer_roles: []
  });
  markDirty();
}

function removeStage(index: number) {
  stages.value.splice(index, 1);
  markDirty();
}

function moveStage(index: number, direction: -1 | 1) {
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= stages.value.length) return;

  const [stage] = stages.value.splice(index, 1);
  if (!stage) return;
  stages.value.splice(nextIndex, 0, stage);
  markDirty();
}

function toggleRole(stage: LifecycleStage, role: ProjectRole) {
  if (stage.closer_roles.includes(role)) {
    stage.closer_roles = stage.closer_roles.filter((item) => item !== role);
  } else {
    stage.closer_roles = [...stage.closer_roles, role];
  }
  markDirty();
}

function roleSummary(selectedRoles: ProjectRole[]) {
  if (!selectedRoles.length) return t('adminProjectLifecycle.noRolesSelected');
  return selectedRoles.map((role) => t(`roles.${role}`)).join(', ');
}

function goBack() {
  router.push('/admin');
}

onMounted(loadLifecycle);
</script>

<style scoped>
.lifecycle-page {
  min-height: 100vh;
  background: var(--bg-page);
  color: var(--text-primary);
  padding: 20px 20px 96px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  max-width: 1280px;
  margin: 0 auto 20px;
}

.eyebrow {
  color: var(--accent-color);
  font-size: 0.82rem;
  font-weight: 700;
  margin: 0 0 4px;
  text-transform: uppercase;
}

.page-header h1 {
  color: var(--heading-color);
  font-size: 2rem;
  margin: 0 0 6px;
}

.subtitle {
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.icon-button,
.order-actions button,
.remove-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  cursor: pointer;
}

.icon-button {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  font-size: 1.4rem;
}

.builder-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 20px;
  max-width: 1280px;
  margin: 0 auto;
}

.stages-panel,
.preview-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-header.compact {
  margin-bottom: 12px;
}

.panel-header h2,
.preview-panel h2 {
  color: var(--heading-color);
  font-size: 1.2rem;
  margin: 0 0 4px;
}

.panel-header span {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.stage-card {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) 44px;
  gap: 16px;
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
}

.stage-order {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.stage-order > span {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent-color);
  color: var(--button-text);
  font-weight: 700;
}

.order-actions {
  display: flex;
  gap: 6px;
}

.order-actions button {
  width: 28px;
  height: 28px;
  border-radius: 8px;
}

.order-actions button:disabled,
.primary-btn:disabled,
.secondary-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.stage-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 14px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

label span,
.field-label {
  color: var(--text-secondary);
  font-size: 0.86rem;
  font-weight: 600;
}

input,
textarea {
  width: 100%;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 8px;
  color: var(--text-primary);
  font: inherit;
  padding: 10px 12px;
}

textarea {
  resize: vertical;
}

input:focus,
textarea:focus {
  border-color: var(--accent-color);
  outline: none;
}

.roles-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 8px;
}

.role-option {
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  flex-direction: row;
  gap: 8px;
  padding: 10px 12px;
}

.role-option input {
  width: auto;
}

.role-option span {
  color: var(--text-primary);
}

.remove-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  color: var(--danger-color);
  font-size: 1.4rem;
}

.primary-btn,
.secondary-btn {
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
  padding: 10px 16px;
}

.primary-btn {
  background: var(--accent-color);
  border: 1px solid var(--accent-color);
  color: var(--button-text);
}

.primary-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.secondary-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.preview-panel {
  align-self: start;
  position: sticky;
  top: 20px;
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 18px 0;
  padding-left: 22px;
}

.preview-list li strong,
.preview-list li span {
  display: block;
}

.preview-list li span {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 4px;
}

pre {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.78rem;
  max-height: 380px;
  overflow: auto;
  padding: 12px;
  white-space: pre-wrap;
}

.state-message,
.empty-state {
  color: var(--text-secondary);
  padding: 24px 0;
  text-align: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-state strong {
  color: var(--heading-color);
}

.save-bar {
  position: fixed;
  right: 20px;
  bottom: 20px;
  left: 20px;
  max-width: 1280px;
  margin: 0 auto;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow-strong);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 14px 18px;
}

.status {
  color: var(--accent-color);
  font-weight: 600;
}

.status.error {
  color: var(--danger-color);
}

.save-actions {
  display: flex;
  gap: 10px;
}

@media (max-width: 980px) {
  .page-header,
  .builder-layout,
  .save-bar {
    max-width: 760px;
  }

  .page-header,
  .builder-layout {
    grid-template-columns: 1fr;
  }

  .builder-layout {
    display: flex;
    flex-direction: column;
  }

  .preview-panel {
    position: static;
  }

  .stage-card {
    grid-template-columns: 1fr;
  }

  .stage-order {
    align-items: flex-start;
    flex-direction: row;
  }

  .remove-btn {
    justify-self: end;
  }
}

@media (max-width: 640px) {
  .page-header,
  .save-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .header-actions,
  .save-actions {
    flex-wrap: wrap;
  }

  .form-grid,
  .role-grid {
    grid-template-columns: 1fr;
  }
}
</style>
