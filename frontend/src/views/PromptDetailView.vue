<template>
  <div class="detail-page">
    <el-breadcrumb separator="/" class="detail-breadcrumb">
      <el-breadcrumb-item>
        <span class="breadcrumb-link" @click="goHome">{{ t('menu.prompt') }}</span>
      </el-breadcrumb-item>
      <el-breadcrumb-item>{{ detail?.name ?? t('promptDetail.breadcrumb.fallback') }}</el-breadcrumb-item>
    </el-breadcrumb>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
    />

    <el-skeleton v-else-if="isLoading" animated :rows="6" />

    <el-empty v-else-if="!detail" :description="t('promptDetail.empty')" />

    <template v-else>
      <el-card class="info-card">
      <template #header>
        <div class="info-header">
          <div class="info-title-group">
            <p class="info-class">{{ t('promptDetail.info.classLabel', { name: detail.prompt_class.name }) }}</p>
            <h2 class="info-title">{{ detail.name }}</h2>
            <p class="info-desc">{{ detail.description ?? t('promptDetail.info.descriptionFallback') }}</p>
          </div>
          <div class="info-meta">
            <el-tag type="success" effect="light">
              {{
                detail.current_version?.version
                  ? t('promptDetail.info.currentVersion', { version: detail.current_version.version })
                  : t('promptDetail.info.currentVersionFallback')
              }}
            </el-tag>
            <span>{{ t('promptDetail.info.updatedAt', { time: formatDateTime(detail.updated_at) }) }}</span>
          </div>
        </div>
      </template>
      <el-descriptions :column="3" border size="small" class="info-descriptions">
        <el-descriptions-item :label="t('promptDetail.info.fields.author')">
          {{ detail.author ?? t('common.notSet') }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('promptDetail.info.fields.createdAt')">
          {{ formatDateTime(detail.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('promptDetail.info.fields.updatedAt')">
          {{ formatDateTime(detail.updated_at) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('promptDetail.info.fields.classDescription')" :span="3">
          {{ detail.prompt_class.description ?? t('promptDetail.info.fields.classDescriptionFallback') }}
        </el-descriptions-item>
      </el-descriptions>
      <div class="info-tags">
        <div class="info-tags__list">
          <el-tag
            v-for="tag in detail.tags"
            :key="tag.id"
            size="small"
            effect="dark"
            :style="{ backgroundColor: tag.color, borderColor: tag.color }"
          >
            {{ tag.name }}
          </el-tag>
        </div>
        <el-button type="primary" link size="small" @click="openMetaDialog">
          {{ t('promptDetail.info.editButton') }}
        </el-button>
      </div>
      <el-dialog v-model="metaDialogVisible" :title="t('promptDetail.info.dialogTitle')" width="520px">
        <el-alert
          v-if="metaError"
          :title="metaError"
          type="warning"
          show-icon
          class="meta-alert"
        />
        <el-form label-width="80px" class="meta-form">
          <el-form-item :label="t('promptDetail.info.dialog.authorLabel')">
            <el-select
              v-model="metaAuthor"
              filterable
              clearable
              :loading="shareUserLoading"
              :placeholder="t('promptDetail.info.dialog.authorPlaceholder')"
            >
              <el-option
                v-for="user in shareUserOptions"
                :key="user.id"
                :label="user.username"
                :value="user.username"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('promptDetail.info.dialog.classLabel')">
            <el-select
              v-model="selectedClassId"
              :placeholder="t('promptDetail.info.dialog.classPlaceholder')"
              :loading="isMetaLoading"
              :disabled="isMetaLoading || !classOptions.length"
            >
              <el-option
                v-for="option in classOptions"
                :key="option.id"
                :label="option.name"
                :value="option.id"
              />
            </el-select>
            <span v-if="!classOptions.length && !isMetaLoading" class="meta-empty-tip">
              {{ t('promptDetail.info.dialog.noClassTip') }}
            </span>
          </el-form-item>
          <el-form-item :label="t('promptDetail.info.dialog.tagsLabel')">
            <el-select
              v-model="selectedTagIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              :placeholder="t('promptDetail.info.dialog.tagsPlaceholder')"
              :loading="isMetaLoading"
            >
              <el-option
                v-for="tag in tagOptions"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              >
                <span class="tag-option">
                  <span class="tag-dot" :style="{ backgroundColor: tag.color }" />
                  {{ tag.name }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="closeMetaDialog" :disabled="isMetaSaving">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="isMetaSaving" :disabled="!canSaveMeta" @click="handleSaveMeta">
            {{ t('common.save') }}
          </el-button>
        </template>
      </el-dialog>
      <div v-if="canManageSharing" class="info-share">
        <div class="info-share__header">
          <span class="info-share__title">{{ t('promptDetail.share.title') }}</span>
          <el-button type="primary" text size="small" @click="openShareDialog">
            {{ t('promptDetail.share.addButton') }}
          </el-button>
        </div>
        <el-alert
          v-if="shareError"
          :title="shareError"
          type="warning"
          show-icon
          class="share-alert"
        />
        <el-table
          v-else-if="collaborators.length"
          :data="collaborators"
          size="small"
          border
          class="share-table"
          v-loading="collaboratorsLoading"
        >
          <el-table-column :label="t('promptDetail.share.columns.username')" prop="username" />
          <el-table-column :label="t('promptDetail.share.columns.role')" prop="role">
            <template #default="{ row }">
              <el-tag :type="row.role === 'editor' ? 'success' : 'info'" size="small">
                {{
                  row.role === 'editor'
                    ? t('promptDetail.share.roles.editor')
                    : t('promptDetail.share.roles.viewer')
                }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('promptDetail.share.columns.createdAt')" prop="created_at">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('promptDetail.share.columns.actions')" width="140">
            <template #default="{ row }">
              <el-popconfirm
                :title="t('promptDetail.share.confirmRevoke', { name: row.username })"
                :confirm-button-text="t('common.delete')"
                :cancel-button-text="t('common.cancel')"
                icon=""
                @confirm="() => handleRevokeCollaborator(row)"
              >
                <template #reference>
                  <el-button
                    type="danger"
                    text
                    size="small"
                    :loading="revokeLoadingId === row.user_id"
                  >
                    {{ t('promptDetail.share.revoke') }}
                  </el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else :description="t('promptDetail.share.empty')" />
      </div>

      <el-dialog
        v-model="shareDialogVisible"
        :title="t('promptDetail.share.dialogTitle')"
        width="480px"
      >
        <el-form :model="shareForm" label-width="100px" class="share-form">
          <el-form-item :label="t('promptDetail.share.fields.username')">
            <el-select
              v-model="shareForm.username"
              filterable
              allow-create
              default-first-option
              :loading="shareUserLoading"
              :placeholder="t('promptDetail.share.placeholders.username')"
            >
              <el-option
                v-for="user in shareUserOptions"
                :key="user.id"
                :label="user.username"
                :value="user.username"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('promptDetail.share.fields.role')">
            <el-radio-group v-model="shareForm.role">
              <el-radio-button label="viewer">
                {{ t('promptDetail.share.roles.viewer') }}
              </el-radio-button>
              <el-radio-button label="editor">
                {{ t('promptDetail.share.roles.editor') }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="shareDialogVisible = false" :disabled="shareLoading">
            {{ t('common.cancel') }}
          </el-button>
          <el-button type="primary" :loading="shareLoading" @click="handleShare">
            {{ t('promptDetail.share.dialogConfirm') }}
          </el-button>
        </template>
      </el-dialog>
      </el-card>

      <el-card class="content-card">
      <template #header>
        <div class="content-header">
          <div>
            <h3 class="content-title">{{ t('promptDetail.content.title') }}</h3>
            <span class="content-subtitle">{{ t('promptDetail.content.subtitle') }}</span>
          </div>
          <div class="content-actions">
            <el-button size="small" @click="handleCreateVersion">{{ t('promptDetail.content.newVersion') }}</el-button>
            <el-button size="small" type="primary" @click="handleViewVersionCompare">{{ t('promptDetail.content.compare') }}</el-button>
          </div>
        </div>
      </template>
      <div class="content-body">
        <section class="content-main">
          <header class="content-main__meta">
            <div>
              <span class="content-main__label">{{ t('promptDetail.content.versionLabel') }}</span>
              <strong class="content-main__value">
                {{ selectedVersion?.version ?? t('promptDetail.content.versionFallback') }}
              </strong>
            </div>
            <div class="content-main__time">
              <span class="content-main__label">{{ t('promptDetail.content.updatedLabel') }}</span>
              <strong class="content-main__value">{{ formatDateTime(selectedVersion?.updated_at ?? selectedVersion?.created_at) }}</strong>
              <el-tooltip :content="t('promptDetail.content.copyTooltip')" placement="top">
                <el-button
                  class="content-copy-button"
                  :icon="DocumentCopy"
                  circle
                  size="small"
                  type="primary"
                  text
                  :disabled="!selectedVersion?.content"
                  @click.stop="handleCopyPrompt"
                />
              </el-tooltip>
            </div>
          </header>
          <div class="content-scroll">
            <template v-if="selectedVersion">
              <pre class="content-text">{{ selectedVersion.content }}</pre>
            </template>
            <el-empty v-else :description="t('promptDetail.content.empty')" />
          </div>
        </section>
        <aside class="content-history">
          <h4 class="history-title">{{ t('promptDetail.content.historyTitle') }}</h4>
          <div class="history-scroll">
            <div
              v-for="version in detail.versions"
              :key="version.id"
              :class="['history-item', { 'is-active': version.id === selectedVersionId }]"
              @click="handleSelectVersion(version.id)"
            >
              <div class="history-item__meta">
                <span class="history-version">{{ version.version }}</span>
                <span class="history-date">{{ formatDateTime(version.updated_at) }}</span>
              </div>
              <p class="history-preview">{{ summarizeContent(version.content) }}</p>
            </div>
          </div>
        </aside>
      </div>
      </el-card>
      <el-card class="implementation-card">
        <template #header>
          <div class="implementation-header">
            <div>
              <h3 class="implementation-title">
                {{ t('promptDetail.implementation.title') }}
              </h3>
              <span class="implementation-subtitle">
                {{ t('promptDetail.implementation.subtitle') }}
              </span>
            </div>
          </div>
        </template>
        <div class="implementation-body">
          <el-form label-width="80px" class="implementation-form">
            <el-form-item :label="t('promptDetail.implementation.field.label')">
              <el-input
                v-model="implementationContent"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 8 }"
                :placeholder="t('promptDetail.implementation.field.placeholder')"
              />
            </el-form-item>
          </el-form>
          <div class="implementation-actions">
            <el-button
              type="primary"
              size="small"
              :loading="implementationSaving"
              @click="handleSaveImplementation"
            >
              {{ t('promptDetail.implementation.saveButton') }}
            </el-button>
          </div>
          <el-alert
            v-if="implementationError"
            :title="implementationError"
            type="error"
            show-icon
            class="implementation-alert"
          />
          <el-skeleton
            v-else-if="implementationLoading && !implementationLogs.length"
            animated
            :rows="2"
          />
          <el-empty
            v-else-if="!implementationLogs.length"
            :description="t('promptDetail.implementation.empty')"
          />
          <div v-else class="implementation-log-list">
            <div
              v-for="log in implementationLogs"
              :key="log.id"
              class="implementation-log-item"
            >
              <div class="implementation-log-meta">
                <span class="implementation-log-time">
                  {{ formatDateTime(log.created_at) }}
                </span>
              </div>
              <p class="implementation-log-content">{{ log.content }}</p>
            </div>
          </div>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DocumentCopy } from '@element-plus/icons-vue'
import { usePromptDetail } from '../composables/usePromptDetail'
import { listPromptClasses, type PromptClassStats } from '../api/promptClass'
import { listPromptTags, type PromptTagStats } from '../api/promptTag'
import {
  listPromptCollaborators,
  revokePromptShare,
  sharePrompt,
  updatePrompt,
  listPromptImplementations,
  createPromptImplementation
} from '../api/prompt'
import { listUsers } from '../api/user'
import type {
  PromptCollaborator,
  PromptCollaboratorRole,
  PromptImplementationRecord
} from '../types/prompt'
import type { User } from '../types/user'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const { currentUser } = useAuth()
const currentId = computed(() => {
  const raw = Number(route.params.id)
  return Number.isFinite(raw) && raw > 0 ? raw : null
})

const {
  prompt: detail,
  loading: isLoading,
  error: errorMessage,
  refresh: refreshDetail
} = usePromptDetail(currentId)

const selectedVersionId = ref<number | null>(null)
const promptClasses = ref<PromptClassStats[]>([])
const promptTags = ref<PromptTagStats[]>([])
const metaError = ref<string | null>(null)
const isMetaLoading = ref(false)
const isMetaSaving = ref(false)
const selectedClassId = ref<number | null>(null)
const selectedTagIds = ref<number[]>([])
const metaDialogVisible = ref(false)
const metaAuthor = ref('')

const collaborators = ref<PromptCollaborator[]>([])
const shareError = ref<string | null>(null)
const collaboratorsLoading = ref(false)
const shareDialogVisible = ref(false)
const shareLoading = ref(false)
const revokeLoadingId = ref<number | null>(null)

const shareUserOptions = ref<User[]>([])
const shareUserLoading = ref(false)

const implementationLogs = ref<PromptImplementationRecord[]>([])
const implementationContent = ref('')
const implementationLoading = ref(false)
const implementationSaving = ref(false)
const implementationError = ref<string | null>(null)

const shareForm = reactive<{
  username: string
  role: PromptCollaboratorRole
}>({
  username: '',
  role: 'viewer'
})

const classOptions = computed(() =>
  promptClasses.value
    .map((item) => ({ id: item.id, name: item.name }))
    .sort((a, b) => a.name.localeCompare(b.name, locale.value))
)

const tagOptions = computed(() =>
  promptTags.value
    .map((tag) => ({ id: tag.id, name: tag.name, color: tag.color }))
    .sort((a, b) => a.name.localeCompare(b.name, locale.value))
)

const canManageSharing = computed(() => {
  const prompt = detail.value
  const user = currentUser.value
  if (!prompt || !user) {
    return false
  }
  if (user.is_superuser) {
    return true
  }
  if (prompt.owner_id != null && prompt.owner_id === user.id) {
    return true
  }
  return false
})

watch(
  () => detail.value,
  (value) => {
    if (!value) {
      selectedVersionId.value = null
      selectedClassId.value = null
      selectedTagIds.value = []
      void fetchCollaborators()
      return
    }
    selectedVersionId.value = value.current_version?.id ?? value.versions[0]?.id ?? null
    selectedClassId.value = value.prompt_class.id
    selectedTagIds.value = value.tags.map((tag) => tag.id)
    metaAuthor.value = value.author ?? ''
    void fetchCollaborators()
  },
  { immediate: true }
)

const selectedVersion = computed(() => {
  const prompt = detail.value
  if (!prompt) {
    return null
  }
  const match = prompt.versions.find((item) => item.id === selectedVersionId.value)
  return match ?? prompt.current_version ?? null
})

watch(classOptions, (options) => {
  if (!options.length) {
    selectedClassId.value = null
    return
  }
  if (selectedClassId.value === null) {
    selectedClassId.value = options[0].id
    return
  }
  const exists = options.some((item) => item.id === selectedClassId.value)
  if (!exists) {
    selectedClassId.value = options[0].id
  }
})

watch(tagOptions, (options) => {
  if (!options.length) {
    selectedTagIds.value = []
    return
  }
  const available = new Set(options.map((item) => item.id))
  selectedTagIds.value = selectedTagIds.value.filter((id) => available.has(id))
})

watch(
  currentId,
  () => {
    void fetchImplementationLogs()
  },
  { immediate: true }
)

onMounted(() => {
  void fetchMeta()
  void fetchCollaborators()
})

watch(
  () => currentUser.value,
  () => {
    void fetchCollaborators()
  }
)

const canSaveMeta = computed(() => {
  const prompt = detail.value
  if (!prompt) {
    return false
  }
  if (selectedClassId.value === null) {
    return false
  }
  const originalClassId = prompt.prompt_class.id
  const originalTags = prompt.tags.map((tag) => tag.id).sort((a, b) => a - b)
  const currentTags = [...selectedTagIds.value].sort((a, b) => a - b)
  const tagsChanged =
    originalTags.length !== currentTags.length ||
    originalTags.some((value, index) => value !== currentTags[index])
  const originalAuthor = prompt.author ?? ''
  const currentAuthor = metaAuthor.value.trim()
  const authorChanged = currentAuthor !== originalAuthor
  return selectedClassId.value !== originalClassId || tagsChanged || authorChanged
})

function extractMetaError(error: unknown): string {
  if (error && typeof error === 'object' && 'payload' in error) {
    const httpError = error as { status?: number; payload?: unknown }
    const payload = httpError.payload
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
    if (httpError.status === 404) {
      return t('promptDetail.messages.metaNotFound')
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return t('promptDetail.messages.metaLoadFailed')
}

function extractShareError(error: unknown): string {
  if (error && typeof error === 'object' && 'payload' in error) {
    const payload = (error as { payload?: unknown }).payload
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return t('promptDetail.share.loadFailed')
}

function extractImplementationError(error: unknown): string {
  if (error && typeof error === 'object' && 'payload' in error) {
    const payload = (error as { payload?: unknown }).payload
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return t('promptDetail.implementation.loadFailed')
}

async function fetchMeta() {
  isMetaLoading.value = true
  metaError.value = null
  try {
    const [classes, tagResponse] = await Promise.all([
      listPromptClasses(),
      listPromptTags()
    ])
    promptClasses.value = classes
    promptTags.value = tagResponse.items
  } catch (error) {
    metaError.value = extractMetaError(error)
  } finally {
    isMetaLoading.value = false
  }
}

async function fetchShareUserOptions() {
  const user = currentUser.value
  if (!user) {
    shareUserOptions.value = []
    return
  }

  shareUserLoading.value = true
  try {
    if (user.is_superuser) {
      const users = await listUsers({ limit: 200 })
      shareUserOptions.value = users
    } else {
      shareUserOptions.value = [user]
    }
  } catch (error) {
    void error
    shareUserOptions.value = user ? [user] : []
  } finally {
    shareUserLoading.value = false
  }
}

async function fetchCollaborators() {
  const promptId = currentId.value
  const prompt = detail.value

  if (!promptId || !prompt || !canManageSharing.value) {
    collaborators.value = []
    shareError.value = null
    return
  }

  collaboratorsLoading.value = true
  shareError.value = null
  try {
    const items = await listPromptCollaborators(promptId)
    collaborators.value = items
  } catch (error) {
    shareError.value = extractShareError(error)
  } finally {
    collaboratorsLoading.value = false
  }
}

async function fetchImplementationLogs() {
  const promptId = currentId.value
  if (!promptId) {
    implementationLogs.value = []
    implementationError.value = null
    return
  }

  implementationLoading.value = true
  implementationError.value = null
  try {
    const records = await listPromptImplementations(promptId)
    implementationLogs.value = records
  } catch (error) {
    implementationError.value = extractImplementationError(error)
  } finally {
    implementationLoading.value = false
  }
}

async function handleShare() {
  if (shareLoading.value) {
    return
  }
  const promptId = currentId.value
  if (!promptId || !canManageSharing.value) {
    return
  }

  const username = shareForm.username.trim()
  if (!username) {
    ElMessage.warning(t('promptDetail.share.validation.usernameRequired'))
    return
  }

  shareLoading.value = true
  try {
    await sharePrompt(promptId, {
      username,
      role: shareForm.role
    })
    ElMessage.success(t('promptDetail.share.shareSuccess'))
    shareDialogVisible.value = false
    await fetchCollaborators()
  } catch (error) {
    const message = extractShareError(error)
    ElMessage.error(message)
  } finally {
    shareLoading.value = false
  }
}

async function handleRevokeCollaborator(target: PromptCollaborator) {
  if (revokeLoadingId.value !== null) {
    return
  }
  const promptId = currentId.value
  if (!promptId || !canManageSharing.value) {
    return
  }

  revokeLoadingId.value = target.user_id
  try {
    await revokePromptShare(promptId, target.user_id)
    ElMessage.success(t('promptDetail.share.revokeSuccess', { name: target.username }))
    collaborators.value = collaborators.value.filter((item) => item.user_id !== target.user_id)
  } catch (error) {
    const message = extractShareError(error)
    ElMessage.error(message)
  } finally {
    revokeLoadingId.value = null
  }
}

async function handleSaveImplementation() {
  if (implementationSaving.value) {
    return
  }

  const promptId = currentId.value
  const content = implementationContent.value.trim()

  if (!promptId) {
    return
  }

  if (!content) {
    ElMessage.warning(t('promptDetail.implementation.validation.contentRequired'))
    return
  }

  implementationSaving.value = true
  implementationError.value = null
  try {
    const record = await createPromptImplementation(promptId, { content })
    implementationContent.value = ''
    implementationLogs.value = [record, ...implementationLogs.value]
    ElMessage.success(t('promptDetail.implementation.saveSuccess'))
  } catch (error) {
    const message = extractImplementationError(error)
    implementationError.value = message
    ElMessage.error(message)
  } finally {
    implementationSaving.value = false
  }
}
function resetMetaSelections() {
  const prompt = detail.value
  if (!prompt) {
    selectedClassId.value = null
    selectedTagIds.value = []
    metaAuthor.value = ''
    return
  }
  selectedClassId.value = prompt.prompt_class.id
  selectedTagIds.value = prompt.tags.map((tag) => tag.id)
  metaAuthor.value = prompt.author ?? ''
}

async function handleSaveMeta() {
  const prompt = detail.value
  if (!prompt) {
    return
  }
  if (selectedClassId.value === null) {
    ElMessage.warning(t('promptDetail.messages.classRequired'))
    return
  }
  if (!canSaveMeta.value) {
    ElMessage.info(t('promptDetail.messages.noChange'))
    return
  }
  isMetaSaving.value = true
  try {
    const payload: Record<string, unknown> = {
      class_id: selectedClassId.value,
      tag_ids: selectedTagIds.value
    }
    const originalAuthor = prompt.author ?? ''
    const currentAuthor = metaAuthor.value.trim()
    if (currentAuthor !== originalAuthor) {
      payload.author = currentAuthor || null
    }

    await updatePrompt(prompt.id, payload)
    ElMessage.success(t('promptDetail.messages.updateSuccess'))
    closeMetaDialog()
    await refreshDetail()
    await fetchMeta()
  } catch (error) {
    ElMessage.error(extractMetaError(error))
  } finally {
    isMetaSaving.value = false
  }
}

function openMetaDialog() {
  metaDialogVisible.value = true
  resetMetaSelections()
  void fetchShareUserOptions()
}

function closeMetaDialog() {
  metaDialogVisible.value = false
}

function openShareDialog() {
  shareForm.username = ''
  shareForm.role = 'viewer'
  shareDialogVisible.value = true
  void fetchShareUserOptions()
}

const dateTimeFormatter = computed(
  () =>
    new Intl.DateTimeFormat(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
)
function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return dateTimeFormatter.value.format(date)
}

function summarizeContent(content: string) {
  const normalized = content.replace(/\s+/g, ' ').trim()
  if (!normalized) {
    return t('promptDetail.messages.contentEmpty')
  }
  return normalized.length > 80 ? `${normalized.slice(0, 80)}…` : normalized
}

async function handleCopyPrompt() {
  const content = selectedVersion.value?.content
  if (!content) {
    ElMessage.warning(t('promptDetail.content.copyEmpty'))
    return
  }
  try {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(content)
    } else {
      legacyCopyToClipboard(content)
    }
    ElMessage.success(t('promptDetail.content.copySuccess'))
  } catch (error) {
    ElMessage.error(t('promptDetail.content.copyFailed'))
  }
}

function legacyCopyToClipboard(text: string) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.top = '0'
  textarea.style.left = '0'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  const succeeded = document.execCommand('copy')
  document.body.removeChild(textarea)
  if (!succeeded) {
    throw new Error('Copy command failed')
  }
}

function handleSelectVersion(id: number) {
  selectedVersionId.value = id
}

function handleViewVersionCompare() {
  if (!currentId.value) return
  router.push({ name: 'prompt-version-compare', params: { id: currentId.value } })
}

function handleCreateVersion() {
  if (!currentId.value) return
  router.push({ name: 'prompt-version-create', params: { id: currentId.value } })
}
function goHome() {
  router.push({ name: 'prompt-management' })
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-breadcrumb {
  font-size: 13px;
}

.breadcrumb-link {
  cursor: pointer;
  color: inherit;
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.info-title-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-class {
  margin: 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.info-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.info-desc {
  margin: 0;
  color: var(--text-weak-color);
  line-height: 1.6;
}

.info-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.info-descriptions :deep(.el-descriptions__body) {
  font-size: 13px;
}

.info-tags {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.info-tags__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.info-share {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-share__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-share__title {
  font-size: 14px;
  font-weight: 500;
}

.share-alert {
  margin-bottom: 4px;
}

.share-form {
  margin-top: 8px;
}

.share-table :deep(.el-table__cell) {
  font-size: 13px;
}

.info-tags :deep(.el-button.is-link) {
  padding: 0;
}

.meta-form {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-alert {
  margin-bottom: 12px;
}

.meta-empty-tip {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-weak-color);
}

.meta-actions {
  display: flex;
  gap: 8px;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #909399;
}

.content-card {
  display: flex;
  flex-direction: column;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.content-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.content-subtitle {
  font-size: 13px;
  color: var(--text-weak-color);
}

.content-actions {
  display: flex;
  gap: 8px;
}

.content-body {
  flex: 1;
  display: flex;
  gap: 20px;
  align-items: stretch;
  min-height: 320px;
}

.content-main {
  flex: 2;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-main__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-weak-color);
}

.content-main__time {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content-copy-button {
  padding: 0;
}

.content-main__label {
  margin-right: 8px;
}

.content-main__value {
  font-size: 14px;
  color: var(--header-text-color);
}

.content-scroll {
  flex: 1;
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  padding: 16px;
  overflow-y: auto;
  max-height: 460px;
}

.content-text {
  margin: 0;
  white-space: pre-wrap;
  font-family: 'JetBrains Mono', 'Fira Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
}

.content-history {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.history-scroll {
  flex: 1;
  border: 1px solid var(--side-border-color);
  border-radius: 8px;
  background: var(--content-bg-color);
  padding: 12px;
  overflow-y: auto;
  max-height: 460px;
}

.history-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.history-item + .history-item {
  margin-top: 8px;
}

.history-item.is-active,
.history-item:hover {
  background: rgba(64, 158, 255, 0.12);
}

.history-item__meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-weak-color);
}

.history-version {
  font-weight: 600;
  color: var(--header-text-color);
}

.history-preview {
  margin: 0;
  font-size: 13px;
  color: var(--header-text-color);
  line-height: 1.5;
}

.history-date {
  font-size: 12px;
}

.implementation-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.implementation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.implementation-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.implementation-subtitle {
  font-size: 13px;
  color: var(--text-weak-color);
}

.implementation-form {
  margin-top: 8px;
}

.implementation-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.implementation-alert {
  margin-bottom: 8px;
}

.implementation-log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.implementation-log-item {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--side-border-color);
  background: var(--content-bg-color);
}

.implementation-log-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-weak-color);
  margin-bottom: 4px;
}

.implementation-log-content {
  margin: 0;
  font-size: 13px;
  color: var(--header-text-color);
  white-space: pre-wrap;
  line-height: 1.5;
}

.test-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.test-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.test-subtitle {
  font-size: 13px;
  color: var(--text-weak-color);
}

.test-card :deep(.el-table__cell) {
  font-size: 13px;
}

.test-record-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-record-empty-action {
  color: var(--text-weak-color);
}

.test-alert {
  margin-bottom: 12px;
}
</style>
