<template>
  <div class="schem-hdr-wrap">

    <!-- Nagłówek -->
    <div class="schem-hd">
      <span class="schem-title">Widmo wysokości — <em>H<sub>dr</sub></em></span>
      <span class="schem-formula">= Σ [ cc<sub>i</sub>/100 · (h<sub>i</sub>/h<sub>max</sub>)<sup>3</sup> ]</span>
    </div>

    <!-- Ciało: SVG po lewej, panel po prawej -->
    <div class="schem-body">

    <!-- SVG -->
    <svg viewBox="0 0 420 550" xmlns="http://www.w3.org/2000/svg"
         class="schem-svg" style="touch-action:manipulation">

      <!-- ═══ Strefy wysokości (klikalne pasy poziome) ═══
           Oś Y: y=455 (h=0%) do y=55 (h=100%), zakres=400px, 5 stref po 80px -->

      <template v-for="(z, idx) in ZONES" :key="z.i">
        <!-- Pas strefy -->
        <rect
          x="110" :y="55 + idx*80" width="290" height="80"
          :fill="zoneBgFill(z.i, idx)"
          :stroke="isSelected(z.i) ? '#0d47a1' : 'rgba(21,101,192,0.18)'"
          :stroke-width="isSelected(z.i) ? 2 : 0.8"
          rx="2" style="cursor:pointer"
          @click="toggleZone(z.i)"
        />
        <!-- Etykieta strefy (na pasie) -->
        <text
          x="118" :y="95 + idx*80"
          text-anchor="start" dominant-baseline="middle"
          font-size="12" font-weight="700"
          :fill="isSelected(z.i) ? '#0d47a1' : '#78909c'"
          font-family="'Segoe UI',Roboto,sans-serif"
          style="pointer-events:none;user-select:none"
        >Strefa {{ z.i }}</text>
        <text
          x="118" :y="110 + idx*80"
          text-anchor="start" dominant-baseline="middle"
          font-size="10" font-weight="500"
          :fill="isSelected(z.i) ? '#1565C0' : '#90a4ae'"
          font-family="'Segoe UI',Roboto,sans-serif"
          style="pointer-events:none;user-select:none"
        >{{ z.range }}</text>
        <!-- Ptaszek zaznaczenia -->
        <g v-if="isSelected(z.i)" style="pointer-events:none">
          <circle cx="386" :cy="95 + idx*80" r="10" fill="#1565C0"/>
          <text x="386" :y="96 + idx*80"
                text-anchor="middle" dominant-baseline="middle"
                font-size="11" font-weight="700" fill="white"
                style="user-select:none">✓</text>
        </g>
        <!-- Linia podziału -->
        <line v-if="idx < 4"
              x1="110" :y1="135 + idx*80" x2="400" :y2="135 + idx*80"
              stroke="#90caf9" stroke-width="0.7" stroke-dasharray="5,3"/>
      </template>

      <!-- Oś Y -->
      <g stroke="#1565C0" stroke-width="2" fill="#1565C0">
        <line x1="100" y1="460" x2="100" y2="38"/>
        <polygon points="94,50 100,26 106,50" stroke="none"/>
      </g>
      <g fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
         font-size="11" font-weight="600" text-anchor="end" dominant-baseline="middle">
        <line x1="94" y1="455" x2="106" y2="455" stroke="#1565C0" stroke-width="1.5"/>
        <text x="88" y="455">0%</text>
        <line x1="94" y1="375" x2="106" y2="375" stroke="#1565C0" stroke-width="1.5"/>
        <text x="88" y="375">20%</text>
        <line x1="94" y1="295" x2="106" y2="295" stroke="#1565C0" stroke-width="1.5"/>
        <text x="88" y="295">40%</text>
        <line x1="94" y1="215" x2="106" y2="215" stroke="#1565C0" stroke-width="1.5"/>
        <text x="88" y="215">60%</text>
        <line x1="94" y1="135" x2="106" y2="135" stroke="#1565C0" stroke-width="1.5"/>
        <text x="88" y="135">80%</text>
        <line x1="94" y1="55"  x2="106" y2="55"  stroke="#1565C0" stroke-width="1.5"/>
        <text x="88" y="55">100%</text>
      </g>
      <text x="28" y="258" fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
            font-size="13" font-weight="700"
            transform="rotate(-90 28 258)" text-anchor="middle">h_pod / h_max [%]</text>

      <!-- Linia terenu -->
      <line x1="100" y1="460" x2="410" y2="460"
            stroke="#1565C0" stroke-width="1.2" stroke-dasharray="5,4" stroke-opacity="0.5"/>
      <text x="255" y="476" text-anchor="middle" fill="#90a4ae"
            font-family="'Segoe UI',Roboto,sans-serif" font-size="10" font-style="italic"
            style="pointer-events:none">poziom terenu</text>

      <!-- ═══ Podest nożycowy ═══ -->
      <!-- Koła -->
      <circle cx="175" cy="470" r="11" fill="none" stroke="#1565C0" stroke-width="2.8"/>
      <circle cx="285" cy="470" r="11" fill="none" stroke="#1565C0" stroke-width="2.8"/>
      <!-- Rama dolna -->
      <rect x="158" y="454" width="144" height="13" rx="2" fill="none" stroke="#1565C0" stroke-width="2.8"/>
      <!-- Nożyce dolny stopień -->
      <line x1="168" y1="454" x2="290" y2="268" stroke="#1565C0" stroke-width="3.2" stroke-linecap="round"/>
      <line x1="292" y1="454" x2="170" y2="268" stroke="#1565C0" stroke-width="3.2" stroke-linecap="round"/>
      <circle cx="230" cy="361" r="4.5" fill="#1565C0"/>
      <!-- Rama środkowa -->
      <rect x="162" y="260" width="136" height="11" rx="2" fill="none" stroke="#1565C0" stroke-width="2.3" stroke-opacity="0.7"/>
      <!-- Nożyce górny stopień -->
      <line x1="172" y1="260" x2="282" y2="78" stroke="#1565C0" stroke-width="3.2" stroke-linecap="round"/>
      <line x1="288" y1="260" x2="178" y2="78" stroke="#1565C0" stroke-width="3.2" stroke-linecap="round"/>
      <circle cx="230" cy="169" r="4.5" fill="#1565C0"/>
      <!-- Platforma górna -->
      <rect x="153" y="64" width="154" height="13" rx="2" fill="rgba(21,101,192,0.12)" stroke="#1565C0" stroke-width="2.8"/>
      <!-- Barierka -->
      <line x1="160" y1="64" x2="160" y2="36" stroke="#1565C0" stroke-width="2.3"/>
      <line x1="300" y1="64" x2="300" y2="36" stroke="#1565C0" stroke-width="2.3"/>
      <line x1="160" y1="36" x2="300" y2="36" stroke="#1565C0" stroke-width="2.3"/>
      <line x1="160" y1="50" x2="300" y2="50" stroke="#1565C0" stroke-width="1.6" stroke-opacity="0.5"/>
      <!-- Sylwetka osoby -->
      <circle cx="230" cy="28" r="8" fill="none" stroke="#1565C0" stroke-width="2"/>
      <line x1="230" y1="36" x2="230" y2="58" stroke="#1565C0" stroke-width="2"/>
      <line x1="215" y1="46" x2="245" y2="46" stroke="#1565C0" stroke-width="2"/>
      <line x1="230" y1="58" x2="220" y2="72" stroke="#1565C0" stroke-width="2"/>
      <line x1="230" y1="58" x2="240" y2="72" stroke="#1565C0" stroke-width="2"/>

      <!-- Strzałka h_max -->
      <line x1="330" y1="64" x2="330" y2="455" stroke="#1565C0" stroke-width="1.3"
            stroke-dasharray="3,3" stroke-opacity="0.45"/>
      <polygon points="324,72 330,54 336,72" fill="#1565C0" opacity="0.5" stroke="none"/>
      <polygon points="324,447 330,465 336,447" fill="#1565C0" opacity="0.5" stroke="none"/>
      <text x="344" y="260" fill="#1565C0" font-size="11" font-weight="700"
            font-family="'Segoe UI',Roboto,sans-serif"
            transform="rotate(90 344 260)" text-anchor="middle" dominant-baseline="middle">h_max</text>


    </svg>

    <!-- Panel inputów — po prawej -->
    <div class="inputs-panel">
      <div v-if="selectedZones.size === 0" class="no-sel">
        <q-icon name="touch_app" size="16px" class="q-mr-xs"/>
        Kliknij strefę na diagramie, podaj h<sub>i</sub> (m) i udział cykli cc<sub>i</sub>&nbsp;(%). Suma cc = 100%.
      </div>
      <template v-else>
        <div class="it-head">
          <span class="it-c-no">Nr</span>
          <span class="it-c-range">Zakres</span>
          <span class="it-c-h">h<sub>i</sub> [m]</span>
          <span class="it-c-cc">cc<sub>i</sub> [%]</span>
          <span class="it-c-del"></span>
        </div>
        <div v-for="zi in sortedSelected" :key="zi" class="it-row">
          <span class="it-c-no">
            <span class="zone-dot">{{ zi }}</span>
          </span>
          <span class="it-c-range">{{ ZONES.find(z => z.i === zi)?.range }}</span>
          <span class="it-c-h">
            <q-input
              :model-value="getNum('h_' + zi)"
              @update:model-value="v => setNum('h_' + zi, v)"
              type="number" dense outlined hide-bottom-space
              :min="0" step="0.1" input-style="text-align:right;padding:0 4px"
              class="it-inp"
            />
          </span>
          <span class="it-c-cc">
            <q-input
              :model-value="getNum('cc_' + zi)"
              @update:model-value="v => setNum('cc_' + zi, v)"
              type="number" dense outlined hide-bottom-space
              :min="0" :max="100" step="1" input-style="text-align:right;padding:0 4px"
              :color="ccSumOk ? 'positive' : 'warning'"
              class="it-inp"
            />
          </span>
          <span class="it-c-del">
            <q-btn flat round dense icon="close" color="negative" size="xs"
                   @click="removeZone(zi)"/>
          </span>
        </div>
        <div class="it-foot">
          <q-chip dense :color="ccSumOk ? 'positive' : 'warning'"
                  text-color="white" icon="functions" size="sm">
            Σ cc = {{ ccSum }}%
          </q-chip>
          <span v-if="!ccSumOk && ccRemaining > 0" class="remain-hint">
            pozostało {{ ccRemaining }}%
            <q-btn flat dense size="xs" color="primary" no-caps
                   label="dopełnij →" @click="fillRemaining"/>
          </span>
          <span v-else-if="!ccSumOk && ccRemaining < 0" class="remain-hint warn">
            przekroczono o {{ -ccRemaining }}%
          </span>
        </div>
      </template>
    </div>

    </div><!-- /schem-body -->
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })
const d = props.data

const ZONES = [
  { i: 5, range: '80–100% h_max' },
  { i: 4, range: '60–80% h_max' },
  { i: 3, range: '40–60% h_max' },
  { i: 2, range: '20–40% h_max' },
  { i: 1, range: '0–20% h_max' },
]

const ZONE_FILLS_UNSEL = [
  'rgba(21,101,192,0.12)',
  'rgba(21,101,192,0.08)',
  'rgba(21,101,192,0.05)',
  'rgba(21,101,192,0.03)',
  'rgba(21,101,192,0.01)',
]
const ZONE_FILLS_SEL = [
  'rgba(21,101,192,0.28)',
  'rgba(21,101,192,0.23)',
  'rgba(21,101,192,0.18)',
  'rgba(21,101,192,0.14)',
  'rgba(21,101,192,0.10)',
]

function zoneBgFill(zoneI, idx) {
  return isSelected(zoneI) ? ZONE_FILLS_SEL[idx] : ZONE_FILLS_UNSEL[idx]
}

function getNum(key) {
  const v = d[key]
  return v != null && typeof v === 'object' ? (v.value ?? null) : (v ?? null)
}
function setNum(key, rawVal) {
  const num = rawVal !== '' && rawVal != null ? Number(rawVal) : null
  const existing = d[key]
  d[key] = existing != null && typeof existing === 'object'
    ? { ...existing, value: num } : num
}
function clearNum(key) {
  const existing = d[key]
  d[key] = existing != null && typeof existing === 'object'
    ? { ...existing, value: null } : null
}

const selectedZones = ref(new Set())

watch(() => props.data, (val) => {
  if (!val) return
  const s = new Set()
  for (let i = 1; i <= 5; i++) {
    const h = getNum(`h_${i}`)
    const cc = getNum(`cc_${i}`)
    if ((h != null && h !== '') || (cc != null && cc !== '')) s.add(i)
  }
  selectedZones.value = s
}, { immediate: true })

function isSelected(i) { return selectedZones.value.has(i) }

function toggleZone(i) {
  if (selectedZones.value.has(i)) {
    selectedZones.value.delete(i)
    clearNum(`h_${i}`)
    clearNum(`cc_${i}`)
  } else {
    selectedZones.value.add(i)
  }
}
function removeZone(i) {
  selectedZones.value.delete(i)
  clearNum(`h_${i}`)
  clearNum(`cc_${i}`)
}

const sortedSelected = computed(() => [...selectedZones.value].sort((a, b) => b - a))

const ccSum = computed(() => {
  let s = 0
  for (const i of selectedZones.value) s += Number(getNum(`cc_${i}`) ?? 0)
  return Math.round(s * 10) / 10
})
const ccSumOk = computed(() => ccSum.value === 100)
const ccRemaining = computed(() => Math.round((100 - ccSum.value) * 10) / 10)

function fillRemaining() {
  // Dopełnij ostatnią wybraną strefę do 100%
  const last = sortedSelected.value[sortedSelected.value.length - 1]
  if (last == null || ccRemaining.value <= 0) return
  const cur = Number(getNum(`cc_${last}`) ?? 0)
  setNum(`cc_${last}`, Math.min(100, cur + ccRemaining.value))
}
</script>

<style scoped>
.schem-hdr-wrap {
  border: 1px solid rgba(21,101,192,0.18);
  border-radius: 10px;
  padding: 12px;
}
.body--dark .schem-hdr-wrap { border-color: rgba(144,202,249,0.22); }

.schem-hd {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.schem-title { font-size: 13px; font-weight: 700; color: #1565C0; }
.body--dark .schem-title { color: #90caf9; }
.schem-formula { font-size: 12px; color: #1976d2; font-style: italic; }
.body--dark .schem-formula { color: #64b5f6; }
.schem-hint { font-size: 11px; color: #78909c; margin-left: auto; }

.svg-above-hint {
  font-size: 11px;
  font-style: italic;
  color: #90caf9;
  text-align: center;
  margin-bottom: 4px;
}

.schem-body {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.schem-svg {
  flex: 0 0 23%;
  width: 23%;
  display: block;
}

.inputs-panel {
  flex: 0 0 auto;
}

.no-sel {
  font-size: 12px;
  color: #90a4ae;
  font-style: italic;
  padding: 12px 0;
}

.it-head, .it-row {
  display: grid;
  grid-template-columns: 38px auto 72px 72px 28px;
  align-items: center;
  gap: 0;
}
.it-head {
  background: rgba(21,101,192,0.08);
  padding: 5px 6px;
  font-size: 11px;
  font-weight: 700;
  color: #1565C0;
  border-radius: 6px 6px 0 0;
  border: 1px solid rgba(21,101,192,0.18);
  border-bottom: none;
}
.body--dark .it-head { background: rgba(21,101,192,0.2); color: #90caf9; border-color: rgba(144,202,249,0.2); }
.it-head span { padding: 0 3px; }
.it-c-h, .it-c-cc, .it-c-del { text-align: center; }

.it-row {
  border: 1px solid rgba(21,101,192,0.12);
  border-top: none;
  padding: 3px 6px;
}
.it-row:last-of-type { border-radius: 0 0 6px 6px; }
.it-row:nth-child(odd) { background: rgba(21,101,192,0.025); }
.body--dark .it-row { border-color: rgba(144,202,249,0.15); }
.body--dark .it-row:nth-child(odd) { background: rgba(21,101,192,0.08); }

.zone-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px; height: 26px;
  background: #1565C0;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 800;
}

.it-c-range {
  font-size: 10px;
  color: #546e7a;
  padding: 0 4px;
}
.body--dark .it-c-range { color: #90a4ae; }

.it-c-h, .it-c-cc { padding: 2px 3px; }
.it-inp { width: 100%; }

.it-c-del {
  display: flex;
  justify-content: center;
}

.it-foot {
  padding: 6px 4px 2px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.remain-hint {
  font-size: 11px;
  color: #ef6c00;
  display: flex;
  align-items: center;
  gap: 2px;
}
.remain-hint.warn { color: #c62828; }

.no-sel {
  font-size: 11px;
  color: #78909c;
  font-style: italic;
  padding: 8px 0;
  line-height: 1.5;
}
</style>
