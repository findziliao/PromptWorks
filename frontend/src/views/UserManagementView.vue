<template>
  <div class="page">
    <section class="page-header">
      <div class="page-header__text">
        <h2>{{ t('userManagement.headerTitle') }}</h2>
        <p class="page-desc">{{ t('userManagement.headerDescription') }}</p>
      </div>
    </section>

    <el-result
      v-if="!isAdmin"
      icon="warning"
      :title="t('userManagement.noPermissionTitle')"
      :sub-title="t('userManagement.noPermissionSubtitle')"
    >
      <template #extra>
        <el-button type="primary" @click="goHome">
          {{ t('userManagement.backToHome') }}
        </el-button>
      </template>
    </el-result>

    <template v-else>
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          :placeholder="t('userManagement.searchPlaceholder')"
          clearable
          class="toolbar__search"
          @change="handleSearch"
        />
        <el-button @click="handleSearch">
          {{ t('userManagement.searchButton') }}
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          {{ t('userManagement.createButton') }}
        </el-button>
      </div>

      <el-table
        :data="users"
        border
        size="small"
        v-loading="loading"
      >
        <el-table-column prop="id" :label="t('userManagement.columns.id')" width="80" />
        <el-table-column prop="username" :label="t('userManagement.columns.username')" min-width="160" />
        <el-table-column :label="t('userManagement.columns.role')" width="140">
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'danger' : 'info'" size="small">
              {{ row.is_superuser ? t('userManagement.roles.admin') : t('userManagement.roles.user') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('userManagement.columns.active')" width="140">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :loading="savingId === row.id"
              @change="(value) => handleToggleActive(row, value as boolean)"
            />
          </template>
        </el-table-column>
        <el-table-column :label="t('userManagement.columns.admin')" width="160">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_superuser"
              :disabled="row.id === currentUser?.id"
              :loading="savingId === row.id"
              @change="(value) => handleToggleAdmin(row, value as boolean)"
            />
          </template>
        </el-table-column>
        <el-table-column :label="t('userManagement.columns.createdAt')" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('userManagement.columns.updatedAt')" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
      </el-table>

      <el-dialog
        v-model="createDialogVisible"
        :title="t('userManagement.createDialogTitle')"
        width="420px"
      >
        <el-form label-position="top" class="create-form">
          <el-form-item :label="t('userManagement.form.username')">
            <el-input
              v-model="createForm.username"
              :placeholder="t('userManagement.form.usernamePlaceholder')"
            />
          </el-form-item>
          <el-form-item :label="t('userManagement.form.password')">
            <el-input
              v-model="createForm.password"
              :placeholder="t('userManagement.form.passwordPlaceholder')"
              type="password"
              show-password
            />
          </el-form-item>
          <el-form-item :label="t('userManagement.form.confirmPassword')">
            <el-input
              v-model="createForm.confirmPassword"
              :placeholder="t('userManagement.form.confirmPasswordPlaceholder')"
              type="password"
              show-password
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="createDialogVisible = false" :disabled="createLoading">
            {{ t('common.cancel') }}
          </el-button>
          <el-button type="primary" :loading="createLoading" @click="handleCreateUser">
            {{ t('userManagement.createConfirm') }}
          </el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { listUsers, updateUser } from '../api/user'
import { signup as signupApi } from '../api/authApi'
import type { User } from '../types/user'
import { useAuth } from '../composables/useAuth'

const { t, locale } = useI18n()
const router = useRouter()
const { currentUser } = useAuth()

const users = ref<User[]>([])
const loading = ref(false)
const savingId = ref<number | null>(null)
const searchKeyword = ref('')

const createDialogVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const isAdmin = computed(() => currentUser.value?.is_superuser === true)

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
  if (Number.isNaN(date.getTime())) return value
  return dateTimeFormatter.value.format(date)
}

function extractErrorMessage(error: unknown): string {
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
  return t('userManagement.messages.loadFailed')
}

async function fetchUsers() {
  if (!isAdmin.value) return
  loading.value = true
  try {
    const data = await listUsers({ q: searchKeyword.value || undefined, limit: 200 })
    users.value = data
  } catch (error) {
    ElMessage.error(extractErrorMessage(error))
    users.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  void fetchUsers()
}

function openCreateDialog() {
  createForm.username = ''
  createForm.password = ''
  createForm.confirmPassword = ''
  createDialogVisible.value = true
}

async function handleToggleAdmin(target: User, value: boolean) {
  if (!isAdmin.value) return
  const original = target.is_superuser
  if (original === value) return

  savingId.value = target.id
  try {
    const updated = await updateUser(target.id, { is_superuser: value })
    target.is_superuser = updated.is_superuser
    target.is_active = updated.is_active
    ElMessage.success(t('userManagement.messages.updateSuccess'))
  } catch (error) {
    ElMessage.error(extractErrorMessage(error))
    target.is_superuser = original
  } finally {
    savingId.value = null
  }
}

async function handleToggleActive(target: User, value: boolean) {
  if (!isAdmin.value) return
  const original = target.is_active
  if (original === value) return

  savingId.value = target.id
  try {
    const updated = await updateUser(target.id, { is_active: value })
    target.is_active = updated.is_active
    ElMessage.success(t('userManagement.messages.updateSuccess'))
  } catch (error) {
    ElMessage.error(extractErrorMessage(error))
    target.is_active = original
  } finally {
    savingId.value = null
  }
}

async function handleCreateUser() {
  if (!isAdmin.value) return
  const username = createForm.username.trim()
  if (!username) {
    ElMessage.warning(t('userManagement.messages.usernameRequired'))
    return
  }
  if (!createForm.password || createForm.password.length < 6) {
    ElMessage.warning(t('userManagement.messages.passwordInvalid'))
    return
  }
  if (createForm.password !== createForm.confirmPassword) {
    ElMessage.warning(t('userManagement.messages.confirmPasswordMismatch'))
    return
  }

  createLoading.value = true
  try {
    await signupApi({ username, password: createForm.password })
    ElMessage.success(t('userManagement.messages.createSuccess'))
    createDialogVisible.value = false
    await fetchUsers()
  } catch (error) {
    ElMessage.error(extractErrorMessage(error))
  } finally {
    createLoading.value = false
  }
}

function goHome() {
  router.push({ name: 'prompt-management' })
}

onMounted(() => {
  void fetchUsers()
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar__search {
  max-width: 260px;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
