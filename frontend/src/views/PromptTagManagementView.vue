<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ t('promptTagManagement.headerTitle') }}</h2>
        <p class="page-desc">{{ t('promptTagManagement.headerDescription') }}</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog">
        {{ t('promptTagManagement.newTag') }}
      </el-button>
    </section>

    <el-card class="table-card">
      <template #header>
        <div class="table-card__header">
          <span>{{ t('promptTagManagement.summary', { totalTags, totalPrompts: totalTaggedPrompts }) }}</span>
        </div>
      </template>
      <el-table
        :data="tagRows"
        v-loading="tableLoading"
        border
        stripe
        :empty-text="t('promptTagManagement.empty')"
      >
        <el-table-column :label="t('promptTagManagement.columns.tag')" min-width="200">
          <template #default="{ row }">
            <span class="tag-cell">
              <span class="tag-dot" :style="{ backgroundColor: row.color }" />
              <span>{{ row.name }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="color" :label="t('promptTagManagement.columns.color')" width="140">
          <template #default="{ row }">
            <el-tag :style="{ backgroundColor: row.color, borderColor: row.color }" effect="dark" size="small">
              {{ row.color }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="prompt_count"
          :label="t('promptTagManagement.columns.promptCount')"
          width="140"
          align="center"
        />
        <el-table-column :label="t('promptTagManagement.columns.createdAt')" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('promptTagManagement.columns.updatedAt')" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('promptTagManagement.columns.actions')" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">
              {{ t('common.edit') }}
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              {{ t('promptTagManagement.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? t('promptTagManagement.editDialogTitle') : t('promptTagManagement.dialogTitle')"
      width="520px"
    >
      <el-form :model="tagForm" label-width="100px" class="dialog-form">
        <el-form-item :label="t('promptTagManagement.form.name')">
          <el-input v-model="tagForm.name" :placeholder="t('promptTagManagement.form.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('promptTagManagement.form.color')">
          <el-color-picker v-model="tagForm.color" :show-alpha="false" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('promptTagManagement.footer.cancel') }}</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ t('promptTagManagement.footer.submit') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPromptTag,
  deletePromptTag,
  listPromptTags,
  updatePromptTag,
  type PromptTagStats
} from '../api/promptTag'
import { useI18n } from 'vue-i18n'

const tableLoading = ref(false)
const submitLoading = ref(false)
const promptTags = ref<PromptTagStats[]>([])
const taggedPromptTotal = ref(0)
const { t, locale } = useI18n()

const tagRows = computed(() => {
  return [...promptTags.value].sort((a, b) => {
    if (b.prompt_count !== a.prompt_count) {
      return b.prompt_count - a.prompt_count
    }
    return a.name.localeCompare(b.name, locale.value)
  })
})

const totalTags = computed(() => tagRows.value.length)
const totalTaggedPrompts = computed(() => taggedPromptTotal.value)

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
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateTimeFormatter.value.format(date)
}

const dialogVisible = ref(false)
const tagForm = reactive({
  name: '',
  color: '#409EFF'
})
const isEditMode = ref(false)
const editingTagId = ref<number | null>(null)

async function fetchPromptTags() {
  tableLoading.value = true
  try {
    const data = await listPromptTags()
    promptTags.value = data.items
    taggedPromptTotal.value = data.tagged_prompt_total
  } catch (error) {
    console.error(error)
    ElMessage.error(t('promptTagManagement.messages.loadFailed'))
  } finally {
    tableLoading.value = false
  }
}

function resetTagForm() {
  tagForm.name = ''
  tagForm.color = '#409EFF'
}

function openDialog() {
  isEditMode.value = false
  editingTagId.value = null
  resetTagForm()
  dialogVisible.value = true
}

function openEditDialog(row: PromptTagStats) {
  isEditMode.value = true
  editingTagId.value = row.id
  tagForm.name = row.name
  tagForm.color = row.color
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!tagForm.name.trim()) {
    ElMessage.warning(t('promptTagManagement.messages.nameRequired'))
    return
  }
  submitLoading.value = true
  try {
    if (!isEditMode.value) {
      await createPromptTag({
        name: tagForm.name.trim(),
        color: tagForm.color.toUpperCase()
      })
      ElMessage.success(t('promptTagManagement.messages.createSuccess'))
    } else if (editingTagId.value != null) {
      await updatePromptTag(editingTagId.value, {
        name: tagForm.name.trim(),
        color: tagForm.color.toUpperCase()
      })
      ElMessage.success(t('promptTagManagement.messages.updateSuccess'))
    }
    dialogVisible.value = false
    await fetchPromptTags()
  } catch (error: any) {
    console.error(error)
    const message =
      error?.payload?.detail ??
      (isEditMode.value
        ? t('promptTagManagement.messages.updateFailed')
        : t('promptTagManagement.messages.createFailed'))
    ElMessage.error(message)
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: PromptTagStats) {
  try {
    await ElMessageBox.confirm(
      t('promptTagManagement.messages.deleteConfirmMessage', { name: row.name }),
      t('promptTagManagement.messages.deleteConfirmTitle'),
      {
      type: 'warning',
        confirmButtonText: t('promptTagManagement.messages.confirmDelete'),
        cancelButtonText: t('common.cancel')
      }
    )
  } catch {
    return
  }

  try {
    await deletePromptTag(row.id)
    ElMessage.success(t('promptTagManagement.messages.deleteSuccess'))
    await fetchPromptTags()
  } catch (error: any) {
    if (error?.status === 409) {
      ElMessage.error(t('promptTagManagement.messages.deleteBlocked'))
      return
    }
    console.error(error)
    const message = error?.payload?.detail ?? t('promptTagManagement.messages.deleteFailed')
    ElMessage.error(message)
  }
}

onMounted(() => {
  fetchPromptTags()
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

.table-card__header {
  font-size: 13px;
  color: var(--text-weak-color);
}

.tag-cell {
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

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
