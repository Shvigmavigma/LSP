<template>
  <div class="project-details-page">
    <header class="details-header" :class="{ 'author-header': userRole }">
      <h1 v-if="!userRole" class="page-title">{{ project?.title || $t('projectDetails.defaultTitle') }}</h1>
      <div class="header-buttons">
        <button v-if="project && (userRole || isAdminOrCurator)" class="audit-header-btn" @click="openAuditLog">
          {{ $t('projectDetails.lifecycle.audit') }}
        </button>
        <ThemeToggle />
        <LanguageSwitcher />
        <HomeButton/>
        <VersionControl v-if="isAdminOrCurator && project" :project-id="project.id" />
      </div>
    </header>

    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="project">
      
      <!-- Баннер статуса одобрения - ПОКАЗЫВАЕТСЯ ТОЛЬКО ДЛЯ НЕ ОДОБРЕННЫХ ПРОЕКТОВ -->
      <div v-if="false && (userRole || isAdminOrCurator) && !project?.is_old && !isProjectApproved" class="approval-banner" :class="approvalBannerClass">
        <template v-if="approvalStatus === 'draft'">
          <span class="approval-icon">📝</span>
          <span>{{ $t('projectDetails.notApproved') }}</span>
          <button v-if="isCustomerOrAdmin" class="approval-action-btn" @click="requestApproval">
            {{ $t('projectDetails.requestApproval') }}
          </button>
        </template>
        <template v-else-if="approvalStatus === 'pending'">
          <span class="approval-icon">🕐</span>
          <span>{{ $t('projectDetails.approvalPending') }}</span>
          <button v-if="isCustomerOrAdmin" class="approval-action-btn cancel" @click="cancelApprovalRequest">
            {{ $t('projectDetails.cancelApproval') }}
          </button>
        </template>
        <template v-else-if="approvalStatus === 'rejected'">
          <span class="approval-icon">❌</span>
          <span>{{ $t('projectDetails.approvalRejected') }}</span>
          <span v-if="project?.approval_info?.approval_comment" class="rejection-reason">
            "{{ project?.approval_info?.approval_comment }}"
          </span>
          <button v-if="isCustomerOrAdmin" class="approval-action-btn" @click="requestApproval">
            {{ $t('projectDetails.resubmitApproval') }}
          </button>
        </template>
      </div>

      <!-- ==================== УЧАСТНИКИ / АДМИНЫ / КУРАТОРЫ ==================== -->
      <template v-if="userRole || isAdminOrCurator">
        <div class="author-layout">
          <div v-if="project.is_old" class="old-project-banner">
            {{ $t('projectDetails.oldProjectReadOnly') }}
          </div>
          <h1 class="project-title-center">{{ project.title }}</h1>
          <section v-if="lifecycleSchema.stages.length" class="lifecycle-train-section">
            <div class="lifecycle-train-header">
              <div class="lifecycle-title-line">
                <h3>{{ $t('projectDetails.lifecycle.title') }}</h3>
                <span v-if="project.is_old" class="old-project-badge">{{ $t('projectDetails.oldProject') }}</span>
              </div>
            </div>
            <div class="lifecycle-train">
              <div
                v-for="(stage, index) in lifecycleSchema.stages"
                :key="stage.id"
                class="train-stage"
                :class="stageStatus(stage.id)"
              >
                <div class="train-car">
                  <span class="train-index">{{ index + 1 }}</span>
                  <strong>{{ stage.title }}</strong>
                  <small>{{ stage.description }}</small>
                  <span class="stage-state">{{ stageStatusText(stage.id) }}</span>
                  <button
                    v-if="isAdminOrCurator && stageStatus(stage.id) === 'completed'"
                    class="reopen-stage-btn"
                    @click.stop="reopenLifecycleStage(stage.id)"
                  >
                    {{ $t('projectDetails.lifecycle.reopen') }}
                  </button>
                </div>
                <div v-if="index < lifecycleSchema.stages.length - 1" class="train-connector"></div>
              </div>
            </div>
            <div v-if="currentLifecycleStage" class="lifecycle-actions">
              <span>{{ $t('projectDetails.lifecycle.current') }}: <strong>{{ currentLifecycleStage.title }}</strong></span>
              <span v-if="currentLifecycleStageState?.status === 'approval_pending'" class="lifecycle-request-info">
                {{ $t('projectDetails.lifecycle.requestedBy') }}:
                <strong>{{ currentLifecycleRequesterName }}</strong>,
                {{ $t('projectDetails.lifecycle.requestedStage') }}:
                <strong>{{ currentLifecycleStage.title }}</strong>
              </span>
              <input v-model="lifecycleComment" class="lifecycle-comment" :placeholder="$t('projectDetails.lifecycle.comment')" />
              <button v-if="canCloseCurrentStage" class="lifecycle-action-btn" @click="requestLifecycleClose">
                {{ currentLifecycleRequiresApproval ? $t('projectDetails.lifecycle.requestClose') : $t('projectDetails.lifecycle.closeStage') }}
              </button>
              <template v-if="isAdminOrCurator && currentLifecycleStageState?.status === 'approval_pending'">
                <button class="lifecycle-action-btn approve" @click="decideLifecycleStage('approve')">{{ $t('common.approve') }}</button>
                <button class="lifecycle-action-btn reject" @click="decideLifecycleStage('reject')">{{ $t('common.reject') }}</button>
              </template>
            </div>
          </section>
          
          <div class="two-columns">
            <!-- ЛЕВАЯ КОЛОНКА -->
            <div class="info-column">
              <div class="project-section">
                <h3>{{ $t('projectDetails.description') }}</h3>
                <p>{{ project.body }}</p>
              </div>
              <div v-if="project.underbody" class="project-section">
                <h3>{{ $t('projectDetails.additional') }}</h3>
                <p>{{ project.underbody }}</p>
              </div>

              <!-- Ссылки проекта -->
              <div class="project-links">
                <h3>{{ $t('projectDetails.projectLinks') }}</h3>
                <div class="links-buttons">
                  <template v-if="project.links?.github">
                    <div v-if="!showEditGithub" class="link-display">
                      <a :href="project.links.github" target="_blank" class="link-button github-link">
                        <img :src="githubIcon" alt="GitHub" class="icon" />
                        {{ $t('projectDetails.githubRepo') }}
                      </a>
                      <div class="link-actions" v-if="!project.is_old || isAdminOrCurator">
                        <button class="link-edit" @click="startEditGithub" :title="$t('common.edit')">✎</button>
                        <button class="link-delete" @click="deleteGithubLink" :title="$t('common.delete')">✖</button>
                      </div>
                    </div>
                    <div v-else class="link-input-wrapper">
                      <input v-model="githubEditValue" type="url" :placeholder="$t('projectDetails.githubPlaceholder')" class="link-input" @keyup.enter="saveEditGithub" />
                      <button class="link-save" @click="saveEditGithub">✔</button>
                      <button class="link-cancel" @click="cancelEditGithub">✖</button>
                    </div>
                  </template>
                  <template v-else>
                    <div v-if="showGithubInput" class="link-input-wrapper">
                      <input v-model="githubInput" type="url" :placeholder="$t('projectDetails.githubPlaceholder')" class="link-input" @keyup.enter="saveGithubLink" />
                      <button class="link-save" @click="saveGithubLink">✔</button>
                      <button class="link-cancel" @click="cancelGithub">✖</button>
                    </div>
                    <button v-else-if="!project.is_old || isAdminOrCurator" class="link-button add-github" @click="showGithubInput = true">
                      <img :src="githubIcon" alt="GitHub" class="icon" />
                      + {{ $t('projectDetails.addGithub') }}
                    </button>
                  </template>

                  <template v-if="project.links?.google_drive">
                    <div v-if="!showEditDrive" class="link-display">
                      <a :href="project.links.google_drive" target="_blank" class="link-button drive-link">
                        <img :src="driveIcon" alt="Google Drive" class="icon" />
                        {{ $t('projectDetails.googleDrive') }}
                      </a>
                      <div class="link-actions" v-if="!project.is_old || isAdminOrCurator">
                        <button class="link-edit" @click="startEditDrive" :title="$t('common.edit')">✎</button>
                        <button class="link-delete" @click="deleteDriveLink" :title="$t('common.delete')">✖</button>
                      </div>
                    </div>
                    <div v-else class="link-input-wrapper">
                      <input v-model="driveEditValue" type="url" :placeholder="$t('projectDetails.drivePlaceholder')" class="link-input" @keyup.enter="saveEditDrive" />
                      <button class="link-save" @click="saveEditDrive">✔</button>
                      <button class="link-cancel" @click="cancelEditDrive">✖</button>
                    </div>
                  </template>
                  <template v-else>
                    <div v-if="showDriveInput" class="link-input-wrapper">
                      <input v-model="driveInput" type="url" :placeholder="$t('projectDetails.drivePlaceholder')" class="link-input" @keyup.enter="saveDriveLink" />
                      <button class="link-save" @click="saveDriveLink">✔</button>
                      <button class="link-cancel" @click="cancelDrive">✖</button>
                    </div>
                    <button v-else-if="!project.is_old || isAdminOrCurator" class="link-button add-drive" @click="showDriveInput = true">
                      <img :src="driveIcon" alt="Google Drive" class="icon" />
                      + {{ $t('projectDetails.addDrive') }}
                    </button>
                  </template>
                </div>
              </div>

              <!-- Участники -->
              <div class="project-section">
                <h3>{{ $t('projectDetails.participants') }}</h3>
                <div v-if="project.participants?.length" class="participants-list">
                  <span v-for="participant in project.participants" :key="participant.user_id" class="participant-link" @click="goToUser(participant.user_id)">
                    {{ getUserDisplayNameById(participant.user_id) }}
                    <span class="role-badge">{{ getRoleDisplay(participant.role) }}</span>
                  </span>
                </div>
                <p v-else>{{ $t('projectDetails.noParticipants') }}</p>
              </div>

              <!-- НЕОБХОДИМЫЕ РОЛИ -->
              <div v-if="Object.keys(project.required_roles || {}).length > 0" class="project-section">
                <h3>{{ $t('projectDetails.requiredRoles') }}</h3>
                <div class="required-roles-info">
                  <div v-for="(target, role) in project.required_roles" :key="role" class="role-info-item">
                    <span class="role-name">{{ getRoleDisplay(role as ProjectRole) }}</span>
                    <span class="role-target">{{ $t('projectDetails.targetCount') }}: {{ target }}</span>
                    <span class="role-current">{{ $t('projectDetails.currentCount') }}: {{ participantsCountByRole[role] || 0 }}</span>
                    <span class="role-deficit">{{ $t('projectDetails.deficit') }}: {{ Math.max(0, target - (participantsCountByRole[role] || 0)) }}</span>
                  </div>
                </div>
              </div>

              <!-- Выполненные задачи -->
              <div v-if="completedTasks.length" class="project-section">
                <h3>{{ $t('projectDetails.completedTasks') }}</h3>
                <div class="completed-tasks">
                  <div v-for="task in completedTasks" :key="task.title" class="completed-task" @click="goToTask(task)">
                    <span class="completed-task-title">{{ task.title }}</span>
                    <span class="completed-task-date">{{ formatTaskDates(task) }}</span>
                  </div>
                </div>
              </div>

              <!-- Кнопки управления проектом -->
              <div class="project-actions" v-if="hasManagementRights && (!project.is_old || isAdminOrCurator)">
                <button class="edit-project-button" @click="goToEdit">✎ {{ $t('projectDetails.editProject') }}</button>
                <button class="delete-project-button" @click="handleProjectDelete" :disabled="deleteInProgress">
                  {{ deleteInProgress ? $t('common.processing') : (isAdminOrCurator ? $t('projectDetails.deleteProject') : $t('projectDetails.hideProject')) }}
                </button>
                <button v-if="isAdminOrCurator && !project.is_old" class="mark-old-button" @click="markAsOld">
                  {{ $t('projectDetails.markAsOld') }}
                </button>
                <button v-if="isAdminOrCurator && project.is_old" class="unmark-old-button" @click="unmarkAsOld">
                  {{ $t('projectDetails.unmarkAsOld') }}
                </button>
              </div>
            </div>

            <!-- ПРАВАЯ КОЛОНКА -->
            <div class="tasks-column">
              <h3 class="tasks-section-title">{{ $t('projectDetails.activeTasks') }}</h3>

              <!-- Кнопки управления -->
              <div class="task-header-buttons">
                <!-- Предложения - только для одобренных -->
                <button v-if="showSuggestionsButton && isProjectApproved" class="suggestions-btn" @click="showSuggestions = !showSuggestions">
                  <span class="btn-content">
                    <span class="suggestions-icon">📋</span>
                    {{ showSuggestions ? $t('common.hide') : $t('suggestions.show') }} {{ $t('suggestions.title') }}
                    <span v-if="pendingSuggestionsCount > 0" class="header-unread-badge">{{ pendingSuggestionsCount }}</span>
                  </span>
                </button>

                <router-link v-if="showSuggestLink && isProjectApproved" :to="`/project/edit/${project.id}?mode=suggest`" custom v-slot="{ navigate }">
                  <button class="suggest-btn" @click="navigate">💡 {{ $t('projectDetails.suggestEdit') }}</button>
                </router-link>

                <!-- Приглашения - всегда -->
                <button v-if="showInviteButton" class="invite-btn" @click="openInviteModal">
                  ✉️ {{ $t('projectDetails.invite') }}
                </button>

                <!-- Комментарии - всегда -->
                <button class="comments-header-btn" @click="showProjectComments = !showProjectComments">
                  <span class="btn-content">
                    <span class="comment-icon">💬</span>
                    {{ showProjectComments ? $t('common.hide') : $t('common.show') }} {{ $t('commentsSection.title') }}
                    <span v-if="unreadProjectCommentsCount > 0" class="header-unread-badge">{{ unreadProjectCommentsCount }}</span>
                  </span>
                </button>

                <!-- Заявки на вступление - всегда -->
                <button v-if="showJoinRequestsButton" class="requests-btn" @click="showJoinRequests = !showJoinRequests">
                  <span class="btn-content">
                    <span class="requests-icon">👥</span>
                    {{ showJoinRequests ? $t('common.hide') : $t('projectDetails.requests') }}
                    <span v-if="pendingJoinRequestsCount > 0" class="header-unread-badge">{{ pendingJoinRequestsCount }}</span>
                  </span>
                </button>
              </div>

              <!-- Предложения - только для одобренных -->
              <div v-if="showSuggestions && isProjectApproved" class="suggestions-container">
                <SuggestionsSection
                  :project-id="project.id"
                  :suggestions="suggestions"
                  :is-project-participant="hasFullAccess"
                  :can-edit="canEdit"
                  :can-hide-comments="canHideComments"
                  :on-accept="acceptSuggestion"
                  :on-reject="rejectSuggestion"
                  :on-add-comment="addSuggestionComment"
                  :on-mark-comment-read="markSuggestionCommentRead"
                  :on-delete-comment="deleteSuggestionComment"
                  :on-hide-comment="hideSuggestionComment"
                />
              </div>

              <!-- Комментарии - всегда -->
              <div v-if="showProjectComments" class="comments-container">
                <CommentsSection
                  :comments="project.comments || []"
                  :can-comment="hasFullAccess"
                  :is-author="canEdit"
                  :can-hide-comments="canHideComments"
                  :is-admin="isAdmin"
                  :is-curator="isCurator"
                  :on-add-comment="addProjectComment"
                  :on-mark-as-read="markProjectCommentAsRead"
                  :on-hide-comment="hideProjectComment"
                  :on-restore-comment="restoreProjectComment"
                  :on-permanent-delete="permanentDeleteComment"
                />
              </div>

              <!-- Заявки на вступление - всегда -->
              <div v-if="showJoinRequests" class="requests-container">
                <div class="requests-header">
                  <h3>{{ $t('projectDetails.joinRequests') }}</h3>
                  <span v-if="pendingJoinRequestsCount > 0" class="pending-badge">{{ pendingJoinRequestsCount }}</span>
                </div>
                <div v-if="project.join_requests === undefined" class="loading">{{ $t('common.loading') }}</div>
                <div v-else-if="pendingJoinRequests.length === 0" class="no-requests">{{ $t('projectDetails.noRequests') }}</div>
                <div v-else class="requests-list">
                  <div v-for="request in pendingJoinRequests" :key="request.id" class="request-item">
                    <div class="request-info">
                      <div class="request-user">
                        <div class="user-avatar">
                          <img v-if="getUserAvatar(request.user_id)" :src="getUserAvatar(request.user_id)" :alt="getUserDisplayNameById(request.user_id)" @error="handleAuthorImageError(request.user_id)" />
                          <span v-else>{{ getUserInitials(request.user_id) }}</span>
                        </div>
                        <span class="user-name">{{ getUserDisplayNameById(request.user_id) }}</span>
                      </div>
                      <div class="request-task">
                        {{ $t('projectDetails.requestMessage') }}
                        <span v-if="request.requested_role" class="requested-role-badge">{{ getRoleDisplay(request.requested_role) }}</span>
                      </div>
                    </div>
                    <div class="request-actions">
                      <button class="accept-request-btn" @click="acceptJoinRequest(request.id)">✅ {{ $t('common.accept') }}</button>
                      <button class="reject-request-btn" @click="rejectJoinRequest(request.id)">❌ {{ $t('common.reject') }}</button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Активные задачи - только для одобренных проектов -->
              <div v-if="isProjectApproved">
                <div v-if="inProgressTasks.length > 0" class="task-group">
                  <h4 class="task-group-title in-progress-title">{{ $t('projectDetails.inProgress') }}</h4>
                  <div class="task-tree">
                    <div v-for="task in inProgressTasks" :key="task.title" class="task-node" :class="taskStatusClass(task)" @click="goToTask(task)">
                      <span class="task-icon">📄</span>
                      <div class="task-content">
                        <strong>{{ task.title }}</strong>
                        <span class="task-status">{{ getTaskStatusText(task.status) }}</span>
                        <p>{{ task.body }}</p>
                        <div v-if="task.required_files && task.required_files.length" class="task-required-files">
                          <div class="required-files-label">{{ $t('taskDetails.requiredFilesLabel') }}:</div>
                          <div class="required-files-list">
                            <div v-for="req in task.required_files" :key="req.id" class="required-file-item" :class="{ satisfied: isTaskRequiredFileAttached(task, req.id) }">
                              {{ req.name }}
                            </div>
                          </div>
                        </div>
                        <span v-if="task.status === 'в работе'" class="task-progress">{{ $t('projectDetails.progress') }}: {{ task.progress ?? 0 }}%</span>
                        <small>{{ $t('projectDetails.deadline') }}: {{ formatTaskDates(task) }}</small>
                        <span v-if="isTaskOverdue(task)" class="overdue-badge">{{ $t('projectDetails.overdue') }}</span>
                        <span v-if="isTaskInvalid(task)" class="invalid-badge">{{ $t('projectDetails.invalidDates') }}</span>
                        <span v-if="isTaskNotStarted(task)" class="not-started-badge">{{ $t('projectDetails.notStarted') }}</span>
                        <span v-if="task.assigned_to" class="assigned-info">{{ $t('projectDetails.assignee') }}: {{ getUserDisplayNameById(task.assigned_to) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="waitingTasks.length > 0" class="task-group">
                  <h4 class="task-group-title waiting-title">{{ $t('projectDetails.waiting') }}</h4>
                  <div class="task-tree">
                    <div v-for="task in waitingTasks" :key="task.title" class="task-node" :class="taskStatusClass(task)" @click="goToTask(task)">
                      <span class="task-icon">📄</span>
                      <div class="task-content">
                        <strong>{{ task.title }}</strong>
                        <span class="task-status">{{ getTaskStatusText(task.status) }}</span>
                        <p>{{ task.body }}</p>
                        <div v-if="task.required_files && task.required_files.length" class="task-required-files">
                          <div class="required-files-label">{{ $t('taskDetails.requiredFilesLabel') }}:</div>
                          <div class="required-files-list">
                            <div v-for="req in task.required_files" :key="req.id" class="required-file-item" :class="{ satisfied: isTaskRequiredFileAttached(task, req.id) }">
                              {{ req.name }}
                            </div>
                          </div>
                        </div>
                        <span v-if="task.status === 'в работе'" class="task-progress">{{ $t('projectDetails.progress') }}: {{ task.progress ?? 0 }}%</span>
                        <small>{{ $t('projectDetails.deadline') }}: {{ formatTaskDates(task) }}</small>
                        <span v-if="isTaskOverdue(task)" class="overdue-badge">{{ $t('projectDetails.overdue') }}</span>
                        <span v-if="isTaskInvalid(task)" class="invalid-badge">{{ $t('projectDetails.invalidDates') }}</span>
                        <span v-if="isTaskNotStarted(task)" class="not-started-badge">{{ $t('projectDetails.notStarted') }}</span>
                        <span v-if="task.assigned_to" class="assigned-info">{{ $t('projectDetails.assignee') }}: {{ getUserDisplayNameById(task.assigned_to) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="inProgressTasks.length === 0 && waitingTasks.length === 0" class="no-tasks">{{ $t('projectDetails.noActiveTasks') }}</div>
              </div>
              
              <!-- Сообщение для неодобренного проекта -->
              <div v-else class="not-approved-tasks-message">
                <p>📋 {{ $t('projectDetails.tasksUnavailable') }}</p>
              </div>
            </div>
          </div>

          <!-- Диаграмма Ганта - только для одобренных проектов -->
          <div v-if="isProjectApproved" class="gantt-switcher">
            <button :class="{ active: ganttMode === 'tasks' }" @click="ganttMode = 'tasks'">{{ $t('projectDetails.gantt.tasks') }}</button>
            <button :class="{ active: ganttMode === 'lifecycle' }" @click="ganttMode = 'lifecycle'">{{ $t('projectDetails.gantt.lifecycle') }}</button>
          </div>
          <GanttChart 
            v-if="isProjectApproved"
            :tasks="ganttMode === 'tasks' ? activeTasks : lifecycleGanttTasks" 
            :title="ganttMode === 'tasks' ? $t('projectDetails.timeline') : $t('projectDetails.lifecycle.title')" 
            :readonly="!canEditGantt" 
            @update-tasks="handleTaskUpdate" 
          />

          <!-- Древовидная структура - только для одобренных проектов -->
          <ProjectTree
            v-if="hasManagementRights && isProjectApproved"
            :project="{ id: project.id, title: project.title, tasks: project.tasks }"
            :project-id="project.id"
            @task-moved="handleTaskMove"
            @subtask-moved="handleSubtaskMove"
            @update-tasks="handleUpdateTasks"
          />
        </div>
      </template>

      <!-- ==================== НЕ-УЧАСТНИКИ (НЕ АДМИНЫ, НЕ КУРАТОРЫ) ==================== -->
      <template v-else>
        <!-- Старый проект – полная версия без кнопок редактирования -->
        <div v-if="project.is_old" class="author-layout">
          <div class="old-project-banner">{{ $t('projectDetails.oldProjectReadOnly') }}</div>
          <h1 class="project-title-center">{{ project.title }}</h1>
          <div class="two-columns">
            <div class="info-column">
              <div class="project-section">
                <h3>{{ $t('projectDetails.description') }}</h3>
                <p>{{ project.body }}</p>
              </div>
              <div v-if="project.underbody" class="project-section">
                <h3>{{ $t('projectDetails.additional') }}</h3>
                <p>{{ project.underbody }}</p>
              </div>
              <div class="project-links">
                <h3>{{ $t('projectDetails.projectLinks') }}</h3>
                <div class="links-buttons">
                  <a v-if="project.links?.github" :href="project.links.github" target="_blank" class="link-button github-link">
                    <img :src="githubIcon" alt="GitHub" class="icon" /> {{ $t('projectDetails.githubRepo') }}
                  </a>
                  <a v-if="project.links?.google_drive" :href="project.links.google_drive" target="_blank" class="link-button drive-link">
                    <img :src="driveIcon" alt="Google Drive" class="icon" /> {{ $t('projectDetails.googleDrive') }}
                  </a>
                </div>
              </div>
              <div class="project-section">
                <h3>{{ $t('projectDetails.participants') }}</h3>
                <div v-if="project.participants?.length" class="participants-list">
                  <span v-for="participant in project.participants" :key="participant.user_id" class="participant-link" @click="goToUser(participant.user_id)">
                    {{ getUserDisplayNameById(participant.user_id) }}
                    <span class="role-badge">{{ getRoleDisplay(participant.role) }}</span>
                  </span>
                </div>
                <p v-else>{{ $t('projectDetails.noParticipants') }}</p>
              </div>
              <div v-if="completedTasks.length" class="project-section">
                <h3>{{ $t('projectDetails.completedTasks') }}</h3>
                <div class="completed-tasks">
                  <div v-for="task in completedTasks" :key="task.title" class="completed-task" @click="goToTask(task)">
                    <span class="completed-task-title">{{ task.title }}</span>
                    <span class="completed-task-date">{{ formatTaskDates(task) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="tasks-column">
              <h3 class="tasks-section-title">{{ $t('projectDetails.activeTasks') }}</h3>
              <div v-if="inProgressTasks.length > 0" class="task-group">
                <h4 class="task-group-title in-progress-title">{{ $t('projectDetails.inProgress') }}</h4>
                <div class="task-tree">
                  <div v-for="task in inProgressTasks" :key="task.title" class="task-node" :class="taskStatusClass(task)" @click="goToTask(task)">
                    <span class="task-icon">📄</span>
                    <div class="task-content">
                      <strong>{{ task.title }}</strong>
                      <span class="task-status">{{ getTaskStatusText(task.status) }}</span>
                      <p>{{ task.body }}</p>
                      <div v-if="task.required_files && task.required_files.length" class="task-required-files">
                        <div class="required-files-label">{{ $t('taskDetails.requiredFilesLabel') }}:</div>
                        <div class="required-files-list">
                          <div v-for="req in task.required_files" :key="req.id" class="required-file-item" :class="{ satisfied: isTaskRequiredFileAttached(task, req.id) }">
                            {{ req.name }}
                          </div>
                        </div>
                      </div>
                      <span v-if="task.status === 'в работе'" class="task-progress">{{ $t('projectDetails.progress') }}: {{ task.progress ?? 0 }}%</span>
                      <small>{{ $t('projectDetails.deadline') }}: {{ formatTaskDates(task) }}</small>
                      <span v-if="isTaskOverdue(task)" class="overdue-badge">{{ $t('projectDetails.overdue') }}</span>
                      <span v-if="isTaskInvalid(task)" class="invalid-badge">{{ $t('projectDetails.invalidDates') }}</span>
                      <span v-if="isTaskNotStarted(task)" class="not-started-badge">{{ $t('projectDetails.notStarted') }}</span>
                      <span v-if="task.assigned_to" class="assigned-info">{{ $t('projectDetails.assignee') }}: {{ getUserDisplayNameById(task.assigned_to) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="waitingTasks.length > 0" class="task-group">
                <h4 class="task-group-title waiting-title">{{ $t('projectDetails.waiting') }}</h4>
                <div class="task-tree">
                  <div v-for="task in waitingTasks" :key="task.title" class="task-node" :class="taskStatusClass(task)" @click="goToTask(task)">
                    <span class="task-icon">📄</span>
                    <div class="task-content">
                      <strong>{{ task.title }}</strong>
                      <span class="task-status">{{ getTaskStatusText(task.status) }}</span>
                      <p>{{ task.body }}</p>
                      <div v-if="task.required_files && task.required_files.length" class="task-required-files">
                        <div class="required-files-label">{{ $t('taskDetails.requiredFilesLabel') }}:</div>
                        <div class="required-files-list">
                          <div v-for="req in task.required_files" :key="req.id" class="required-file-item" :class="{ satisfied: isTaskRequiredFileAttached(task, req.id) }">
                            {{ req.name }}
                          </div>
                        </div>
                      </div>
                      <span v-if="task.status === 'в работе'" class="task-progress">{{ $t('projectDetails.progress') }}: {{ task.progress ?? 0 }}%</span>
                      <small>{{ $t('projectDetails.deadline') }}: {{ formatTaskDates(task) }}</small>
                      <span v-if="isTaskOverdue(task)" class="overdue-badge">{{ $t('projectDetails.overdue') }}</span>
                      <span v-if="isTaskInvalid(task)" class="invalid-badge">{{ $t('projectDetails.invalidDates') }}</span>
                      <span v-if="isTaskNotStarted(task)" class="not-started-badge">{{ $t('projectDetails.notStarted') }}</span>
                      <span v-if="task.assigned_to" class="assigned-info">{{ $t('projectDetails.assignee') }}: {{ getUserDisplayNameById(task.assigned_to) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="inProgressTasks.length === 0 && waitingTasks.length === 0" class="no-tasks">{{ $t('projectDetails.noActiveTasks') }}</div>
            </div>
          </div>
          <GanttChart :tasks="activeTasks" :title="$t('projectDetails.timeline')" :readonly="true" @update-tasks="handleTaskUpdate" />
        </div>

        <!-- НЕ СТАРЫЙ ПРОЕКТ – карточка с возможностью откликнуться (только для одобренных) -->
        <div v-else-if="isProjectApproved" class="non-author-layout">
          <div class="project-card">
            <div class="project-section">
              <h3>{{ $t('projectDetails.description') }}</h3>
              <p>{{ project.body }}</p>
            </div>
            <div v-if="project.underbody" class="project-section">
              <h3>{{ $t('projectDetails.additional') }}</h3>
              <p>{{ project.underbody }}</p>
            </div>
            <div class="project-section">
              <h3>{{ $t('projectDetails.participants') }}</h3>
              <div v-if="project.participants?.length" class="participants-list">
                <span v-for="participant in project.participants" :key="participant.user_id" class="participant-link" @click="goToUser(participant.user_id)">
                  {{ getUserDisplayNameById(participant.user_id) }}
                  <span class="role-badge">{{ getRoleDisplay(participant.role) }}</span>
                </span>
              </div>
              <p v-else>{{ $t('projectDetails.noParticipants') }}</p>
            </div>

            <!-- Доступные роли для отклика -->
            <div v-if="availableJoinRoles.length > 0" class="respond-roles-section">
              <h4>{{ $t('projectDetails.availableRolesToJoin') }}</h4>
              <div class="roles-to-join" :key="`roles-${project.id}-${project.join_requests?.length || 0}`">
                <div v-for="roleInfo in availableJoinRoles" :key="`${roleInfo.role}-${hasPendingRequestForRole(roleInfo.role)}`" class="role-join-card">
                  <div class="role-join-header">
                    <span class="role-name">{{ getRoleDisplay(roleInfo.role) }}</span>
                    <span class="role-openings">{{ $t('projectDetails.roleOpenings', { count: roleInfo.deficit }) }}</span>
                  </div>
                  <div class="role-description">{{ getRoleDescription(roleInfo.role) }}</div>
                  
                  <button
                    class="respond-role-btn"
                    @click="respondToProjectWithRole(roleInfo.role)"
                    :disabled="hasPendingRequestForRole(roleInfo.role) || respondingRole === roleInfo.role"
                  >
                    {{ respondingRole === roleInfo.role ? $t('common.sending') : $t('projectDetails.joinAsRole', { role: getRoleDisplay(roleInfo.role) }) }}
                  </button>
                  
                  <div v-if="hasPendingRequestForRole(roleInfo.role)" class="already-responded-role">
                    {{ $t('projectDetails.alreadyResponded') }}
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else-if="userHasAnyPendingRequest" class="already-responded">
              <span class="responded-message">✅ {{ $t('projectDetails.alreadyResponded') }}</span>
            </div>
            <div v-else class="no-roles-available">
              <p>{{ $t('projectDetails.noOpenRoles') }}</p>
            </div>
          </div>
        </div>
        
        <!-- Не одобренный проект для не-участников -->
        <div v-else class="non-author-layout">
          <div class="project-card">
            <div class="project-section">
              <h3>{{ $t('projectDetails.description') }}</h3>
              <p>{{ project.body }}</p>
            </div>
            <div v-if="project.underbody" class="project-section">
              <h3>{{ $t('projectDetails.additional') }}</h3>
              <p>{{ project.underbody }}</p>
            </div>
            <div class="project-section">
              <h3>{{ $t('projectDetails.participants') }}</h3>
              <div v-if="project.participants?.length" class="participants-list">
                <span v-for="participant in project.participants" :key="participant.user_id" class="participant-link" @click="goToUser(participant.user_id)">
                  {{ getUserDisplayNameById(participant.user_id) }}
                  <span class="role-badge">{{ getRoleDisplay(participant.role) }}</span>
                </span>
              </div>
              <p v-else>{{ $t('projectDetails.noParticipants') }}</p>
            </div>
            <div class="not-approved-public-banner" style="margin-top: 20px;">
              📝 {{ $t('projectDetails.notApprovedPublic') }}
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Модальное окно приглашения -->
    <InviteModal :show="showInviteModal" :project-id="project?.id" @close="showInviteModal = false" @invite="sendInvite" />

    <!-- Фиксированная кнопка "Покинуть проект" -->
    <button v-if="canLeaveProject" class="floating-leave-button" @click="leaveProject" :disabled="deleteInProgress">
      🚪 {{ $t('projectDetails.leaveProject') }}
    </button>

    <div v-if="showAuditModal" class="audit-modal-overlay" @click.self="showAuditModal = false">
      <div class="audit-modal">
        <div class="audit-modal-header">
          <h3>{{ $t('projectDetails.lifecycle.audit') }}</h3>
          <button class="audit-close-btn" @click="showAuditModal = false">×</button>
        </div>
        <div v-if="auditItems.length" class="audit-list">
          <div v-for="item in auditItems" :key="item.id" class="audit-row">
            <span>{{ item.user_name || 'System' }}</span>
            <strong>{{ item.details?.description || item.action }}</strong>
            <small>{{ formatAuditDate(item.created_at) }}</small>
          </div>
        </div>
        <div v-else class="audit-empty">{{ $t('projectDetails.lifecycle.auditEmpty') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getUserDisplayName as displayUserName, getUserInitial as displayUserInitial } from '@/utils/userDisplay';
import { ref, onMounted, computed, watch } from 'vue';
import VersionControl from '@/components/VersionControl.vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useProjectsStore } from '@/stores/projects';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';
import ThemeToggle from '@/components/ThemeToggle.vue';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';
import CommentsSection from '@/components/CommentsSection.vue';
import SuggestionsSection from '@/components/SuggestionsSection.vue';
import InviteModal from '@/components/InviteModal.vue';
import GanttChart from '@/components/GanttChart.vue';
import ProjectTree from '@/components/ProjectTree.vue';
import type { Project, Task, Comment, ProjectRole, JoinRequest } from '@/types';
import axios from 'axios';
import HomeButton from '@/components/HomeButton.vue';
import { v4 as uuidv4 } from 'uuid';
import githubIcon from '@/assets/icons/icons8-github-30.png';
import driveIcon from '@/assets/icons/icons8-google-drive-48.png';
import { parseDate } from '@/utils/dateUtils';
import api from '@/utils/api'

const { t } = useI18n();
const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();
const authStore = useAuthStore();
const usersStore = useUsersStore();

// ========== Состояние ==========
const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref('');
const showProjectComments = ref(false);
const showSuggestions = ref(false);
const showJoinRequests = ref(false);
const respondingRole = ref<string | null>(null);
const showGithubInput = ref(false);
const githubInput = ref('');
const showDriveInput = ref(false);
const driveInput = ref('');
const showEditGithub = ref(false);
const githubEditValue = ref('');
const showEditDrive = ref(false);
const driveEditValue = ref('');
const deleteInProgress = ref(false);
const showInviteModal = ref(false);
const avatarError = ref<Record<number, boolean>>({});
const isProjectApproved = ref<boolean>(false);
const approvalStatus = ref<string>('draft');
const lifecycleSchema = ref<{ stages: Array<{ id: string; title: string; description: string; closer_roles: ProjectRole[] }> }>({ stages: [] });
const lifecycleState = ref<{ current_stage_id: string | null; stages: Array<any> }>({ current_stage_id: null, stages: [] });
const lifecycleComment = ref('');
const auditItems = ref<Array<any>>([]);
const showAuditModal = ref(false);
const ganttMode = ref<'tasks' | 'lifecycle'>('tasks');

// ========== Computed: Роли и доступы ==========
const userRole = computed<ProjectRole | null>(() => {
  if (!authStore.userId || !project.value) return null;
  const participant = project.value.participants?.find(p => p.user_id === authStore.userId);
  return participant?.role || null;
});

const isAdmin = computed(() => authStore.user?.is_admin ?? false);
const isCurator = computed(() => {
  const user = authStore.user;
  if (!user) return false;
  if (!user.is_teacher) return false;
  return user.teacher_info?.curator ?? false;
});
const isAdminOrCurator = computed(() => isAdmin.value || isCurator.value);
const isCustomerOrAdmin = computed(() => userRole.value === 'customer' || isAdminOrCurator.value);
const hasFullAccess = computed(() => !!userRole.value || isAdminOrCurator.value);

const approvalBannerClass = computed(() => {
  switch (approvalStatus.value) {
    case 'pending': return 'approval-pending';
    case 'rejected': return 'approval-rejected';
    default: return 'approval-draft';
  }
});

// ========== Computed: UI флаги ==========
const isReadonly = computed(() => {
  if (isAdminOrCurator.value) return false;
  if (!userRole.value && !isProjectApproved.value) return true;
  if (project.value?.is_old) return !isAdminOrCurator.value;
  return false;
});

const showLinkControls = computed(() => {
  if (project.value?.is_old) return isAdminOrCurator.value;
  return isCustomerOrAdmin.value;
});

const showProjectActions = computed(() => {
  if (project.value?.is_old) return isAdminOrCurator.value;
  return isCustomerOrAdmin.value;
});

const shouldShowResponseSection = computed(() => 
  !userRole.value && !isAdminOrCurator.value && !project.value?.is_old && isProjectApproved.value
);

const canEditGantt = computed(() => {
  if (isAdminOrCurator.value) return true;
  if (project.value?.is_old) return false;
  return userRole.value === 'customer' || userRole.value === 'executor';
});

const canSuggest = computed(() => 
  ['expert', 'supervisor', 'executor'].includes(userRole.value || '') || isAdminOrCurator.value
);

const canHideComments = computed(() => userRole.value === 'supervisor' || isAdminOrCurator.value);
const canInvite = computed(() => isCustomerOrAdmin.value || userRole.value === 'executor');
const canManageJoinRequests = computed(() => isCustomerOrAdmin.value);
const canLeaveProject = computed(() => userRole.value && (project.value?.participants?.length || 0) > 1);

const isTasksReadonly = computed(() => {
  if (project.value?.is_old && !isAdminOrCurator.value) return true;
  if (!userRole.value && !isProjectApproved.value) return true;
  return false;
});

const showSuggestionsButton = computed(() => hasFullAccess.value && (!project.value?.is_old || isAdminOrCurator.value) && userRole.value !== 'executor');
const showSuggestLink = computed(() => canSuggest.value && (!project.value?.is_old || isAdminOrCurator.value));
const showInviteButton = computed(() => canInvite.value && isCustomerOrAdmin.value && (!project.value?.is_old || isAdminOrCurator.value));
const showJoinRequestsButton = computed(() => canManageJoinRequests.value && isCustomerOrAdmin.value && (!project.value?.is_old || isAdminOrCurator.value));
const showSuggestionsContent = computed(() => hasFullAccess.value);
const showCommentsContent = computed(() => hasFullAccess.value);
const showJoinRequestsContent = computed(() => isCustomerOrAdmin.value);
const showProjectTree = computed(() => isCustomerOrAdmin.value);
const canComment = computed(() => hasFullAccess.value);
const hasActiveTasks = computed(() => inProgressTasks.value.length > 0 || waitingTasks.value.length > 0);
const hasManagementRights = computed(() => isCustomerOrAdmin.value);
const canEdit = computed(() => isCustomerOrAdmin.value);
const currentLifecycleStage = computed(() => lifecycleSchema.value.stages.find(stage => stage.id === lifecycleState.value.current_stage_id) || null);
const currentLifecycleStageState = computed(() => lifecycleState.value.stages.find(stage => stage.id === lifecycleState.value.current_stage_id) || null);
const canCloseCurrentStage = computed(() => {
  const stage = currentLifecycleStage.value;
  if (!stage || currentLifecycleStageState.value?.status === 'approval_pending') return false;
  if (isAdmin.value) return true;
  if (stage.closer_roles.includes('curator') && isCurator.value) return true;
  if (stage.closer_roles.includes('curator') && userRole.value) return true;
  return !!userRole.value && stage.closer_roles.includes(userRole.value);
});
const currentLifecycleRequiresApproval = computed(() => {
  const stage = currentLifecycleStage.value;
  return !!stage && stage.closer_roles.includes('curator') && !isAdminOrCurator.value;
});
const currentLifecycleRequesterName = computed(() => {
  const requesterId = currentLifecycleStageState.value?.requested_by;
  return requesterId ? getUserDisplayNameById(requesterId) : t('common.notSelected');
});

// ========== Computed: Данные ==========
const participantsCountByRole = computed(() => {
  const counts: Record<string, number> = {};
  if (!project.value?.participants) return counts;
  for (const p of project.value.participants) {
    counts[p.role] = (counts[p.role] || 0) + 1;
  }
  return counts;
});

const availableJoinRoles = computed(() => {
  if (!project.value || !authStore.user) return [];
  const required = project.value.required_roles || {};
  const roles: { role: ProjectRole; deficit: number }[] = [];
  for (const [role, target] of Object.entries(required)) {
    const current = participantsCountByRole.value[role] || 0;
    const deficit = Math.max(0, target - current);
    if (deficit > 0 && userCanActAsRole(role as ProjectRole)) {
      roles.push({ role: role as ProjectRole, deficit });
    }
  }
  return roles;
});

const userHasAnyPendingRequest = computed(() => {
  if (!authStore.userId || !project.value?.join_requests) return false;
  return project.value.join_requests.some(r => r.user_id === authStore.userId && r.status === 'pending');
});

const activeTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status !== 'выполнена') || []);
const completedTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status === 'выполнена') || []);
const inProgressTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status === 'в работе') || []);
const waitingTasks = computed<Task[]>(() => project.value?.tasks?.filter(t => t.status === 'ожидает') || []);

const lifecycleGanttTasks = computed<Task[]>(() => lifecycleSchema.value.stages.map((stage, index) => ({
  title: stage.title,
  body: stage.description,
  status: stageStatus(stage.id) === 'completed' ? 'выполнена' : stageStatus(stage.id) === 'current' ? 'в работе' : 'ожидает',
  timeline: makeLifecycleDate(index),
  timelinend: makeLifecycleDate(index + 1),
})));

const unreadProjectCommentsCount = computed(() => {
  const comments = project.value?.comments || [];
  if (canHideComments.value) return comments.filter(c => !c.isRead).length;
  return comments.filter(c => !c.hidden && !c.isRead).length;
});

const suggestions = computed(() => project.value?.suggestions || []);
const pendingSuggestionsCount = computed(() => suggestions.value.filter(s => s.status === 'pending').length);

const pendingJoinRequests = computed<JoinRequest[]>(() => 
  (project.value?.join_requests?.filter(r => r.status === 'pending') || []) as JoinRequest[]
);
const pendingJoinRequestsCount = computed(() => pendingJoinRequests.value.length);

// ========== Функция проверки одобрения ==========
async function checkApprovalStatus(projectId: number) {
  try {
    const response = await api.get(`/projects/${projectId}/is-approved`);
    isProjectApproved.value = response.data.is_approved;
    approvalStatus.value = response.data.status;
    return response.data;
  } catch (error) {
    console.error('Failed to check approval status:', error);
    // Fallback: проверяем из данных проекта
    if (project.value) {
      isProjectApproved.value = !!(project.value.is_approved || project.value.approval_info?.is_approved);
      approvalStatus.value = project.value.approval_status || project.value.approval_info?.approval_status || 'draft';
    }
    return null;
  }
}

// ========== Вспомогательные функции ==========
function userCanActAsRole(role: ProjectRole): boolean {
  const user = authStore.user;
  if (!user) return false;
  if (role === 'executor') return true;
  if (!user.is_teacher) return false;
  if (role === 'curator') return user.teacher_info?.curator === true;
  return user.teacher_info?.roles?.includes(role) || false;
}

function hasPendingRequestForRole(role: ProjectRole): boolean {
  if (!project.value?.join_requests || !authStore.userId) return false;
  return project.value.join_requests.some(r => r.user_id === authStore.userId && r.status === 'pending' && r.requested_role === role);
}

function getRoleDescription(role: ProjectRole): string {
  const descriptions: Record<ProjectRole, string> = {
    customer: t('roles.customerDesc') || '',
    supervisor: t('roles.supervisorDesc') || '',
    expert: t('roles.expertDesc') || '',
    executor: t('roles.executorDesc') || '',
    curator: t('roles.curatorDesc') || ''
  };
  return descriptions[role] || '';
}

function getUserDisplayNameById(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return user ? displayUserName(user) : `ID: ${id}`;
}

function getUserAvatar(id: number): string | undefined {
  const user = usersStore.users.find(u => u.id === id);
  return user?.avatar ? `${baseUrl}/avatars/${user.avatar}` : undefined;
}

function getUserInitials(id: number): string {
  const user = usersStore.users.find(u => u.id === id);
  return displayUserInitial(user);
}

function getRoleDisplay(role: ProjectRole): string {
  return t(`roles.${role}`);
}

function formatTaskDates(task: Task): string {
  if (task.timelinend) return `${task.timeline || '?'} – ${task.timelinend}`;
  if (task.timeline?.includes('-')) {
    const parts = task.timeline.split('-');
    return `${parts[0]} – ${parts[1]}`;
  }
  return task.timeline || '?';
}

function isTaskOverdue(task: Task): boolean {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  let endStr = task.timelinend;
  if (!endStr && task.timeline?.includes('-')) {
    const parts = task.timeline.split('-');
    endStr = parts[1];
  }
  const endDate = parseDate(endStr || '');
  if (!endDate) return false;
  return today > endDate && task.status !== 'выполнена';
}

function isTaskInvalid(task: Task): boolean {
  let startStr = task.timeline, endStr = task.timelinend;
  if (!endStr && startStr?.includes('-')) {
    const parts = startStr.split('-');
    startStr = parts[0];
    endStr = parts[1];
  }
  const start = parseDate(startStr || '');
  const end = parseDate(endStr || '');
  if (!start || !end) return true;
  return start > end;
}

function isTaskNotStarted(task: Task): boolean {
  if (isTaskInvalid(task) || isTaskOverdue(task)) return false;
  let startStr = task.timeline;
  if (!task.timelinend && startStr?.includes('-')) startStr = startStr.split('-')[0];
  const start = parseDate(startStr || '');
  if (!start) return false;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return today < start;
}

function taskStatusClass(task: Task): string {
  if (isTaskInvalid(task)) return 'task-invalid';
  if (isTaskOverdue(task)) return 'task-overdue';
  if (isTaskNotStarted(task)) return 'task-not-started';
  return '';
}

function getTaskStatusText(status: string): string {
  switch (status) {
    case 'в работе': return t('projectDetails.status.inProgress');
    case 'ожидает': return t('projectDetails.status.waiting');
    case 'выполнена': return t('projectDetails.status.completed');
    default: return status;
  }
}

function isTaskRequiredFileAttached(task: Task, requiredFileId: string): boolean {
  return task.attachments?.some(att => att.required_file_id === requiredFileId) ?? false;
}

// ========== Уведомления ==========
function makeLifecycleDate(offset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + offset * 7);
  return `${date.getDate().toString().padStart(2, '0')}.${(date.getMonth() + 1).toString().padStart(2, '0')}.${date.getFullYear()}`;
}

function stageStatus(stageId: string): string {
  return lifecycleState.value.stages.find(stage => stage.id === stageId)?.status || 'pending';
}

function stageStatusText(stageId: string): string {
  return t(`projectDetails.lifecycle.status.${stageStatus(stageId)}`);
}

function formatAuditDate(value: string): string {
  return new Date(value).toLocaleString();
}

async function loadLifecycle() {
  if (!project.value) return;
  const { data } = await api.get(`/projects/${project.value.id}/lifecycle`);
  lifecycleSchema.value = data.schema;
  lifecycleState.value = data.state;
  isProjectApproved.value = lifecycleState.value.stages[0]?.status === 'completed' || isProjectApproved.value;
}

async function requestLifecycleClose() {
  if (!project.value || !currentLifecycleStage.value) return;
  try {
    await api.post(`/projects/${project.value.id}/lifecycle/${currentLifecycleStage.value.id}/request`, { comment: lifecycleComment.value });
    lifecycleComment.value = '';
    showNotification(t('projectDetails.lifecycle.updated'), 'success');
    await loadLifecycle();
    await checkApprovalStatus(project.value.id);
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.lifecycle.error'), 'error');
  }
}

async function decideLifecycleStage(action: 'approve' | 'reject') {
  if (!project.value || !currentLifecycleStage.value) return;
  try {
    await api.post(`/admin/projects/${project.value.id}/lifecycle/${currentLifecycleStage.value.id}/decision`, { action, comment: lifecycleComment.value });
    lifecycleComment.value = '';
    showNotification(t('projectDetails.lifecycle.updated'), 'success');
    await loadLifecycle();
    await checkApprovalStatus(project.value.id);
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.lifecycle.error'), 'error');
  }
}

async function reopenLifecycleStage(stageId: string) {
  if (!project.value) return;
  try {
    await api.post(`/projects/${project.value.id}/lifecycle/${stageId}/reopen`, { comment: lifecycleComment.value });
    lifecycleComment.value = '';
    showNotification(t('projectDetails.lifecycle.updated'), 'success');
    await loadLifecycle();
    await checkApprovalStatus(project.value.id);
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.lifecycle.error'), 'error');
  }
}

async function loadAuditLog() {
  if (!project.value) return;
  const { data } = await api.get(`/projects/${project.value.id}/audit`);
  auditItems.value = data.items || [];
}

async function openAuditLog() {
  await loadAuditLog();
  showAuditModal.value = true;
}

const notification = ref({ show: false, message: '', type: 'error' as 'error' | 'info' | 'success' });
let notificationTimeout: number | null = null;

function showNotification(message: string, type: 'error' | 'info' | 'success' = 'error', duration = 5000) {
  if (notificationTimeout) clearTimeout(notificationTimeout);
  notification.value = { show: true, message, type };
  notificationTimeout = window.setTimeout(() => { notification.value.show = false; }, duration);
}

// ========== Загрузка проекта ==========
async function loadProject(force = false) {
  const id = Number(route.params.id);
  if (isNaN(id)) {
    error.value = t('projectDetails.invalidId');
    loading.value = false;
    return;
  }
  try {
    project.value = await projectsStore.fetchProjectById(id, force);
    if (usersStore.users.length === 0) await usersStore.fetchAllUsers();
    // Проверяем статус одобрения через отдельный эндпоинт
    await checkApprovalStatus(id);
    // Загружаем лайфцикл только для участников/админов/кураторов
    if (userRole.value || isAdminOrCurator.value) {
      await loadLifecycle();
    }
  } catch (err) {
    error.value = t('projectDetails.loadError');
    console.error(err);
  } finally {
    loading.value = false;
  }
}

// ========== Одобрение ==========
async function requestApproval() {
  if (!project.value) return;
  try {
    await api.post(`/projects/${project.value.id}/request-approval`);
    showNotification(t('projectDetails.approvalRequestSent'), 'success');
    await loadProject(true);
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.approvalRequestError'), 'error');
  }
}

async function cancelApprovalRequest() {
  if (!project.value) return;
  try {
    await api.post(`/projects/${project.value.id}/cancel-approval`);
    showNotification(t('projectDetails.approvalCancelled'), 'success');
    await loadProject(true);
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.cancelApprovalError'), 'error');
  }
}

// ========== Отклик ==========
async function respondToProjectWithRole(role: ProjectRole) {
  if (!project.value) return;
  if (hasPendingRequestForRole(role)) {
    showNotification(t('projectDetails.alreadyResponded'), 'info');
    return;
  }
  if (respondingRole.value === role) return;
  respondingRole.value = role;
  try {
    await api.post(`${baseUrl}/projects/${project.value.id}/join-requests`, { requested_role: role });
    showNotification(t('projectDetails.requestSent'), 'success');
    await loadProject(true);
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.requestError'), 'error');
  } finally {
    respondingRole.value = null;
  }
}

// ========== Заявки ==========
async function acceptJoinRequest(requestId: string) {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/join-requests/${requestId}/accept`);
    showNotification(t('projectDetails.requestAccepted'), 'success');
    await loadProject(true);
  } catch (err) {
    showNotification(t('projectDetails.acceptError'), 'error');
    await loadProject(true);
  }
}

async function rejectJoinRequest(requestId: string) {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/join-requests/${requestId}/reject`);
    showNotification(t('projectDetails.requestRejected'), 'success');
    await loadProject(true);
  } catch (err) {
    showNotification(t('projectDetails.rejectError'), 'error');
    await loadProject(true);
  }
}

// ========== Комментарии ==========
async function addProjectComment(content: string) {
  if (!project.value || !authStore.user || !hasFullAccess.value) return;
  const newComment: Comment = {
    id: uuidv4(),
    authorId: authStore.user.id,
    content,
    createdAt: new Date().toISOString(),
    isRead: false,
    hidden: false,
  };
  try {
    const response = await axios.post(`${baseUrl}/projects/${project.value.id}/comments`, newComment);
    project.value = response.data;
    showProjectComments.value = true;
  } catch (error) {
    alert(t('commentsSection.saveError'));
  }
}

async function markProjectCommentAsRead(commentId: string) {
  if (!project.value || !commentId) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/comments/${commentId}/read`);
    if (project.value.comments) {
      project.value.comments = project.value.comments.map(c => c.id === commentId ? { ...c, isRead: true } : c);
    }
  } catch (error) {
    alert(t('commentsSection.markReadError'));
  }
}

async function hideProjectComment(commentId: string) {
  if (!project.value || !commentId) return;
  try {
    const response = await axios.delete(`${baseUrl}/projects/${project.value.id}/comments/${commentId}`);
    project.value = response.data;
  } catch (error) {
    alert(t('commentsSection.hideError'));
  }
}

async function restoreProjectComment(commentId: string) {
  if (!project.value || !commentId) return;
  try {
    await axios.post(`${baseUrl}/projects/${project.value.id}/comments/${commentId}/restore`);
    showNotification(t('commentsSection.restoreSuccess'), 'success');
    await loadProject();
  } catch (error) {
    showNotification(t('commentsSection.restoreError'), 'error');
  }
}

async function permanentDeleteComment(commentId: string) {
  if (!project.value || !commentId) return;
  try {
    await axios.delete(`${baseUrl}/admin/comments/${commentId}`);
    showNotification(t('commentsSection.permanentDeleteSuccess'), 'success');
    await loadProject();
  } catch (error) {
    showNotification(t('commentsSection.permanentDeleteError'), 'error');
  }
}

// ========== Предложения ==========
async function acceptSuggestion(suggestionId: string) {
  if (!project.value) return;
  try {
    const response = await axios.put(`${baseUrl}/projects/${project.value.id}/suggestions/${suggestionId}/accept`);
    project.value = response.data;
  } catch (error) {
    alert(t('suggestions.acceptError'));
  }
}

async function rejectSuggestion(suggestionId: string) {
  if (!project.value) return;
  try {
    const response = await axios.put(`${baseUrl}/projects/${project.value.id}/suggestions/${suggestionId}/reject`);
    project.value = response.data;
  } catch (error) {
    alert(t('suggestions.rejectError'));
  }
}

const addSuggestionComment = async () => alert(t('suggestions.commentsNotImplemented'));
const markSuggestionCommentRead = async () => {};
const deleteSuggestionComment = async () => {};
const hideSuggestionComment = async () => {};

// ========== Приглашения ==========
async function sendInvite(userId: number, role: ProjectRole) {
  if (!project.value) return;
  try {
    await axios.post('/invitations', { project_id: project.value.id, invited_user_id: userId, role: role });
    showNotification(t('inviteModal.inviteSuccess'), 'success');
  } catch (error: any) {
    const msg = error.response?.data?.detail || t('inviteModal.inviteError');
    showNotification(msg, 'error');
  }
}

function openInviteModal() { showInviteModal.value = true; }

// ========== Ссылки ==========
async function updateProjectLinks(updates: Record<string, string | null>) {
  if (!project.value) return;
  try {
    const response = await axios.patch(`${baseUrl}/projects/${project.value.id}/links`, updates);
    project.value = response.data;
    showNotification(t('projectDetails.linkUpdated'), 'success');
  } catch (err: any) {
    showNotification(err.response?.data?.detail || t('projectDetails.linkUpdateError'), 'error');
  }
}

function saveGithubLink() { if (githubInput.value.trim()) updateProjectLinks({ github: githubInput.value.trim() }); showGithubInput.value = false; githubInput.value = ''; }
function cancelGithub() { showGithubInput.value = false; githubInput.value = ''; }
function startEditGithub() { githubEditValue.value = project.value?.links?.github || ''; showEditGithub.value = true; }
function saveEditGithub() { if (githubEditValue.value.trim()) updateProjectLinks({ github: githubEditValue.value.trim() }); showEditGithub.value = false; githubEditValue.value = ''; }
function cancelEditGithub() { showEditGithub.value = false; githubEditValue.value = ''; }
async function deleteGithubLink() {
  if (!project.value?.links?.github) return;
  if (confirm(t('projectDetails.confirmDeleteGithub'))) {
    try {
      const response = await axios.delete(`${baseUrl}/projects/${project.value.id}/links/github`);
      project.value = response.data;
      showNotification(t('projectDetails.linkDeleted'), 'success');
    } catch (err: any) { showNotification(err.response?.data?.detail || t('projectDetails.linkDeleteError'), 'error'); }
  }
}
function saveDriveLink() { if (driveInput.value.trim()) updateProjectLinks({ google_drive: driveInput.value.trim() }); showDriveInput.value = false; driveInput.value = ''; }
function cancelDrive() { showDriveInput.value = false; driveInput.value = ''; }
function startEditDrive() { driveEditValue.value = project.value?.links?.google_drive || ''; showEditDrive.value = true; }
function saveEditDrive() { if (driveEditValue.value.trim()) updateProjectLinks({ google_drive: driveEditValue.value.trim() }); showEditDrive.value = false; driveEditValue.value = ''; }
function cancelEditDrive() { showEditDrive.value = false; driveEditValue.value = ''; }
async function deleteDriveLink() {
  if (!project.value?.links?.google_drive) return;
  if (confirm(t('projectDetails.confirmDeleteDrive'))) {
    try {
      const response = await axios.delete(`${baseUrl}/projects/${project.value.id}/links/google-drive`);
      project.value = response.data;
      showNotification(t('projectDetails.linkDeleted'), 'success');
    } catch (err: any) { showNotification(err.response?.data?.detail || t('projectDetails.linkDeleteError'), 'error'); }
  }
}

// ========== Управление проектом ==========
const handleProjectDelete = async () => {
  if (!project.value) return;
  deleteInProgress.value = true;
  if (isAdminOrCurator.value) {
    if (confirm(t('projectDetails.confirmDeleteProject'))) {
      try {
        await axios.delete(`${baseUrl}/projects/${project.value.id}`);
        showNotification(t('projectDetails.projectDeleted'), 'success');
        router.push('/main');
      } catch (error) { showNotification(t('projectDetails.deleteError'), 'error'); }
    }
  } else {
    if (confirm(t('projectDetails.confirmHideProject'))) {
      try {
        await axios.patch(`${baseUrl}/projects/${project.value.id}/hide`);
        showNotification(t('projectDetails.projectHidden'), 'success');
        router.push('/main');
      } catch (error) { showNotification(t('projectDetails.hideError'), 'error'); }
    }
  }
  deleteInProgress.value = false;
};

const markAsOld = async () => {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/mark-old`);
    showNotification(t('projectDetails.markedAsOld'), 'success');
    await loadProject(true);
  } catch (err: any) { showNotification(err.response?.data?.detail || t('projectDetails.markOldError'), 'error'); }
};

const unmarkAsOld = async () => {
  if (!project.value) return;
  try {
    await axios.put(`${baseUrl}/projects/${project.value.id}/unmark-old`);
    showNotification(t('projectDetails.unmarkedAsOld'), 'success');
    await loadProject(true);
  } catch (err: any) { showNotification(err.response?.data?.detail || t('projectDetails.unmarkOldError'), 'error'); }
};

const leaveProject = async () => {
  if (!project.value || !authStore.userId) return;
  if (!confirm(t('projectDetails.confirmLeaveProject'))) return;
  deleteInProgress.value = true;
  try {
    await axios.post(`${baseUrl}/projects/${project.value.id}/leave`);
    showNotification(t('projectDetails.leftProject'), 'success');
    router.push('/my-projects');
  } catch (error: any) {
    console.error(error);
    showNotification(error.response?.data?.detail || t('projectDetails.leaveError'), 'error');
  } finally {
    deleteInProgress.value = false;
  }
};

// ========== Навигация ==========
const goToEdit = () => router.push(`/project/edit/${route.params.id}`);
const goToUser = (userId: number) => router.push(`/user/${userId}`);
const goToTask = (task: Task) => {
  if (!project.value?.tasks) return;
  const index = project.value.tasks.findIndex(t => t === task);
  if (index !== -1) router.push(`/project/${route.params.id}/task/${index}`);
};
const navigateToSuggest = () => { router.push(`/project/edit/${route.params.id}?mode=suggest`); };

// ========== Обработчики задач ==========
const handleTaskUpdate = async (payload: { task: Task; index: number }) => {
  if (!project.value || !canEditGantt.value) return;
  const tasks = [...(project.value.tasks || [])];
  tasks[payload.index] = payload.task;
  const uniqueTasks: Task[] = [];
  const seenTitles = new Set<string>();
  for (const t of tasks) {
    const title = t.title?.trim().toLowerCase();
    if (!seenTitles.has(title)) { seenTitles.add(title); uniqueTasks.push(t); }
  }
  try {
    await axios.patch(`${baseUrl}/projects/${project.value.id}/tasks`, { tasks: uniqueTasks });
    project.value = { ...project.value, tasks: uniqueTasks };
    showNotification(t('projectDetails.timelineUpdated'), 'success');
  } catch (error: any) {
    console.error('Failed to update task dates', error);
    showNotification(t('projectDetails.timelineUpdateError'), 'error');
    await loadProject(true);
  }
};

const handleTaskMove = async (fromIndex: number, toIndex: number) => {
  if (!project.value || !canEditGantt.value) return;
  const tasks = [...(project.value.tasks || [])];
  const [movedTask] = tasks.splice(fromIndex, 1);
  tasks.splice(toIndex, 0, movedTask);
  try {
    await axios.patch(`${baseUrl}/projects/${project.value.id}/tasks`, { tasks });
    project.value = { ...project.value, tasks };
    showNotification(t('projectDetails.tasksReordered'), 'success');
  } catch (error: any) {
    console.error('Failed to reorder tasks', error);
    showNotification(t('projectDetails.tasksReorderError'), 'error');
    await loadProject(true);
  }
};

const handleSubtaskMove = async (fromTaskIndex: number, fromSubtaskIndex: number, toTaskIndex: number, toSubtaskIndex: number) => {
  if (!project.value) return;
  try {
    const tasksCopy = JSON.parse(JSON.stringify(project.value.tasks || []));
    const fromSubtasks = tasksCopy[fromTaskIndex].subtasks || [];
    const [movedSubtask] = fromSubtasks.splice(fromSubtaskIndex, 1);
    tasksCopy[fromTaskIndex] = { ...tasksCopy[fromTaskIndex], subtasks: fromSubtasks };
    const toSubtasks = tasksCopy[toTaskIndex].subtasks || [];
    const insertIndex = Math.min(toSubtaskIndex, toSubtasks.length);
    toSubtasks.splice(insertIndex, 0, movedSubtask);
    tasksCopy[toTaskIndex] = { ...tasksCopy[toTaskIndex], subtasks: toSubtasks };
    await axios.patch(`${baseUrl}/projects/${project.value.id}/tasks`, { tasks: tasksCopy });
    project.value = { ...project.value, tasks: tasksCopy };
    showNotification(t('projectDetails.subtaskMoved'), 'success');
  } catch (error) {
    console.error('Failed to move subtask', error);
    showNotification(t('projectDetails.tasksUpdateError'), 'error');
    await loadProject(true);
  }
};

const handleUpdateTasks = async (tasks: Task[]) => {
  if (!project.value) return;
  try {
    await api.patch(`${baseUrl}/projects/${project.value.id}/tasks`, { tasks });
    project.value = { ...project.value, tasks };
    showNotification(t('projectDetails.tasksUpdated'), 'success');
  } catch (error) {
    console.error('Failed to update tasks', error);
    showNotification(t('projectDetails.tasksUpdateError'), 'error');
    await loadProject(true);
  }
};

const handleAuthorImageError = (id: number) => { avatarError.value[id] = true; };

// ========== Жизненный цикл ==========
onMounted(() => { loadProject(true); });
watch(() => route.params.id, () => { loadProject(true); });
</script>

<style scoped>
/* Все стили остаются без изменений (они уже есть в вашем файле) */
/* ... все стили из вашего оригинального файла ... */

.not-approved-tasks-message {
  text-align: center;
  padding: 40px 20px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px dashed var(--border-color);
  color: var(--text-secondary);
  margin-top: 20px;
}

.not-approved-tasks-message p {
  margin: 0;
  font-size: 1rem;
}
</style>

<style scoped>
/* Все стили остаются без изменений */
.approval-banner {
  max-width: 1200px;
  margin: 0 auto 20px;
  padding: 16px 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-weight: 500;
  box-shadow: var(--shadow);
}
.approval-draft { background: linear-gradient(135deg, rgba(255,152,0,0.1), rgba(255,152,0,0.05)); border: 1px solid #ff9800; color: #ff9800; }
.approval-pending { background: linear-gradient(135deg, rgba(33,150,243,0.1), rgba(33,150,243,0.05)); border: 1px solid #2196f3; color: #2196f3; }
.approval-rejected { background: linear-gradient(135deg, rgba(244,67,54,0.1), rgba(244,67,54,0.05)); border: 1px solid #f44336; color: #f44336; }
.approval-icon { font-size: 1.5rem; }
.approval-action-btn { padding: 8px 16px; border: none; border-radius: 20px; font-weight: 600; cursor: pointer; transition: all 0.2s; margin-left: auto; background: white; color: inherit; }
.approval-action-btn:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
.approval-action-btn.cancel { background: rgba(244,67,54,0.1); color: #f44336; }

.lifecycle-train-section {
  margin: 18px 0 24px;
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--bg-card);
  box-shadow: var(--shadow);
}
.lifecycle-train-header,
.lifecycle-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
}
.lifecycle-request-info {
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  background: var(--bg-page);
  border-radius: 8px;
  padding: 8px 10px;
}
.lifecycle-train-header h3 { margin: 0; }
.lifecycle-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.old-project-badge {
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 152, 0, 0.14);
  color: #ff9800;
  border: 1px solid rgba(255, 152, 0, 0.35);
  font-size: 0.85rem;
  font-weight: 700;
}
.lifecycle-train {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  padding: 16px 0;
}
.train-stage {
  display: flex;
  align-items: center;
  min-width: 190px;
}
.train-car {
  width: 180px;
  min-height: 110px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 10px;
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.train-stage.completed .train-car {
  background: var(--completed-bg);
  color: var(--text-primary);
  border-color: var(--accent-color);
}
.train-stage.current .train-car,
.train-stage.approval_pending .train-car {
  border-color: var(--accent-color);
  box-shadow: var(--shadow-strong);
}
.train-stage.rejected .train-car {
  background: var(--danger-bg);
  border-color: var(--danger-color);
}
.train-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  background: var(--accent-color);
  color: var(--button-text);
  font-size: 0.8rem;
}
.train-car small { line-height: 1.25; opacity: 0.8; }
.stage-state { margin-top: auto; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; }
.train-connector {
  width: 34px;
  height: 2px;
  background: var(--border-color);
  margin: 0 8px;
}
.lifecycle-comment {
  flex: 1;
  min-width: 220px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}
.lifecycle-action-btn,
.audit-header-btn,
.reopen-stage-btn,
.gantt-switcher button {
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-primary);
  border-radius: 8px;
  padding: 9px 14px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s;
}
.lifecycle-action-btn:hover,
.audit-header-btn:hover,
.reopen-stage-btn:hover,
.gantt-switcher button:hover { border-color: var(--accent-color); box-shadow: var(--shadow); }
.lifecycle-action-btn.approve,
.gantt-switcher button.active { background: var(--accent-color); color: var(--button-text); }
.lifecycle-action-btn.reject { color: var(--danger-color); border-color: var(--danger-color); }
.reopen-stage-btn { margin-top: 4px; padding: 7px 10px; font-size: 0.78rem; }
.audit-modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay-bg);
  display: grid;
  place-items: center;
  padding: 20px;
  z-index: 1000;
}
.audit-modal {
  width: min(720px, 100%);
  max-height: 80vh;
  overflow: auto;
  background: var(--modal-bg);
  color: var(--modal-text);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  padding: 20px;
}
.audit-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.audit-modal-header h3 { margin: 0; color: var(--heading-color); }
.audit-close-btn {
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-primary);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
}
.audit-list { display: flex; flex-direction: column; gap: 8px; }
.audit-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 8px;
  padding: 10px;
  font-size: 0.9rem;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-card);
}
.audit-empty { color: var(--text-secondary); padding: 16px 0; }
.gantt-switcher {
  display: flex;
  gap: 8px;
  margin: 18px 0 10px;
}
.rejection-reason { font-style: italic; opacity: 0.8; font-size: 0.9rem; }

.project-details-page { min-height: 100vh; background: var(--bg-page); padding: 20px; box-sizing: border-box; }
.details-header { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto 20px; gap: 10px; }
.author-header { justify-content: flex-end; }
.page-title { color: var(--heading-color); font-size: 2rem; margin: 0; flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }
.header-buttons { display: flex; gap: 10px; align-items: center; justify-content: flex-end; flex: 0 0 auto; margin-left: auto; }

.author-layout { max-width: 1200px; margin: 0 auto; }
.project-title-center { text-align: center; color: var(--heading-color); font-size: 2.5rem; margin-bottom: 30px; }
.two-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
.info-column, .tasks-column { background: var(--bg-column); backdrop-filter: blur(4px); border-radius: 24px; padding: 30px; box-shadow: var(--shadow); }

.project-section { margin-bottom: 28px; }
.project-section h3 { color: var(--heading-color); margin-bottom: 10px; font-weight: 500; }
.project-section p { color: var(--text-primary); line-height: 1.6; }

.participants-list { display: flex; flex-wrap: wrap; gap: 8px; }
.participant-link { cursor: pointer; color: var(--link-color); text-decoration: underline; margin-right: 8px; display: inline-block; }
.participant-link:hover { color: var(--link-hover); }
.role-badge { font-size: 0.8rem; background: var(--accent-color); color: white; padding: 2px 6px; border-radius: 12px; margin-left: 4px; }

.project-links { margin-bottom: 28px; }
.project-links h3 { color: var(--heading-color); margin-bottom: 10px; font-weight: 500; }
.links-buttons { display: flex; gap: 12px; flex-wrap: wrap; }
.link-button { display: inline-flex; align-items: center; justify-content: center; padding: 8px 16px; border-radius: 50px; font-size: 0.95rem; font-weight: 500; text-decoration: none; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.link-button .icon { width: 20px; height: 20px; margin-right: 6px; object-fit: contain; }
.add-github, .add-drive { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); }
.add-github:hover, .add-drive:hover { background: var(--bg-page); box-shadow: var(--shadow); }
.link-input-wrapper { display: flex; gap: 4px; align-items: center; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 50px; padding: 4px 4px 4px 12px; }
.link-input { flex: 1; min-width: 200px; background: transparent; border: none; color: var(--text-primary); font-size: 0.95rem; outline: none; }
.link-save, .link-cancel, .link-edit, .link-delete { background: transparent; border: none; font-size: 1.2rem; cursor: pointer; padding: 4px 8px; border-radius: 50%; transition: background 0.2s; display: inline-flex; align-items: center; justify-content: center; }
.link-save { color: #4caf50; } .link-save:hover { background: rgba(76,175,80,0.2); }
.link-cancel { color: #f44336; } .link-cancel:hover { background: rgba(244,67,54,0.2); }
.link-edit { color: #ff9800; } .link-edit:hover { background: rgba(255,152,0,0.2); }
.link-delete { color: #f44336; } .link-delete:hover { background: rgba(244,67,54,0.2); }
.link-display { display: flex; align-items: center; gap: 8px; }
.link-actions { display: flex; gap: 4px; }
.github-link { background: #24292e; color: white; } .github-link:hover { background: #2c3e50; box-shadow: var(--shadow-strong); }
.drive-link { background: #4285f4; color: white; } .drive-link:hover { background: #3367d6; box-shadow: var(--shadow-strong); }

.required-roles-info { background: var(--bg-page); border-radius: 12px; padding: 12px; margin-top: 8px; }
.role-info-item { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border-color); }
.role-info-item:last-child { border-bottom: none; }
.role-name { font-weight: 600; min-width: 100px; }
.role-target, .role-current, .role-deficit { font-size: 0.9rem; color: var(--text-secondary); }

.completed-tasks { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.completed-task { cursor: pointer; background: var(--completed-bg); padding: 10px; border-radius: 8px; border-left: 4px solid var(--accent-color); transition: all 0.2s; }
.completed-task:hover { background: var(--bg-card); box-shadow: var(--shadow); }
.completed-task.readonly { cursor: default; }
.completed-task.readonly:hover { background: var(--completed-bg); box-shadow: none; }
.completed-task-title { font-weight: 600; color: var(--heading-color); }
.completed-task-date { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }

.project-actions { margin-top: 30px; display: flex; gap: 12px; flex-wrap: wrap; }
.edit-project-button, .delete-project-button, .mark-old-button, .unmark-old-button { flex: 1; padding: 12px 20px; border: none; border-radius: 50px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
.edit-project-button { background: var(--accent-color); color: var(--button-text); }
.edit-project-button:hover { background: transparent; color: var(--accent-color); border: 1px solid var(--accent-color); }
.delete-project-button { background: var(--danger-bg); color: var(--danger-color); }
.delete-project-button:hover { background: transparent; color: var(--danger-color); border: 1px solid var(--danger-color); }
.mark-old-button { background: #ff9800; color: white; }
.mark-old-button:hover { background: #e68900; }
.unmark-old-button { background: #2196f3; color: white; }
.unmark-old-button:hover { background: #0b7dda; }

.tasks-section-title { color: var(--heading-color); font-weight: 500; font-size: 1.5rem; margin: 0 0 15px 0; }
.task-header-buttons { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
.suggestions-btn, .suggest-btn, .invite-btn, .comments-header-btn, .requests-btn { background: var(--accent-color); color: var(--button-text); border: none; border-radius: 30px; padding: 8px 16px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; box-shadow: var(--shadow); display: inline-flex; align-items: center; }
.btn-content { display: flex; align-items: center; gap: 6px; }
.header-unread-badge { background: #f44336; color: white; border-radius: 50%; min-width: 20px; height: 20px; font-size: 11px; font-weight: bold; display: inline-flex; align-items: center; justify-content: center; padding: 0 4px; margin-left: 4px; }

.comments-container, .suggestions-container, .requests-container { margin-bottom: 25px; border: 1px solid var(--border-color); border-radius: 16px; overflow: hidden; width: 100%; box-sizing: border-box; background: var(--bg-card); padding: 15px; }
.requests-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid var(--border-color); }
.requests-header h3 { color: var(--heading-color); font-size: 1.2rem; font-weight: 500; margin: 0; }
.pending-badge { background: var(--accent-color); color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.9rem; }
.requests-list { display: flex; flex-direction: column; gap: 12px; }
.request-item { background: var(--bg-page); border-radius: 12px; padding: 12px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; border-left: 4px solid #ff9800; }
.request-info { flex: 1; min-width: 200px; }
.request-user { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.user-avatar { width: 24px; height: 24px; border-radius: 50%; background: var(--accent-color); color: var(--button-text); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; overflow: hidden; }
.user-avatar img { width: 100%; height: 100%; object-fit: cover; }
.user-name { font-weight: 600; color: var(--heading-color); }
.request-task { font-size: 0.9rem; color: var(--text-primary); margin-bottom: 2px; }
.requested-role-badge { display: inline-block; margin-left: 8px; background: var(--accent-color); color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; }
.request-actions { display: flex; gap: 8px; }
.accept-request-btn, .reject-request-btn { padding: 6px 12px; border: none; border-radius: 20px; font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: background 0.2s; }
.accept-request-btn { background: #4caf50; color: white; } .accept-request-btn:hover { background: #45a049; }
.reject-request-btn { background: #f44336; color: white; } .reject-request-btn:hover { background: #da190b; }

.task-group { margin-bottom: 30px; }
.task-group-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 15px; padding-bottom: 5px; border-bottom: 2px solid; }
.task-group-title.in-progress-title { color: var(--accent-color); border-bottom-color: var(--accent-color); }
.task-group-title.waiting-title { color: #ff9800; border-bottom-color: #ff9800; }
.task-tree { display: flex; flex-direction: column; gap: 15px; }
.task-node { display: flex; align-items: flex-start; gap: 15px; padding: 15px; background: var(--bg-card); border-radius: 12px; box-shadow: var(--shadow); cursor: pointer; transition: all 0.2s; border-left: 4px solid var(--accent-color); }
.task-node:hover { transform: translateX(5px); box-shadow: var(--shadow-strong); }
.task-node.readonly { cursor: default; opacity: 0.8; }
.task-node.readonly:hover { transform: none; box-shadow: var(--shadow); }
.task-node.task-overdue { background-color: var(--overdue-bg); border-left-color: #f44336; }
.task-node.task-invalid { background-color: var(--invalid-bg); border-left-color: #9e9e9e; opacity: 0.7; }
.task-node.task-not-started { background-color: var(--not-started-bg); border-left-color: #bdbdbd; opacity: 0.8; }
.task-icon { font-size: 1.5rem; color: var(--accent-color); }
.task-content { flex: 1; }
.task-content strong { color: var(--heading-color); display: block; margin-bottom: 4px; }
.task-status { color: var(--text-secondary); font-size: 0.9rem; margin-left: 8px; }
.task-content p { color: var(--text-primary); margin: 8px 0 4px; }
.task-required-files { margin-top: 8px; font-size: 0.8rem; }
.required-files-label { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; }
.required-files-list { display: flex; flex-wrap: wrap; gap: 6px; }
.required-file-item { font-size: 0.75rem; color: #888; background: var(--bg-page); padding: 2px 8px; border-radius: 12px; display: inline-block; }
.required-file-item.satisfied { color: #4caf50; background: rgba(76,175,80,0.1); font-weight: 500; }
.task-progress { display: inline-block; margin-top: 4px; margin-right: 8px; font-size: 0.9rem; color: var(--heading-color); background: var(--completed-bg); padding: 2px 8px; border-radius: 12px; }
.task-content small { color: var(--text-secondary); }
.overdue-badge, .invalid-badge, .not-started-badge { display: inline-block; margin-left: 8px; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; color: white; }
.overdue-badge { background-color: #f44336; }
.invalid-badge { background-color: #9e9e9e; }
.not-started-badge { background-color: #757575; }
.assigned-info { display: inline-block; margin-left: 8px; font-size: 0.8rem; color: var(--text-secondary); background: var(--bg-card); padding: 2px 8px; border-radius: 12px; }
.no-tasks { text-align: center; color: var(--text-secondary); padding: 40px; }

.old-project-banner { background-color: #ff9800; color: white; text-align: center; padding: 12px; margin-bottom: 20px; border-radius: 8px; font-weight: 500; box-shadow: var(--shadow); }
.not-approved-public-banner { background: linear-gradient(135deg, #ff9800, #ffa726); color: white; text-align: center; padding: 12px; margin-bottom: 20px; border-radius: 8px; font-weight: 500; box-shadow: var(--shadow); }

.respond-roles-section { margin-top: 24px; padding-top: 16px; border-top: 2px dashed var(--border-color); }
.respond-roles-section h4 { color: var(--heading-color); margin-bottom: 16px; font-weight: 500; }
.roles-to-join { display: flex; flex-direction: column; gap: 16px; }
.role-join-card { background: var(--bg-card); border-radius: 16px; padding: 16px; border-left: 4px solid var(--accent-color); box-shadow: var(--shadow); }
.role-join-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.role-name { font-size: 1.1rem; font-weight: 600; color: var(--heading-color); }
.role-openings { font-size: 0.85rem; background: rgba(76,175,80,0.1); padding: 2px 8px; border-radius: 20px; color: #4caf50; }
.role-description { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 12px; }
.respond-role-btn { width: 100%; padding: 10px; background: var(--accent-color); color: var(--button-text); border: none; border-radius: 30px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.respond-role-btn:hover:not(:disabled) { background: var(--accent-hover); }
.respond-role-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.already-responded { text-align: center; padding: 12px 24px; background: rgba(76,175,80,0.1); border-radius: 30px; border: 2px solid #4caf50; color: #4caf50; font-weight: 600; font-size: 1.1rem; margin-bottom: 20px; }
.already-responded-role { text-align: center; font-size: 0.75rem; color: #4caf50; margin-top: 6px; font-style: italic; }
.no-roles-available { text-align: center; color: var(--text-secondary); padding: 20px; font-style: italic; }

.floating-leave-button { position: fixed; bottom: 20px; right: 20px; z-index: 1000; padding: 12px 24px; background: var(--danger-bg); color: var(--danger-color); border: 1px solid var(--danger-color); border-radius: 50px; font-size: 1rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; box-shadow: var(--shadow-strong); }
.floating-leave-button:hover:not(:disabled) { background: transparent; color: var(--danger-color); border-color: var(--danger-color); }
.floating-leave-button:disabled { opacity: 0.6; cursor: not-allowed; }

.loading, .error { text-align: center; color: var(--text-primary); font-size: 1.2rem; padding: 40px; }

@media (max-width: 768px) {
  .two-columns { grid-template-columns: 1fr; }
  .approval-banner { flex-direction: column; text-align: center; }
  .approval-action-btn { margin-left: 0; width: 100%; }
}
</style>
