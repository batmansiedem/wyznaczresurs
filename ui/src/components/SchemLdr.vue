<template>
  <div class="schem-wrap q-mb-sm">
    <div class="text-caption text-grey-7 q-mb-xs text-weight-medium">
      Schemat stref zasięgu i wysokości — współczynnik <em>L<sub>dr</sub></em>
    </div>
    <div class="text-caption text-grey-6 q-mb-sm">
      Zaznacz do <strong>5</strong> punktów na diagramie. Suma p<sub>i</sub> = 100%.
    </div>

    <div class="row items-start q-col-gutter-md">

      <!-- ── Diagram LDR (ldr.svg + 25 klikalnych punktów) ── -->
      <div class="col ldr-col">
        <svg viewBox="0 0 920 600" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;display:block;touch-action:manipulation">

          <!-- ── ldr.svg content (style → presentation attributes) ── -->
          <rect width="100%" height="100%" fill="#ffffff"/>

          <!-- Siatka -->
          <g fill="none" stroke="#000080" stroke-width="1.5" stroke-opacity="0.35"
             stroke-linecap="round" stroke-linejoin="round">
            <line x1="80"  y1="380" x2="820" y2="380"/>
            <line x1="80"  y1="320" x2="820" y2="320"/>
            <line x1="80"  y1="260" x2="820" y2="260"/>
            <line x1="80"  y1="200" x2="820" y2="200"/>
            <line x1="80"  y1="140" x2="820" y2="140"/>
            <line x1="80"  y1="80"  x2="820" y2="80"/>
            <line x1="500" y1="80"  x2="500" y2="520"/>
            <line x1="560" y1="80"  x2="560" y2="520"/>
            <line x1="620" y1="80"  x2="620" y2="520"/>
            <line x1="680" y1="80"  x2="680" y2="520"/>
            <line x1="740" y1="80"  x2="740" y2="520"/>
            <line x1="800" y1="80"  x2="800" y2="520"/>
          </g>

          <!-- Osie -->
          <g fill="none" stroke="#000080" stroke-width="2.5"
             stroke-linecap="round" stroke-linejoin="round">
            <line x1="100" y1="500" x2="100" y2="35"/>
            <line x1="100" y1="500" x2="865" y2="500"/>
          </g>
          <polygon points="93,45 100,15 107,45"    fill="#000080" stroke="none"/>
          <polygon points="855,493 885,500 855,507" fill="#000080" stroke="none"/>

          <!-- Pojazd -->
          <g fill="none" stroke="#000080" stroke-width="5"
             stroke-linecap="round" stroke-linejoin="round">
            <circle cx="260" cy="460" r="40"/>
            <circle cx="500" cy="460" r="40"/>
            <line x1="140" y1="440" x2="220" y2="440"/>
            <line x1="300" y1="440" x2="460" y2="440"/>
            <line x1="540" y1="440" x2="580" y2="440"/>
            <line x1="140" y1="440" x2="140" y2="380"/>
            <line x1="140" y1="380" x2="200" y2="320"/>
            <line x1="200" y1="320" x2="300" y2="320"/>
            <line x1="300" y1="320" x2="300" y2="440"/>
            <line x1="140" y1="380" x2="300" y2="380"/>
            <line x1="580" y1="380" x2="580" y2="440"/>
            <line x1="300" y1="380" x2="580" y2="380"/>
            <line x1="460" y1="380" x2="380" y2="260"/>
            <line x1="380" y1="260" x2="630" y2="190"/>
          </g>
          <rect x="630" y="155" width="45" height="35" fill="#000080" rx="3"/>

          <!-- Etykiety osi -->
          <text x="45" y="270" fill="#000080" font-family="'Segoe UI',Roboto,Helvetica,sans-serif"
                font-size="26" font-weight="700" letter-spacing="0.5"
                transform="rotate(-90 45 270)" text-anchor="middle">hpod/hmax[%]</text>
          <g fill="#000080" font-family="'Segoe UI',Roboto,Helvetica,sans-serif"
             font-size="15" font-weight="600" dominant-baseline="middle" text-anchor="middle">
            <text x="70" y="380" transform="rotate(-90 70 380)">0%</text>
            <text x="70" y="320" transform="rotate(-90 70 320)">20%</text>
            <text x="70" y="260" transform="rotate(-90 70 260)">40%</text>
            <text x="70" y="200" transform="rotate(-90 70 200)">60%</text>
            <text x="70" y="140" transform="rotate(-90 70 140)">80%</text>
            <text x="70" y="80"  transform="rotate(-90 70 80)">100%</text>
          </g>
          <text x="250" y="555" fill="#000080" font-family="'Segoe UI',Roboto,Helvetica,sans-serif"
                font-size="26" font-weight="700" letter-spacing="0.5">Lb/Lmax[%]</text>
          <g fill="#000080" font-family="'Segoe UI',Roboto,Helvetica,sans-serif"
             font-size="15" font-weight="600" dominant-baseline="middle" text-anchor="middle">
            <text x="500" y="530">0%</text>
            <text x="560" y="530">20%</text>
            <text x="620" y="530">40%</text>
            <text x="680" y="530">60%</text>
            <text x="740" y="530">80%</text>
            <text x="800" y="530">100%</text>
          </g>

          <!-- ── 25 klikalnych punktów ──
               svgRow=1 (góra, H 80-100%) → p1-p5
               svgRow=5 (dół, H 0-20%)   → p21-p25
               cx = 530 + (col-1)*60
               cy = 110 + (svgRow-1)*60  -->
          <template v-for="svgRow in 5" :key="svgRow">
            <template v-for="col in 5" :key="col">
              <circle
                :cx="530 + (col-1)*60"
                :cy="110 + (svgRow-1)*60"
                r="22"
                :fill="isSelected(zone(svgRow,col)) ? '#1b5e20' : 'rgba(255,255,255,0.88)'"
                :stroke="isSelected(zone(svgRow,col)) ? '#1b5e20' : '#000080'"
                :stroke-width="isSelected(zone(svgRow,col)) ? 2.5 : 1.5"
                style="cursor:pointer"
                @click="toggleZone(zone(svgRow, col))"
              />
              <text
                :x="530 + (col-1)*60"
                :y="110 + (svgRow-1)*60 + 1"
                :font-size="isSelected(zone(svgRow,col)) ? 14 : 11"
                :font-weight="isSelected(zone(svgRow,col)) ? 'bold' : 'normal'"
                text-anchor="middle" dominant-baseline="middle"
                :fill="isSelected(zone(svgRow,col)) ? '#ffffff' : '#000080'"
                style="pointer-events:none;user-select:none"
              >{{ zone(svgRow, col) }}</text>
            </template>
          </template>

        </svg>
      </div>

      <!-- ── Tabela inputów (prawa kolumna) ── -->
      <div class="col-auto inputs-col">
        <div v-if="selectedZones.size === 0" class="text-caption text-grey-5 q-pa-md text-center">
          ← Zaznacz punkt na diagramie<br>(maks. 5)
        </div>
        <template v-else>
          <div v-for="n in sortedSelected" :key="n" class="p-row">
            <div class="p-label">
              Procent cykli dla wybranego<br>punktu nr {{ n }} [%]:
            </div>
            <div class="p-input">
              <q-input
                :model-value="getNum('p_' + n)"
                @update:model-value="v => setNum('p_' + n, v)"
                type="number" dense outlined hide-bottom-space
                :min="0" :max="100" step="1"
                input-style="text-align:right"
                :color="pSumOk ? 'positive' : 'warning'"
              />
            </div>
            <div class="p-action">
              <q-btn flat round dense icon="close" color="negative" size="xs" @click="removeZone(n)" />
            </div>
          </div>

          <div class="q-mt-sm">
            <q-chip size="sm" :color="pSumOk ? 'positive' : 'warning'" text-color="white" dense icon="functions">
              Σ p = {{ pSum }}% <span class="q-ml-xs opacity-80">(wymagane 100%)</span>
            </q-chip>
          </div>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Notify } from 'quasar'

const props = defineProps({ data: { type: Object, required: true } })

// `d` to ten sam obiekt co formData w rodzicu — mutacja wewnętrznych kluczy jest celowa
const d = props.data

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
  for (let i = 1; i <= 25; i++) {
    const v = getNum(`p_${i}`)
    if (v != null && v !== '') s.add(i)
  }
  selectedZones.value = s
}, { immediate: true })

// svgRow=1 (GÓRA, H 80-100%) → p1-p5 | svgRow=5 (DÓŁ, H 0-20%) → p21-p25
function zone(svgRow, col) { return (svgRow - 1) * 5 + col }
function isSelected(n) { return selectedZones.value.has(n) }

function toggleZone(n) {
  if (selectedZones.value.has(n)) {
    selectedZones.value.delete(n)
    clearNum(`p_${n}`)
  } else if (selectedZones.value.size >= 5) {
    Notify.create({ type: 'warning', message: 'Możesz wybrać maksymalnie 5 punktów', position: 'top', timeout: 2000 })
  } else {
    selectedZones.value.add(n)
  }
}
function removeZone(n) { selectedZones.value.delete(n); clearNum(`p_${n}`) }

const sortedSelected = computed(() => [...selectedZones.value].sort((a, b) => a - b))
const pSum = computed(() => {
  let s = 0
  for (const n of selectedZones.value) s += Number(getNum(`p_${n}`) ?? 0)
  return Math.round(s * 10) / 10
})
const pSumOk = computed(() => pSum.value === 100)
</script>

<style scoped>
.schem-wrap {
  border: 1px solid rgba(0,0,0,.09);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}
.body--dark .schem-wrap { background: #1e2530; border-color: rgba(255,255,255,.1); }

.ldr-col    { min-width: 0; }
.inputs-col { min-width: 240px; max-width: 320px; }

/* Wiersz inputu — styl jak w calculator_1.jpg */
.p-row {
  display: flex;
  align-items: center;
  border: 1px solid #4caf50;
  border-radius: 4px;
  margin-bottom: 6px;
  overflow: hidden;
}
.p-label {
  flex: 1;
  background: #e8f5e9;
  color: #1b5e20;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 10px;
  line-height: 1.3;
  border-right: 1px solid #4caf50;
}
.body--dark .p-label { background: #1a3a1a; color: #a5d6a7; }
.p-input {
  width: 90px;
  padding: 4px 6px;
  background: #fff;
}
.body--dark .p-input { background: #263238; }
.p-action {
  width: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
.body--dark .p-action { background: #263238; }
</style>
