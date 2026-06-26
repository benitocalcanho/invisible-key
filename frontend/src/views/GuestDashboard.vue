<template>
  <div class="guest-page">
    <!-- Floating sign-out button -->
    <button class="signout-btn" @click="logout">{{ $t('signout') }}</button>
    <p v-if="unlockError" class="unlock-error">{{ unlockError }}</p>
    <div class="door-card">
      <img
        v-if="imageUrl('building_door')"
        class="door-image"
        :src="imageUrl('building_door')"
        :style="imageStyle('building_door')"
        alt=""
      />
      <div class="door-overlay">
        <p class="door-label">{{ $t('building_door') }}</p>
        <button
          class="unlock-btn"
          :class="{ unlocking: active === 'building' }"
          :style="active === 'building' ? `--progress: ${progress}%` : ''"
          :disabled="active !== null || pending !== null"
          @click="unlock('building')"
        >
          {{ active === 'building' ? $t('push_door') : '🔓 ' + $t('unlock_door') }}
        </button>
      </div>
    </div>

    <div class="door-card">
      <img
        v-if="imageUrl('apartment_door')"
        class="door-image"
        :src="imageUrl('apartment_door')"
        :style="imageStyle('apartment_door')"
        alt=""
      />
      <div class="door-overlay">
        <p class="door-label">{{ $t('apartment_door') }}</p>
        <button
          class="unlock-btn"
          :class="{ unlocking: active === 'apartment' }"
          :style="active === 'apartment' ? `--progress: ${progress}%` : ''"
          :disabled="active !== null || pending !== null"
          @click="unlock('apartment')"
        >
          {{ active === 'apartment' ? $t('push_door') : '🔓 ' + $t('unlock_door') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const images = ref({ building_door: null, apartment_door: null })
const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

const DURATION = 5000  // ms — relay pulse duration for all doors
const active = ref(null)   // 'building' | 'apartment' | null
const progress = ref(100)  // 100 → 0 over DURATION ms
const pending = ref(null)
const unlockError = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get('/uploads/images')
    images.value = data
  } catch (_) {}
})

function imageData(key) {
  const value = images.value[key]
  if (!value || typeof value === 'string') {
    return { url: value, position_x: 50, position_y: 50, zoom: 1 }
  }
  return {
    url: value.url,
    position_x: value.position_x ?? 50,
    position_y: value.position_y ?? 50,
    zoom: value.zoom ?? 1,
  }
}

function imageUrl(key) {
  return imageData(key).url
}

function imageStyle(key) {
  const image = imageData(key)
  return {
    objectPosition: `${image.position_x}% ${image.position_y}%`,
    transform: `scale(${image.zoom})`,
    transformOrigin: `${image.position_x}% ${image.position_y}%`,
  }
}

async function unlock(door) {
  if (active.value !== null || pending.value !== null) return
  pending.value = door
  unlockError.value = ''
  const duration = DURATION

  // Fire-and-forget: log button press without blocking the unlock request.
  api.post('/admin/audit/button_press', { button: door }).catch(() => {})

  // Trigger GPIO relay: building -> pin 17, apartment -> pin 27.
  // The success animation starts only after the backend accepts the pulse.
  const pinMap = { building: 17, apartment: 27 }
  const pin = pinMap[door]
  if (!pin) {
    pending.value = null
    return
  }

  try {
    await api.post(`/gpio/pins/${pin}/pulse`, { duration: duration / 1000 })
  } catch (err) {
    unlockError.value = t('unlock_failed_try_again')
    pending.value = null
    setTimeout(() => {
      if (unlockError.value) unlockError.value = ''
    }, 5000)
    return
  }

  pending.value = null
  active.value = door
  progress.value = 100

  const start = performance.now()
  const tick = (now) => {
    const elapsed = now - start
    progress.value = Math.max(0, 100 - (elapsed / duration) * 100)
    if (elapsed < duration) {
      requestAnimationFrame(tick)
    } else {
      active.value = null
      progress.value = 100
    }
  }
  requestAnimationFrame(tick)
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}

// Helper: progress < 90 means red is visible
function progressAttr(door) {
  return active.value === door && progress.value < 90 ? { 'data-progress': '' } : {}
}
</script>

<style scoped>
.guest-page {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%;
  max-width: 430px;
  min-height: 100dvh;   /* fills screen, respects mobile browser chrome */
  height: 100dvh;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  background: #1a1a2e;
}

.signout-btn {
  position: absolute;
  top: 0.9rem;
  right: 1rem;
  z-index: 200;
  background: rgba(0,0,0,0.45);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 20px;
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
  cursor: pointer;
  backdrop-filter: blur(4px);
}

.unlock-error {
  position: absolute;
  top: 3.8rem;
  left: 1rem;
  right: 1rem;
  z-index: 210;
  margin: 0;
  padding: 0.7rem 0.9rem;
  color: #fff;
  background: rgba(165, 42, 42, 0.92);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 700;
  text-align: center;
  box-shadow: 0 4px 18px rgba(0,0,0,0.35);
}


.door-card {
  flex: 1 1 0;
  min-height: 0;
  background-color: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.door-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  will-change: transform;
}

.door-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.2rem;
}

.door-label {
  color: white;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-shadow: 0 2px 8px rgba(0,0,0,0.85);
}

.unlock-btn {
  padding: 1.1rem 3rem;
  font-size: 1.4rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.93);
  color: #0f3460;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  transition: transform 0.1s, box-shadow 0.1s;
  min-width: 200px;
  min-height: 60px;
  touch-action: manipulation;
  /* progress bar lives here — set via --progress custom property */
  background-image: none;
  position: relative;
  overflow: hidden;
}

/* Drain animation: red fills from left, white retreats to the right */
.unlock-btn.unlocking {
  background: linear-gradient(
    to left,
    rgba(255,255,255,0.93) var(--progress, 100%),
    #e74c3c var(--progress, 100%)
  );
  color: #0f3460;
}

.unlock-btn.unlocking[data-progress] {
  color: #fff;
}

.unlock-btn:disabled:not(.unlocking) {
  opacity: 0.5;
  cursor: not-allowed;
}

.unlock-btn:active:not(:disabled) {
  transform: scale(0.96);
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

@media (min-width: 480px) {
  .guest-page {
    box-shadow: 0 0 36px rgba(0, 0, 0, 0.28);
  }
}
</style>
