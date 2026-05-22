<template>
  <div class="wifi-manager">

    <!-- Current status -->
    <div class="status-bar">
      <span class="dot" :class="status.state === 'connected' ? 'dot-green' : 'dot-grey'"></span>
      <span v-if="status.state === 'connected'">
        {{ $t('wifi_connected_to') }} <strong>{{ status.connection }}</strong> {{ $t('wifi_on_device') }} {{ status.device }}
      </span>
      <span v-else>{{ $t('wifi_not_connected', { state: status.state }) }}</span>
      <button @click="loadStatus" class="btn-sm">{{ $t('doorLog.refresh') }}</button>
    </div>

    <!-- Nearby networks -->
    <div class="section-card">
      <div class="section-head">
        <div>
          <h4>{{ $t('wifi_nearby_networks') }}</h4>
          <p class="hint">{{ $t('wifi_scan_hint') }}</p>
        </div>
        <button @click="scanNetworks" :disabled="scanning" class="btn-sm">
          {{ scanning ? $t('wifi_scanning') : $t('wifi_scan') }}
        </button>
      </div>

      <p v-if="scanError" class="error">{{ scanError }}</p>
      <p v-else-if="scanned.length === 0" class="hint">{{ $t('wifi_no_scan_results') }}</p>
      <ul v-else class="scan-dropdown">
        <li
          v-for="network in scanned"
          :key="`${network.ssid}-${network.security}`"
          :class="{ selected: newSsid === network.ssid }"
          @click="selectNetwork(network.ssid)"
        >
          <span>{{ network.ssid }}</span>
          <span class="meta">{{ network.signal }}% · {{ network.security }}</span>
        </li>
      </ul>
    </div>

    <!-- Saved networks -->
    <div class="section-card">
      <h4>{{ $t('wifi_saved_networks') }}</h4>
      <p v-if="!saved.length" class="hint">{{ $t('wifi_no_saved_networks') }}</p>
      <ul v-else class="saved-list">
        <li v-for="net in saved" :key="net.name" :class="{ active: net.active }">
          <span class="net-name">
            {{ net.name }}
            <span v-if="net.active" class="badge-active">{{ $t('wifi_active') }}</span>
          </span>
          <div class="net-actions">
            <button
              @click="connectSaved(net.name)"
              :disabled="net.active || connecting === net.name"
              class="btn-sm"
            >
              {{ connecting === net.name ? $t('wifi_connecting') : $t('wifi_connect') }}
            </button>
            <button
              @click="deleteSaved(net.name)"
              :disabled="deleting === net.name"
              class="btn-sm btn-danger"
            >
              {{ deleting === net.name ? '…' : $t('remove') }}
            </button>
          </div>
        </li>
      </ul>
      <p v-if="actionError" class="error">{{ actionError }}</p>
    </div>

    <!-- Add / update network -->
    <div class="section-card">
      <h4>{{ $t('wifi_add_update_network') }}</h4>
      <p class="hint">
        {{ $t('wifi_add_update_hint') }}
      </p>

      <div class="field">
        <label>{{ $t('wifi_network_name') }}</label>
        <input v-model="newSsid" :placeholder="$t('wifi_ssid_placeholder')" />
      </div>

      <div class="field">
        <label>{{ $t('password') }}</label>
        <input v-model="newPass" type="text" :placeholder="$t('wifi_password_placeholder')" />
      </div>

      <div class="button-row">
        <button @click="addNetwork" :disabled="adding || connectingNow" class="btn-primary">
          {{ adding ? $t('saving') : $t('wifi_save_credentials') }}
        </button>
        <button @click="connectNow" :disabled="adding || connectingNow" class="btn-secondary">
          {{ connectingNow ? $t('wifi_connecting') : $t('wifi_connect_now') }}
        </button>
      </div>
      <p class="hint action-hint">{{ $t('wifi_connect_interrupt_hint') }}</p>
      <p v-if="addError" class="error">{{ addError }}</p>
      <p v-if="addSuccess" class="success">{{ addSuccess }}</p>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api.js'

const { t } = useI18n()
const status = ref({ state: 'unknown', connection: '', device: '' })
const saved = ref([])
const scanned = ref([])
const newSsid = ref('')
const newPass = ref('')
const adding = ref(false)
const connecting = ref(null)
const deleting = ref(null)
const scanning = ref(false)
const connectingNow = ref(false)
const addError = ref('')
const addSuccess = ref('')
const actionError = ref('')
const scanError = ref('')

onMounted(() => {
  loadStatus()
  loadSaved()
})

async function loadStatus() {
  try {
    const { data } = await api.get('/wifi/admin/status')
    status.value = data
  } catch { /* best effort */ }
}

async function loadSaved() {
  try {
    const { data } = await api.get('/wifi/admin/saved')
    saved.value = data
  } catch { /* best effort */ }
}

async function scanNetworks() {
  scanning.value = true
  scanError.value = ''
  try {
    const { data } = await api.get('/wifi/admin/scan')
    scanned.value = data
  } catch (e) {
    scanError.value = e.response?.data?.error || t('wifi_scan_failed')
    scanned.value = []
  } finally {
    scanning.value = false
  }
}

function selectNetwork(ssid) {
  newSsid.value = ssid
  addError.value = ''
  addSuccess.value = ''
}


async function addNetwork() {
  addError.value = ''
  addSuccess.value = ''
  if (!newSsid.value.trim() || !newPass.value) {
    addError.value = t('wifi_credentials_required')
    return
  }
  adding.value = true
  try {
    await api.post('/wifi/admin/saved', { ssid: newSsid.value.trim(), passphrase: newPass.value })
    addSuccess.value = t('wifi_credentials_saved', { ssid: newSsid.value.trim() })
    newSsid.value = ''
    newPass.value = ''
    await loadSaved()
  } catch (e) {
    addError.value = e.response?.data?.error || t('wifi_save_failed')
  } finally {
    adding.value = false
  }
}

async function connectNow() {
  addError.value = ''
  addSuccess.value = ''
  if (!newSsid.value.trim() || !newPass.value) {
    addError.value = t('wifi_credentials_required')
    return
  }
  connectingNow.value = true
  try {
    const { data } = await api.post('/wifi/connect', { ssid: newSsid.value.trim(), passphrase: newPass.value })
    if (data.status === 'error') {
      throw new Error(data.message || t('wifi_connect_failed'))
    }
    addSuccess.value = t('wifi_connected_success', { ssid: newSsid.value.trim() })
    newSsid.value = ''
    newPass.value = ''
    await loadStatus()
    await loadSaved()
  } catch (e) {
    addError.value = e.response?.data?.error || e.message || t('wifi_connect_failed')
  } finally {
    connectingNow.value = false
  }
}

async function connectSaved(name) {
  connecting.value = name
  actionError.value = ''
  try {
    await api.post(`/wifi/admin/saved/${encodeURIComponent(name)}/connect`)
    await loadStatus()
    await loadSaved()
  } catch (e) {
    actionError.value = e.response?.data?.error || t('wifi_connect_failed')
  } finally {
    connecting.value = null
  }
}

async function deleteSaved(name) {
  deleting.value = name
  actionError.value = ''
  try {
    await api.delete(`/wifi/admin/saved/${encodeURIComponent(name)}`)
    saved.value = saved.value.filter(n => n.name !== name)
  } catch (e) {
    actionError.value = e.response?.data?.error || t('wifi_remove_failed')
  } finally {
    deleting.value = null
  }
}
</script>

<style scoped>
.wifi-manager { max-width: 640px; }

.status-bar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: white;
  border-radius: 10px;
  padding: 0.9rem 1.2rem;
  margin-bottom: 1.2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  font-size: 0.9rem;
}
.dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.dot-green { background: #27ae60; }
.dot-grey  { background: #bbb; }

.section-card {
  background: white;
  border-radius: 10px;
  padding: 1.2rem 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.section-card h4 { margin: 0 0 0.5rem; color: #0f3460; font-size: 1rem; }
.section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
.button-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }

.saved-list { list-style: none; margin: 0 0 0.5rem; padding: 0; }
.saved-list li {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.6rem 0; border-bottom: 1px solid #f0f0f0;
}
.saved-list li:last-child { border-bottom: none; }
.saved-list li.active .net-name { font-weight: 700; }
.net-name { display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; }
.net-actions { display: flex; gap: 0.4rem; }
.badge-active {
  background: #d4edda; color: #155724;
  font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 8px; font-weight: 500;
}

.field { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.9rem; }
.field label { font-size: 0.85rem; font-weight: 600; color: #444; }
.field input {
  padding: 0.5rem 0.7rem; border: 1px solid #ddd;
  border-radius: 6px; font-size: 0.9rem; font-family: monospace;
}
.field input:focus { outline: none; border-color: #0f3460; }

.ssid-row { display: flex; gap: 0.5rem; }
.ssid-row input { flex: 1; }

.scan-dropdown {
  list-style: none; margin: 0; padding: 0;
  border: 1px solid #ddd; border-radius: 6px;
  max-height: 200px; overflow-y: auto;
}
.scan-dropdown li {
  padding: 0.55rem 0.8rem; cursor: pointer; font-size: 0.88rem;
  display: flex; justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
}
.scan-dropdown li:last-child { border-bottom: none; }
.scan-dropdown li:hover, .scan-dropdown li.selected { background: #f5f7fa; }
.scan-dropdown li.selected span:first-child { font-weight: 700; }
.meta { font-size: 0.78rem; color: #888; }

.btn-primary {
  padding: 0.45rem 1rem; background: #0f3460; color: white;
  border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem;
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary {
  padding: 0.45rem 1rem; background: #eef2f7; color: #344054;
  border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem;
}
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-sm {
  padding: 0.3rem 0.7rem; background: #e8ecf0; color: #333;
  border: none; border-radius: 5px; cursor: pointer; font-size: 0.8rem;
}
.btn-sm:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { background: #fde8e8; color: #c0392b; }
.btn-danger:hover { background: #f5c6c6; }

.hint { color: #888; font-size: 0.82rem; margin: 0 0 0.75rem; }
.action-hint { margin-top: 0.5rem; }
.success { color: #27ae60; font-size: 0.88rem; margin: 0.4rem 0 0; }
.error { color: #c0392b; font-size: 0.88rem; margin: 0.4rem 0 0; }
</style>
