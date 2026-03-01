<template>
  <div class="schem-wrap q-mb-sm">
    <div class="text-caption text-grey-7 q-mb-xs text-weight-medium">
      Schemat stref wysokości — współczynnik <em>H<sub>dr</sub></em>
    </div>
    <div class="text-caption text-grey-6 q-mb-sm">
      Kliknij strefę, podaj wys. h<sub>i</sub> (m) i udział cykli cc<sub>i</sub> (%). Suma cc<sub>i</sub> = 100%.
    </div>

    <div class="row items-start q-col-gutter-md">

      <!-- ── 1. Schemat referencyjny (podest nożycowy z osią wysokości) ── -->
      <div class="col-auto ref-col">
        <svg viewBox="0 0 120 265" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;max-width:120px;display:block">
          <defs>
            <marker id="avHdr" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
              <path d="M0,0 L5,2.5 L0,5 Z" fill="#1b5e20"/>
            </marker>
          </defs>
          <!-- Oś Y: h_pod/h_max -->
          <line x1="40" y1="245" x2="40" y2="5" stroke="#1b5e20" stroke-width="1.3" marker-end="url(#avHdr)"/>
          <!-- Etykiety Y -->
          <text x="36" y="245" font-size="7.5" fill="#1b5e20" text-anchor="end">0%</text>
          <text x="36" y="197" font-size="7.5" fill="#1b5e20" text-anchor="end">20%</text>
          <text x="36" y="149" font-size="7.5" fill="#1b5e20" text-anchor="end">40%</text>
          <text x="36" y="101" font-size="7.5" fill="#1b5e20" text-anchor="end">60%</text>
          <text x="36" y="53"  font-size="7.5" fill="#1b5e20" text-anchor="end">80%</text>
          <text x="36" y="10"  font-size="7.5" fill="#1b5e20" text-anchor="end">100%</text>
          <!-- Opis osi Y -->
          <text x="9" y="128" font-size="7.5" fill="#1b5e20" text-anchor="middle"
                transform="rotate(-90,9,128)">h_pod/h_max[%]</text>
          <!-- Linie siatki poziome -->
          <line x1="40" y1="10"  x2="115" y2="10"  stroke="#1b5e20" stroke-width="0.6"/>
          <line x1="40" y1="58"  x2="115" y2="58"  stroke="#1b5e20" stroke-width="0.6"/>
          <line x1="40" y1="106" x2="115" y2="106" stroke="#1b5e20" stroke-width="0.6"/>
          <line x1="40" y1="154" x2="115" y2="154" stroke="#1b5e20" stroke-width="0.6"/>
          <line x1="40" y1="202" x2="115" y2="202" stroke="#1b5e20" stroke-width="0.6"/>
          <!-- Sylwetka podestu nożycowego -->
          <!-- Platforma górna -->
          <rect x="41" y="12" width="68" height="9" fill="none" stroke="#1b5e20" stroke-width="1.8" rx="1"/>
          <!-- Barierka -->
          <line x1="41"  y1="12" x2="41"  y2="5"  stroke="#1b5e20" stroke-width="1.4"/>
          <line x1="109" y1="12" x2="109" y2="5"  stroke="#1b5e20" stroke-width="1.4"/>
          <line x1="41"  y1="5"  x2="109" y2="5"  stroke="#1b5e20" stroke-width="1.4"/>
          <!-- Nożyce (dwa skrzyżowane ramiona) -->
          <line x1="57"  y1="21" x2="78"  y2="233" stroke="#1b5e20" stroke-width="1.6"/>
          <line x1="93"  y1="21" x2="57"  y2="233" stroke="#1b5e20" stroke-width="1.6"/>
          <!-- Rama dolna -->
          <rect x="47" y="233" width="58" height="9" fill="none" stroke="#1b5e20" stroke-width="1.8" rx="1"/>
          <!-- Koła -->
          <circle cx="59"  cy="249" r="7" fill="none" stroke="#1b5e20" stroke-width="1.5"/>
          <circle cx="97"  cy="249" r="7" fill="none" stroke="#1b5e20" stroke-width="1.5"/>
          <!-- Linia terenu -->
          <line x1="35" y1="257" x2="115" y2="257" stroke="#1b5e20" stroke-width="1.2" stroke-dasharray="4,3"/>
          <text x="75" y="265" font-size="7" fill="#1b5e20" text-anchor="middle">poziom terenu</text>
        </svg>
      </div>

      <!-- ── 2. Klikalne strefy wysokości (siatka 1×5) ── -->
      <div class="col-auto grid-col">
        <svg viewBox="0 0 260 240" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;max-width:260px;display:block;touch-action:manipulation">

          <!-- Nagłówek górny -->
          <rect x="0" y="0" width="260" height="40" fill="#1b5e20"/>
          <text x="130" y="15" font-size="9.5" fill="white" text-anchor="middle" font-weight="bold">Strefa</text>
          <text x="130" y="31" font-size="9"   fill="white" text-anchor="middle">h_pod / h_max [%]</text>

          <!-- 5 stref (idx=0 → Strefa 5, H 80-100%, GÓRA) -->
          <template v-for="(z, idx) in ZONES" :key="z.i">
            <!-- Etykieta wiersza (dark green) -->
            <rect x="0" :y="40 + idx*40" width="130" height="40" fill="#1b5e20"/>
            <text x="65" :y="40 + idx*40 + 15" font-size="10" fill="white" text-anchor="middle" font-weight="bold">
              Strefa {{ z.i }}
            </text>
            <text x="65" :y="40 + idx*40 + 30" font-size="8" fill="white" text-anchor="middle">
              {{ z.range }}
            </text>
            <!-- Klikalna komórka -->
            <rect
              x="130" :y="40 + idx*40" width="130" height="40"
              :fill="isSelected(z.i) ? '#2e7d32' : '#ffffff'"
              stroke="#4caf50" stroke-width="0.7"
              rx="1" style="cursor:pointer"
              @click="toggleZone(z.i)"
            />
            <text
              v-if="isSelected(z.i)"
              x="195" :y="40 + idx*40 + 26"
              font-size="17" font-weight="bold" text-anchor="middle" fill="white"
              style="pointer-events:none;user-select:none"
            >{{ z.i }}</text>
          </template>

          <!-- Obramowanie -->
          <rect x="0" y="0" width="260" height="240" fill="none" stroke="#1b5e20" stroke-width="1.4"/>
        </svg>
      </div>

      <!-- ── 3. Tabela inputów (prawa kolumna) ── -->
      <div class="col inputs-col">
        <div v-if="selectedZones.size === 0" class="text-caption text-grey-5 q-pa-md text-center">
          ← Zaznacz strefę na schemacie
        </div>
        <template v-else>
          <div v-for="zi in sortedSelected" :key="zi" class="z-block">
            <div class="z-header">Strefa {{ zi }} — {{ ZONES.find(z => z.i === zi).range }}</div>
            <div class="z-row">
              <div class="z-label">Typowa wysokość h<sub>{{ zi }}</sub> (m):</div>
              <div class="z-input">
                <q-input
                  :model-value="getNum('h_' + zi)"
                  @update:model-value="v => setNum('h_' + zi, v)"
                  type="number" dense outlined hide-bottom-space
                  :min="0" step="0.1"
                  input-style="text-align:right"
                />
              </div>
            </div>
            <div class="z-row">
              <div class="z-label">Udział cykli cc<sub>{{ zi }}</sub> (%):</div>
              <div class="z-input">
                <q-input
                  :model-value="getNum('cc_' + zi)"
                  @update:model-value="v => setNum('cc_' + zi, v)"
                  type="number" dense outlined hide-bottom-space
                  :min="0" :max="100" step="1"
                  input-style="text-align:right"
                  :color="ccSumOk ? 'positive' : 'warning'"
                  suffix="%"
                />
              </div>
              <div class="z-action">
                <q-btn flat round dense icon="close" color="negative" size="xs" @click="removeZone(zi)" />
              </div>
            </div>
          </div>

          <div class="q-mt-sm">
            <q-chip size="sm" :color="ccSumOk ? 'positive' : 'warning'" text-color="white" dense icon="functions">
              Σ cc = {{ ccSum }}% <span class="q-ml-xs opacity-80">(wymagane 100%)</span>
            </q-chip>
          </div>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })

// `d` to ten sam obiekt co formData w rodzicu — mutacja wewnętrznych kluczy jest celowa
const d = props.data

// Strefy: idx=0 → Strefa 5 (GÓRA, H 80-100%), idx=4 → Strefa 1 (DÓŁ, H 0-20%)
const ZONES = [
  { i: 5, range: '80–100% h_max' },
  { i: 4, range: '60–80% h_max' },
  { i: 3, range: '40–60% h_max' },
  { i: 2, range: '20–40% h_max' },
  { i: 1, range: '0–20% h_max' },
]

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

// Przywróć zaznaczenie przy wczytaniu zapisanego wyniku
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

// Wyświetlaj od najwyższej strefy do najniższej
const sortedSelected = computed(() => [...selectedZones.value].sort((a, b) => b - a))

const ccSum = computed(() => {
  let s = 0
  for (const i of selectedZones.value) s += Number(getNum(`cc_${i}`) ?? 0)
  return Math.round(s * 10) / 10
})
const ccSumOk = computed(() => ccSum.value === 100)
</script>

<style scoped>
.schem-wrap {
  border: 1px solid rgba(0,0,0,.09);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}
.body--dark .schem-wrap { background: #1e2530; border-color: rgba(255,255,255,.1); }

.ref-col   { min-width: 100px; max-width: 130px; }
.grid-col  { min-width: 200px; max-width: 260px; }
.inputs-col { min-width: 240px; }

/* Blok jednej strefy w tabeli inputów */
.z-block {
  border: 1px solid #4caf50;
  border-radius: 4px;
  margin-bottom: 8px;
  overflow: hidden;
}
.z-header {
  background: #1b5e20;
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
}
.z-row {
  display: flex;
  align-items: center;
  border-top: 1px solid #e8f5e9;
}
.z-label {
  flex: 1;
  background: #e8f5e9;
  color: #1b5e20;
  font-size: 11px;
  font-weight: 600;
  padding: 5px 10px;
  border-right: 1px solid #4caf50;
}
.body--dark .z-label { background: #1a3a1a; color: #a5d6a7; }
.z-input {
  width: 90px;
  padding: 3px 6px;
  background: #fff;
}
.body--dark .z-input { background: #263238; }
.z-action {
  width: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
.body--dark .z-action { background: #263238; }
</style>
