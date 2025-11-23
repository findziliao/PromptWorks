<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <div class="auth-header">
        <h2>{{ t('auth.title') }}</h2>
        <p class="auth-subtitle">{{ t('auth.subtitle') }}</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        @submit.prevent
      >
        <el-form-item :label="t('auth.fields.username')" prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="t('auth.placeholders.username')"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item :label="t('auth.fields.password')" prop="password">
          <el-input
            v-model="loginForm.password"
            :placeholder="t('auth.placeholders.password')"
            type="password"
            autocomplete="current-password"
            show-password
          />
        </el-form-item>
        <div class="auth-actions">
          <el-button
            type="primary"
            :loading="loginLoading"
            @click="handleLogin"
          >
            {{ t('auth.actions.login') }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../composables/useAuth'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const { isAuthenticated, loadingUser, loadUser, login } = useAuth()

const loginFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: ''
})

const loginLoading = ref(false)

const loginRules: FormRules = {
  username: [
    { required: true, message: t('auth.validation.usernameRequired'), trigger: 'blur' },
    { min: 3, max: 50, message: t('auth.validation.usernameLength'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('auth.validation.passwordRequired'), trigger: 'blur' },
    { min: 6, max: 128, message: t('auth.validation.passwordLength'), trigger: 'blur' }
  ]
}

const redirectPath = computed(() => {
  const raw = route.query.redirect
  if (typeof raw === 'string' && raw.trim()) {
    return raw
  }
  return '/'
})

function redirectAfterLogin() {
  router.replace(redirectPath.value)
}

onMounted(async () => {
  if (!isAuthenticated.value && !loadingUser.value) {
    await loadUser()
  }
  if (isAuthenticated.value) {
    redirectAfterLogin()
  }
})

async function handleLogin() {
  if (loginLoading.value) return
  const form = loginFormRef.value
  if (!form) return

  try {
    await form.validate()
  } catch (error) {
    void error
    return
  }

  loginLoading.value = true
  try {
    await login({
      username: loginForm.username.trim(),
      password: loginForm.password
    })
    redirectAfterLogin()
  } catch (error) {
    void error
  } finally {
    loginLoading.value = false
  }
}

</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-card {
  width: 360px;
}

.auth-header {
  margin-bottom: 16px;
  text-align: center;
}

.auth-header h2 {
  margin: 0 0 4px;
}

.auth-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--text-weak-color);
}

.auth-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
