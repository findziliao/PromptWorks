<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ t('promptManagement.headerTitle') }}</h2>
        <p class="page-desc">{{ t('promptManagement.headerDescription') }}</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        {{ t('promptManagement.createPrompt') }}
      </el-button>
    </section>

    <div class="page-filters">
      <el-tabs v-model="activeClassKey" type="card" class="class-tabs">
        <el-tab-pane :label="t('promptManagement.allClasses')" name="all" />
        <el-tab-pane
          v-for="item in classOptions"
          :key="item.id"
          :label="item.name"
          :name="String(item.id)"
        />
      </el-tabs>

      <div class="filter-row">
        <el-input
          v-model="searchKeyword"
          :placeholder="t('promptManagement.searchPlaceholder')"
          clearable
          class="filter-item search-input"
          :prefix-icon="Search"
        />
        <el-select
          v-model="selectedTagIds"
          multiple
          collapse-tags
          collapse-tags-tooltip
          class="filter-item tag-select"
          :placeholder="t('promptManagement.tagPlaceholder')"
          clearable
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
        <el-select v-model="sortKey" class="filter-item sort-select" :placeholder="t('promptManagement.sortPlaceholder')">
          <el-option :label="t('promptManagement.sortDefault')" value="default" />
          <el-option :label="t('promptManagement.sortCreatedAt')" value="created_at" />
          <el-option :label="t('promptManagement.sortUpdatedAt')" value="updated_at" />
          <el-option :label="t('promptManagement.sortAuthor')" value="author" />
        </el-select>
        <el-button
          class="view-toggle"
          text
          circle
          @click="toggleViewMode"
        >
          <el-icon>
            <component :is="viewMode === 'list' ? Grid : Menu" />
          </el-icon>
        </el-button>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      show-icon
      class="data-alert"
    />

    <el-skeleton v-else-if="isLoading" animated :rows="6" />

    <template v-else>
      <template v-if="filteredPrompts.length">
        <el-table
          v-if="viewMode === 'list'"
          :data="filteredPrompts"
          border
          size="small"
          class="prompt-table"
          @row-click="handleRowClick"
        >
          <el-table-column :label="t('promptManagement.form.title')" min-width="220">
            <template #default="{ row }">
              <div class="table-title-cell">
                <div class="table-title-main">{{ row.name }}</div>
                <div class="table-title-sub">{{ row.prompt_class?.name }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="t('promptManagement.currentVersion')" width="140">
            <template #default="{ row }">
              <el-tag type="success" round size="small">
                {{ row.current_version?.version ?? t('common.notEnabled') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('promptManagement.author')" width="140">
            <template #default="{ row }">
              {{ row.author ?? t('common.notSet') }}
            </template>
          </el-table-column>
          <el-table-column :label="t('promptManagement.form.tags')" min-width="200">
            <template #default="{ row }">
              <div class="table-tags">
                <el-tag
                  v-for="tag in row.tags"
                  :key="tag.id"
                  size="small"
                  effect="dark"
                  :style="{ backgroundColor: tag.color, borderColor: tag.color }"
                >
                  {{ tag.name }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="t('promptManagement.createdAt')" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('promptManagement.updatedAt')" width="180">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('promptClassManagement.columns.actions')" width="140" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                @click.stop="goDetail(row.id)"
              >
                {{ t('common.view') }}
              </el-button>
              <el-popconfirm
                :title="t('promptManagement.confirmDelete', { name: row.name })"
                :confirm-button-text="t('promptManagement.delete')"
                :cancel-button-text="t('promptManagement.cancel')"
                icon=""
                @confirm="() => handleDeletePrompt(row)"
              >
                <template #reference>
                  <el-button
                    link
                    type="danger"
                    size="small"
                    :loading="isDeleting(row.id)"
                    @click.stop
                  >
                    {{ t('promptManagement.delete') }}
                  </el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div v-else class="card-grid">
          <div v-for="prompt in filteredPrompts" :key="prompt.id" class="card-grid__item">
            <el-card class="prompt-card" shadow="hover" @click="goDetail(prompt.id)">
              <div class="prompt-card__header">
                <div>
                  <p class="prompt-class">{{ prompt.prompt_class.name }}</p>
                  <h3 class="prompt-title">{{ prompt.name }}</h3>
                </div>
                <el-tag type="success" round size="small">
                  {{ t('promptManagement.currentVersion') }}
                  {{ prompt.current_version?.version ?? t('common.notEnabled') }}
                </el-tag>
              </div>
              <p class="prompt-desc">{{ prompt.description ?? t('common.descriptionNone') }}</p>
              <div class="prompt-meta">
                <div class="meta-item">
                  <span class="meta-label">{{ t('promptManagement.author') }}</span>
                  <span>{{ prompt.author ?? t('common.notSet') }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">{{ t('promptManagement.createdAt') }}</span>
                  <span>{{ formatDate(prompt.created_at) }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">{{ t('promptManagement.updatedAt') }}</span>
                  <span>{{ formatDate(prompt.updated_at) }}</span>
                </div>
              </div>
              <div class="prompt-tags">
                <div class="prompt-tags__list">
                  <el-tag
                    v-for="tag in prompt.tags"
                    :key="tag.id"
                    size="small"
                    effect="dark"
                    :style="{ backgroundColor: tag.color, borderColor: tag.color }"
                  >
                    {{ tag.name }}
                  </el-tag>
                </div>
                <el-popconfirm
                  :title="t('promptManagement.confirmDelete', { name: prompt.name })"
                  :confirm-button-text="t('promptManagement.delete')"
                  :cancel-button-text="t('promptManagement.cancel')"
                  icon=""
                  @confirm="() => handleDeletePrompt(prompt)"
                >
                  <template #reference>
                    <el-button
                      type="danger"
                      text
                      size="small"
                      class="card-delete"
                      :loading="isDeleting(prompt.id)"
                      @click.stop
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </el-card>
          </div>
        </div>
      </template>
      <el-empty v-else :description="t('promptManagement.emptyDescription')" />
    </template>

    <el-dialog v-model="createDialogVisible" :title="t('promptManagement.dialogTitle')" width="900px">
      <el-alert
        v-if="!classOptions.length"
        :title="t('promptManagement.dialogAlert')"
        type="warning"
        show-icon
        class="dialog-alert"
      />
      <div class="dialog-body">
        <el-form :model="promptForm" label-width="100px" class="dialog-form">
          <el-form-item :label="t('promptManagement.form.title')">
            <el-input v-model="promptForm.name" :placeholder="t('promptManagement.form.titlePlaceholder')" />
          </el-form-item>
          <el-form-item :label="t('promptManagement.form.author')">
            <el-input v-model="promptForm.author" :placeholder="t('promptManagement.form.authorPlaceholder')" />
          </el-form-item>
          <el-form-item :label="t('promptManagement.form.description')">
            <el-input
              v-model="promptForm.description"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 4 }"
              :placeholder="t('promptManagement.form.descriptionPlaceholder')"
            />
          </el-form-item>
          <el-form-item :label="t('promptManagement.form.class')">
            <el-select v-model="promptForm.classId" :placeholder="t('promptManagement.form.classPlaceholder')">
              <el-option
                v-for="item in classOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('promptManagement.form.tags')">
            <el-select
              v-model="promptForm.tagIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              :placeholder="t('promptManagement.form.tagsPlaceholder')"
            >
              <el-option
                v-for="tag in tagOptions"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('promptManagement.form.version')">
            <el-input v-model="promptForm.version" :placeholder="t('promptManagement.form.versionPlaceholder')" />
          </el-form-item>
          <el-form-item :label="t('promptManagement.form.content')">
            <el-input
              v-model="promptForm.content"
              type="textarea"
              :autosize="{ minRows: 6, maxRows: 12 }"
              :placeholder="t('promptManagement.form.contentPlaceholder')"
            />
          </el-form-item>
        </el-form>

        <div class="ai-panel">
          <h4 class="ai-panel__title">{{ t('promptManagement.aiHelper.panelTitle') }}</h4>
          <p class="ai-panel__hint">
            {{ t('promptManagement.aiHelper.description') }}
          </p>
          <el-form label-position="top" class="ai-dialog-form">
            <el-form-item :label="t('promptManagement.aiHelper.modelLabel')">
              <el-cascader
                v-model="aiModelPath"
                :options="aiModelOptions"
                :props="aiCascaderProps"
                :show-all-levels="false"
                clearable
                filterable
                :placeholder="t('promptManagement.aiHelper.modelPlaceholder')"
                :disabled="aiLoading"
              />
            </el-form-item>
            <el-form-item :label="t('promptManagement.aiHelper.promptLabel')">
              <el-input
                v-model="aiDescription"
                type="textarea"
                :autosize="{ minRows: 5, maxRows: 8 }"
                :placeholder="t('promptManagement.aiHelper.promptPlaceholder')"
              />
            </el-form-item>
            <div class="ai-panel__actions">
              <el-button @click="handleAiReset" :disabled="aiLoading">
                {{ t('common.cancel') }}
              </el-button>
              <el-button type="primary" :loading="aiLoading" @click="handleAiGenerate">
                {{ t('promptManagement.aiHelper.generate') }}
              </el-button>
            </div>
          </el-form>
        </div>
      </div>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ t('promptManagement.footer.cancel') }}</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="handleCreatePrompt">
          {{ t('promptManagement.footer.submit') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Grid, Menu, Plus, Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listPrompts, createPrompt, deletePrompt, type HttpError } from '../api/prompt'
import { listPromptClasses, type PromptClassStats } from '../api/promptClass'
import { listPromptTags, type PromptTagStats } from '../api/promptTag'
import { listLLMProviders } from '../api/llmProvider'
import { invokeQuickTest, type QuickTestStreamPayload } from '../api/quickTest'
import type { ChatMessagePayload, LLMProvider } from '../types/llm'
import type { Prompt } from '../types/prompt'
import { useI18n } from 'vue-i18n'

type SortKey = 'default' | 'created_at' | 'updated_at' | 'author'

interface PromptFormState {
  name: string
  description: string
  author: string
  classId: number | null
  tagIds: number[]
  version: string
  content: string
}

const router = useRouter()
const { t, locale } = useI18n()
const prompts = ref<Prompt[]>([])
const promptClasses = ref<PromptClassStats[]>([])
const promptTags = ref<PromptTagStats[]>([])
const isLoading = ref(false)
const promptError = ref<string | null>(null)
const collectionError = ref<string | null>(null)
const loadError = computed(() => promptError.value ?? collectionError.value)
const isSubmitting = ref(false)
const deletingIds = ref<number[]>([])

const activeClassKey = ref('all')
const searchKeyword = ref('')
const selectedTagIds = ref<number[]>([])
const sortKey = ref<SortKey>('default')
const viewMode = ref<'list' | 'card'>('list')

const aiDescription = ref('')
const aiLoading = ref(false)
const aiProviders = ref<LLMProvider[]>([])
const aiModelOptions = ref<{ value: number | string; label: string; children?: { value: number | string; label: string }[] }[]>([])
const aiModelPath = ref<(number | string)[]>([])
const aiCascaderProps = reactive({
  expandTrigger: 'hover' as const,
  emitPath: true
})

const classOptions = computed(() => {
  return promptClasses.value
    .map((item) => ({ id: item.id, name: item.name }))
    .sort((a, b) => a.name.localeCompare(b.name, locale.value))
})

const tagOptions = computed(() => {
  return promptTags.value
    .map((tag) => ({ id: tag.id, name: tag.name, color: tag.color }))
    .sort((a, b) => a.name.localeCompare(b.name, locale.value))
})

const dateFormatter = computed(
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

function formatDate(value: string | null | undefined) {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateFormatter.value.format(date)
}

function matchKeyword(keyword: string, prompt: Prompt) {
  if (!keyword.trim()) return true
  const target = keyword.trim().toLowerCase()
  const fields: (string | null | undefined)[] = [
    prompt.name,
    prompt.author,
    prompt.description,
    prompt.current_version?.content,
    prompt.versions.map((item) => item.content).join('\n')
  ]
  return fields.some((field) => field?.toLowerCase().includes(target))
}

function sortPrompts(list: Prompt[]) {
  const sorted = [...list]
  switch (sortKey.value) {
    case 'created_at':
      sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      break
    case 'updated_at':
      sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      break
    case 'author':
      sorted.sort((a, b) => {
        const authorA = a.author ?? ''
        const authorB = b.author ?? ''
        const cmp = authorA.localeCompare(authorB, locale.value)
        if (cmp !== 0) return cmp
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      })
      break
    default:
      sorted.sort((a, b) => {
        const diff = new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        if (diff !== 0) return diff
        return a.name.localeCompare(b.name, locale.value)
      })
  }
  return sorted
}

const filteredPrompts = computed(() => {
  const keyword = searchKeyword.value
  const activeClass = activeClassKey.value
  const tagIds = selectedTagIds.value

  const list = prompts.value.filter((prompt) => {
    if (activeClass !== 'all' && String(prompt.prompt_class.id) !== activeClass) {
      return false
    }
    if (!matchKeyword(keyword, prompt)) {
      return false
    }
    if (tagIds.length) {
      const tagSet = new Set(prompt.tags.map((tag) => tag.id))
      if (!tagIds.every((tagId) => tagSet.has(tagId))) {
        return false
      }
    }
    return true
  })

  return sortPrompts(list)
})

const createDialogVisible = ref(false)
const promptForm = reactive<PromptFormState>({
  name: '',
  description: '',
  author: '',
  classId: null,
  tagIds: [],
  version: '',
  content: ''
})

function resetPromptForm() {
  promptForm.name = ''
  promptForm.description = ''
  promptForm.author = ''
  promptForm.classId = classOptions.value[0]?.id ?? null
  promptForm.tagIds = []
  promptForm.version = ''
  promptForm.content = ''
}

function openCreateDialog() {
  resetPromptForm()
  createDialogVisible.value = true
}
async function fetchAiProviders() {
  try {
    const providers = await listLLMProviders()
    aiProviders.value = providers.filter((item) => item.models && item.models.length > 0)
    aiModelOptions.value = aiProviders.value.map((provider) => ({
      value: provider.id,
      label: provider.provider_name,
      children: provider.models.map((model) => ({
        value: model.name,
        label: model.name
      }))
    }))
    if (!aiModelPath.value.length && aiProviders.value.length && aiProviders.value[0].models.length) {
      const firstProvider = aiProviders.value[0]
      const firstModel = firstProvider.models[0]
      aiModelPath.value = [firstProvider.id, firstModel.name]
    }
  } catch (error) {
    void error
    ElMessage.error(t('promptManagement.aiHelper.loadProviderFailed'))
  }
}

function toggleViewMode() {
  viewMode.value = viewMode.value === 'list' ? 'card' : 'list'
}

function isDeleting(id: number) {
  return deletingIds.value.includes(id)
}

function handleCreatePrompt() {
  if (!promptForm.name.trim() || !promptForm.version.trim() || !promptForm.content.trim()) {
    ElMessage.warning(t('promptManagement.messages.missingRequired'))
    return
  }
  if (!promptForm.classId) {
    ElMessage.warning(t('promptManagement.messages.selectClass'))
    return
  }
  if (isSubmitting.value) {
    return
  }

  if (!promptForm.classId) {
    ElMessage.warning(t('promptManagement.messages.selectClass'))
    return
  }

  isSubmitting.value = true
  const payload = {
    name: promptForm.name.trim(),
    description: promptForm.description.trim() || null,
    author: promptForm.author.trim() || null,
    class_id: promptForm.classId,
    version: promptForm.version.trim(),
    content: promptForm.content,
    tag_ids: promptForm.tagIds.length ? promptForm.tagIds : []
  }

  createPrompt(payload)
    .then(async () => {
      ElMessage.success(t('promptManagement.messages.createSuccess'))
      createDialogVisible.value = false
      await Promise.all([fetchPrompts(), fetchCollections()])
    })
    .catch((error) => {
      ElMessage.error(extractErrorMessage(error, t('promptManagement.messages.createFailed')))
    })
    .finally(() => {
      isSubmitting.value = false
    })
}

function resolveAiModelSelection() {
  if (aiModelPath.value.length !== 2) {
    return null
  }
  const [providerIdRaw, modelNameRaw] = aiModelPath.value
  const providerId = Number(providerIdRaw)
  if (Number.isNaN(providerId)) return null
  const provider = aiProviders.value.find((item) => item.id === providerId)
  if (!provider) return null
  const model = provider.models.find((item) => item.name === String(modelNameRaw))
  if (!model) return null
  return { provider, model }
}

function applyAiSuggestion(raw: unknown) {
  if (!raw || typeof raw !== 'object') return
  const suggestion = raw as Record<string, unknown>
  const title = suggestion.title
  const description = suggestion.description
  const content = suggestion.content
  const author = suggestion.author
  const version = suggestion.version
  const tags = suggestion.tags

  if (typeof title === 'string' && title.trim()) {
    promptForm.name = title.trim()
  }
  if (typeof description === 'string' && description.trim()) {
    promptForm.description = description.trim()
  }
  if (typeof content === 'string' && content.trim()) {
    promptForm.content = content
  }
  if (typeof author === 'string' && author.trim()) {
    promptForm.author = author.trim()
  }
  if (typeof version === 'string' && version.trim()) {
    promptForm.version = version.trim()
  }

  if (Array.isArray(tags) && tags.length && tagOptions.value.length) {
    const nameToId = new Map<string, number>()
    tagOptions.value.forEach((tag) => {
      nameToId.set(tag.name.toLowerCase(), tag.id)
    })
    const selected: number[] = []
    for (const item of tags) {
      if (typeof item !== 'string') continue
      const id = nameToId.get(item.toLowerCase())
      if (id != null && !selected.includes(id)) {
        selected.push(id)
      }
    }
    if (selected.length) {
      promptForm.tagIds = selected
    }
  }
}

async function handleAiGenerate() {
  const selection = resolveAiModelSelection()
  if (!selection) {
    ElMessage.warning(t('promptManagement.aiHelper.noProviderShort'))
    return
  }
  const description = aiDescription.value.trim()
  if (!description) {
    ElMessage.warning(t('promptManagement.aiHelper.descriptionRequired'))
    return
  }

  const systemPrompt =
    '你是 PromptWorks 平台的提示词设计助手。' +
    '用户会用中文描述一个 Prompt 的用途、目标用户、输入输出等信息。' +
    '请只输出一个 JSON 对象，不要包含任何额外文字或解释。' +
    'JSON 字段为: title(标题字符串), description(简要描述字符串), content(Prompt 具体内容字符串), ' +
    'author(作者或责任人字符串，可为空字符串), version(版本号字符串，建议形如 v1 或 v1.0), ' +
    'tags(字符串数组，每个是一个标签名称)。'

  const messagesPayload: ChatMessagePayload[] = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: description }
  ]

  const payload: QuickTestStreamPayload = {
    providerId: selection.provider.id,
    modelId: selection.model.id,
    modelName: selection.model.name,
    messages: messagesPayload,
    temperature: 0.7,
    parameters: {},
    promptId: null,
    promptVersionId: null,
    persistUsage: false
  }

  aiLoading.value = true
  try {
    const response = (await invokeQuickTest(payload)) as any
    const choices = Array.isArray(response?.choices) ? response.choices : []
    let combined = ''
    for (const choice of choices) {
      if (!choice || typeof choice !== 'object') continue
      const message = (choice as any).message
      if (message && typeof message.content === 'string') {
        combined += message.content
        continue
      }
      const text = (choice as any).text
      if (typeof text === 'string') {
        combined += text
      }
    }
    const jsonText = combined.trim()
    if (!jsonText) {
      ElMessage.error(t('promptManagement.aiHelper.emptyResponse'))
      return
    }
    let parsed: unknown
    try {
      parsed = JSON.parse(jsonText)
    } catch (error) {
      void error
      ElMessage.error(t('promptManagement.aiHelper.parseFailed'))
      return
    }
    applyAiSuggestion(parsed)
    aiDialogVisible.value = false
    ElMessage.success(t('promptManagement.aiHelper.applySuccess'))
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, t('promptManagement.aiHelper.invokeFailed')))
  } finally {
    aiLoading.value = false
  }
}

function handleAiReset() {
  aiDescription.value = ''
}

function goDetail(id: number) {
  router.push({ name: 'prompt-detail', params: { id: String(id) } })
}

function handleRowClick(row: Prompt) {
  if (row && typeof row.id === 'number') {
    goDetail(row.id)
  }
}

async function handleDeletePrompt(target: Prompt) {
  if (isDeleting(target.id)) {
    return
  }
  deletingIds.value = [...deletingIds.value, target.id]
  try {
    await deletePrompt(target.id)
    ElMessage.success(t('promptManagement.messages.deleteSuccess', { name: target.name }))
    await Promise.all([fetchPrompts(), fetchCollections()])
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, t('promptManagement.messages.deleteFailed')))
  } finally {
    deletingIds.value = deletingIds.value.filter((item) => item !== target.id)
  }
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'status' in error) {
    const httpError = error as HttpError
    if (httpError.payload && typeof httpError.payload === 'object' && 'detail' in httpError.payload) {
      const detail = (httpError.payload as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
    }
    if (httpError.status === 404) {
      return t('promptManagement.messages.resourceNotFound')
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

async function fetchPrompts() {
  try {
    const data = await listPrompts({ limit: 200 })
    prompts.value = data
    promptError.value = null
  } catch (error) {
    const message = extractErrorMessage(error, t('promptManagement.messages.loadPromptFailed'))
    promptError.value = message
    ElMessage.error(message)
    prompts.value = []
  }
}

async function fetchCollections() {
  try {
    const [classes, tagResponse] = await Promise.all([
      listPromptClasses(),
      listPromptTags()
    ])
    promptClasses.value = classes
    promptTags.value = tagResponse.items
    collectionError.value = null
  } catch (error) {
    const message = extractErrorMessage(error, t('promptManagement.messages.loadCollectionFailed'))
    collectionError.value = message
    ElMessage.error(message)
    promptClasses.value = []
    promptTags.value = []
  }
}

async function bootstrap() {
  isLoading.value = true
  promptError.value = null
  collectionError.value = null
  await Promise.all([fetchPrompts(), fetchCollections(), fetchAiProviders()])
  isLoading.value = false
}

watch(classOptions, (options) => {
  if (activeClassKey.value !== 'all') {
    const exists = options.some((item) => String(item.id) === activeClassKey.value)
    if (!exists) {
      activeClassKey.value = 'all'
    }
  }
  if (!options.length) {
    promptForm.classId = null
    return
  }
  if (promptForm.classId === null || !options.some((item) => item.id === promptForm.classId)) {
    promptForm.classId = options[0].id
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

onMounted(() => {
  void bootstrap()
})
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-header__text h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-desc {
  margin: 0;
  color: var(--text-weak-color);
  font-size: 14px;
}

.page-filters {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.class-tabs {
  --el-tabs-header-height: 40px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filter-item {
  flex: 1;
  min-width: 200px;
}

.search-input {
  max-width: 320px;
}

.tag-select {
  max-width: 320px;
}

.sort-select {
  width: 180px;
  flex: initial;
}

.view-toggle {
  flex: initial;
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

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  align-items: stretch;
}

.prompt-table {
  margin-top: 8px;
}

.table-title-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.table-title-main {
  font-weight: 600;
}

.table-title-sub {
  font-size: 12px;
  color: var(--text-weak-color);
}

.table-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.data-alert {
  margin-bottom: 12px;
}

.card-grid__item {
  height: 100%;
}

.prompt-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 12px;
  border: 1px solid transparent;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.prompt-card:hover {
  transform: translateY(-4px);
  border-color: #409eff33;
}

.prompt-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.prompt-class {
  margin: 0 0 4px;
  font-size: 13px;
  color: var(--text-weak-color);
}

.prompt-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.prompt-desc {
  margin: 16px 0;
  color: var(--header-text-color);
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
}

.prompt-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: var(--text-weak-color);
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-weight: 500;
  min-width: 64px;
}

.prompt-tags {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.prompt-tags__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.card-delete {
  color: var(--el-color-danger);
  display: flex;
  align-items: center;
  padding: 4px;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialog-alert {
  margin-bottom: 12px;
}
.dialog-body {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  align-items: flex-start;
}

.ai-panel {
  border-left: 1px solid var(--el-border-color-lighter);
  padding-left: 16px;
}

.ai-panel__title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px;
}

.ai-panel__hint {
  font-size: 12px;
  color: var(--text-weak-color);
  margin: 0 0 12px;
}

.ai-dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-panel__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
