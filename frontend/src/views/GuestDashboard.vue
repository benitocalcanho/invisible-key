<template>
  <div class="guest-page">
    <!-- Floating sign-out button -->
    <button class="signout-btn" @click="logout">{{ $t('signout') }}</button>
    <div class="safety-banner">{{ $t('unlock_safety_notice') }}</div>

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
          :disabled="active !== null"
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
          :disabled="active !== null"
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
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const images = ref({ building_door: null, apartment_door: null })
const router = useRouter()
const authStore = useAuthStore()

const DURATION = 5000  // ms — relay pulse duration for all doors
const active = ref(null)   // 'building' | 'apartment' | null
const progress = ref(100)  // 100 → 0 over DURATION ms

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
  if (active.value !== null) return
  active.value = door
  progress.value = 100
  const duration = DURATION

  // Fire-and-forget: log button press and trigger GPIO without blocking the UI
  api.post('/admin/audit/button_press', { button: door }).catch(() => {})

  // Trigger GPIO relay: building → pin 17, apartment → pin 27
  const pinMap = { building: 17, apartment: 27 }
  const pin = pinMap[door]
  if (pin) {
    api.post(`/gpio/pins/${pin}/pulse`, { duration: duration / 1000 }).catch(() => {})
  }

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
  height: 100dvh;       /* fills screen, respects mobile browser chrome */
  position: relative;
}

.signout-btn {
  position: fixed;
  top: 0.9rem;
  right: 1rem;
  z-index: 220;
  background: rgba(0,0,0,0.45);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 20px;
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
  cursor: pointer;
  backdrop-filter: blur(4px);
}

.safety-banner {
  position: fixed;
  top: 3.8rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 210;
  width: min(92vw, 560px);
  background: rgba(255, 244, 229, 0.96);
  color: #7a3b00;
  border: 1px solid rgba(255, 215, 166, 0.95);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.3;
  box-shadow: 0 4px 18px rgba(0,0,0,0.22);
}

.door-card {
  flex: 1;
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
</style>
