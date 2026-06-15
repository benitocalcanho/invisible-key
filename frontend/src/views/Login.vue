<template>
  <div class="login-view">
    <h1>{{ $t('sign_in') }}</h1>
    <p class="safety-notice">{{ $t('unlock_safety_notice') }}</p>
    <form @submit.prevent="handleLogin">
      <div class="field">
          <label for="username">{{ $t('username') }}</label>
        <input id="username" v-model="username" required />
      </div>
      <div class="field">
          <label for="password">{{ $t('password') }}</label>
        <div class="password-control">
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            required
          />
          <button
            type="button"
            class="password-toggle"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            :title="showPassword ? 'Hide password' : 'Show password'"
            @click="showPassword = !showPassword"
          >
            <svg v-if="!showPassword" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg v-else viewBox="0 0 24 24" aria-hidden="true">
              <path d="m3 3 18 18" />
              <path d="M10.6 10.6A2.9 2.9 0 0 0 12 15a3 3 0 0 0 2.4-1.2" />
              <path d="M7.5 7.8C4.3 9.5 2.5 12 2.5 12s3.5 6 9.5 6c1.7 0 3.1-.5 4.4-1.2" />
              <path d="M13.7 6.2C18.7 7 21.5 12 21.5 12a16 16 0 0 1-2.3 2.8" />
            </svg>
          </button>
        </div>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? $t('signing_in') : $t('sign_in') }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const cleanUsername = username.value.trim()
    username.value = cleanUsername
    const user = await authStore.login(cleanUsername, password.value)
    if (user.role === 'admin') {
      router.push('/admin')
    } else if (['cleaner', 'guest', 'master', 'user'].includes(user.role)) {
      router.push('/guest')
    } else {
      router.push('/dashboard')
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.login-card {
  background: white;
  border-radius: 12px;
  padding: 2.5rem;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
h1 { font-size: 1.8rem; margin-bottom: 0.25rem; color: #1a1a2e; }
.subtitle { color: #666; margin-bottom: 1.5rem; }
.field { margin-bottom: 1rem; }
.field label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.3rem; }
.field input {
  width: 100%; padding: 0.65rem 0.8rem; border: 1px solid #ddd;
  border-radius: 6px; font-size: 1rem; transition: border-color 0.2s;
}
.field input:focus { outline: none; border-color: #0f3460; }
.password-control {
  position: relative;
}
.password-control input {
  padding-right: 2.75rem;
}
.password-toggle {
  position: absolute;
  top: 50%;
  right: 0.35rem;
  width: 2.1rem;
  height: 2.1rem;
  padding: 0;
  margin: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #57606f;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transform: translateY(-50%);
  transition: background 0.2s, color 0.2s;
}
.password-toggle:hover,
.password-toggle:focus-visible {
  background: #f0f3f7;
  color: #0f3460;
  outline: none;
}
.password-toggle svg {
  width: 1.25rem;
  height: 1.25rem;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}
.password-toggle svg circle {
  fill: none;
}
button {
  width: 100%; padding: 0.75rem; background: #0f3460; color: white;
  border: none; border-radius: 6px; font-size: 1rem; cursor: pointer;
  margin-top: 0.5rem; transition: background 0.2s;
}
button:hover:not(:disabled) { background: #16213e; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
button.password-toggle:hover:not(:disabled),
button.password-toggle:focus-visible {
  background: #f0f3f7;
  color: #0f3460;
}
.safety-notice {
  background: #fff4e5;
  color: #7a3b00;
  border: 1px solid #ffd7a6;
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  margin: 0.75rem 0 1.25rem;
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.35;
}
.error { color: #e74c3c; font-size: 0.88rem; margin-bottom: 0.5rem; }
</style>
