<template>
  <div class="schem-wrap">

    <!-- Nagłówek -->
    <div class="schem-hd">
      <span class="schem-title">Widmo obciążeń — <em>L<sub>dr</sub></em></span>
      <span class="schem-formula">= Σ [ p<sub>i</sub>/100 · (L<sub>b,i</sub>/L<sub>max</sub>)<sup>3</sup> ]</span>
    </div>

    <!-- Ciało: SVG po lewej, panel po prawej -->
    <div class="schem-body">

      <!-- SVG z siatką 5×5 i pojazdem -->
      <svg viewBox="-10 0 410 490" xmlns="http://www.w3.org/2000/svg"
           class="schem-svg" style="touch-action:manipulation">

        <!-- Siatka: (0,0) = zgięcie wysięgnika = (105,368). Grid x=105–345, y=128–368 -->
        <rect x="105" y="128" width="240" height="240" fill="rgba(21,101,192,0.05)" rx="3"/>

        <!-- Siatka pomocnicza (co 48px) -->
        <g stroke="#90caf9" stroke-width="0.7" stroke-dasharray="3,3" fill="none">
          <line x1="109" y1="368" x2="347" y2="368"/>
          <line x1="109" y1="320" x2="347" y2="320"/>
          <line x1="109" y1="272" x2="347" y2="272"/>
          <line x1="109" y1="224" x2="347" y2="224"/>
          <line x1="109" y1="176" x2="347" y2="176"/>
          <line x1="109" y1="128" x2="347" y2="128"/>
          <line x1="105" y1="125" x2="105" y2="372"/>
          <line x1="153" y1="125" x2="153" y2="372"/>
          <line x1="201" y1="125" x2="201" y2="372"/>
          <line x1="249" y1="125" x2="249" y2="372"/>
          <line x1="297" y1="125" x2="297" y2="372"/>
          <line x1="345" y1="125" x2="345" y2="372"/>
        </g>

        <!-- Osie — przecięcie dokładnie w zgięciu wysięgnika (105,368) -->
        <g stroke="#1565C0" stroke-width="2" fill="#1565C0">
          <line x1="105" y1="368" x2="105" y2="88"/>
          <polygon points="99,100 105,80 111,100" stroke="none"/>
          <line x1="105" y1="368" x2="367" y2="368"/>
          <polygon points="356,362 373,368 356,374" stroke="none"/>
        </g>

        <!-- Y-axis ticks + etykiety -->
        <g fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
           font-size="10" font-weight="600" text-anchor="end" dominant-baseline="middle">
          <line x1="99" y1="368" x2="111" y2="368" stroke="#1565C0" stroke-width="1.4"/>
          <text x="93" y="368">0%</text>
          <line x1="99" y1="320" x2="111" y2="320" stroke="#1565C0" stroke-width="1.4"/>
          <text x="93" y="320">20%</text>
          <line x1="99" y1="272" x2="111" y2="272" stroke="#1565C0" stroke-width="1.4"/>
          <text x="93" y="272">40%</text>
          <line x1="99" y1="224" x2="111" y2="224" stroke="#1565C0" stroke-width="1.4"/>
          <text x="93" y="224">60%</text>
          <line x1="99" y1="176" x2="111" y2="176" stroke="#1565C0" stroke-width="1.4"/>
          <text x="93" y="176">80%</text>
          <line x1="99" y1="128" x2="111" y2="128" stroke="#1565C0" stroke-width="1.4"/>
          <text x="93" y="128">100%</text>
        </g>
        <text x="52" y="248" fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
              font-size="11" font-weight="700"
              transform="rotate(-90 52 248)" text-anchor="middle">h_pod / h_max</text>

        <!-- X-axis ticks + etykiety -->
        <g fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
           font-size="10" font-weight="600" text-anchor="middle">
          <line x1="105" y1="366" x2="105" y2="374" stroke="#1565C0" stroke-width="1.4"/>
          <text x="105" y="384">0%</text>
          <line x1="153" y1="366" x2="153" y2="374" stroke="#1565C0" stroke-width="1.4"/>
          <text x="153" y="384">20%</text>
          <line x1="201" y1="366" x2="201" y2="374" stroke="#1565C0" stroke-width="1.4"/>
          <text x="201" y="384">40%</text>
          <line x1="249" y1="366" x2="249" y2="374" stroke="#1565C0" stroke-width="1.4"/>
          <text x="249" y="384">60%</text>
          <line x1="297" y1="366" x2="297" y2="374" stroke="#1565C0" stroke-width="1.4"/>
          <text x="297" y="384">80%</text>
          <line x1="345" y1="366" x2="345" y2="374" stroke="#1565C0" stroke-width="1.4"/>
          <text x="345" y="384">100%</text>
        </g>
        <text x="225" y="397" fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
              font-size="10" font-weight="700" text-anchor="middle">L_b / L_max</text>

        <!-- Pojazd z ldr.svg — przeskalowany 0.47×, przeniesiony poniżej osi X -->
        <!-- Transformacja: new_x = old_x*0.47 - 74,  new_y = old_y*0.47 + 246 -->
        <g fill="none" stroke="#1565C0" stroke-linecap="round" stroke-linejoin="round"
           stroke-width="2.5" opacity="0.72">

          <!-- Koła (ldr: cx=260,r=40 i cx=500,r=40) -->
          <circle cx="48"  cy="462" r="19"/>
          <circle cx="161" cy="462" r="19"/>

          <!-- Podwozie (3 segmenty): ldr x1=140→220, 300→460, 540→580 y=440 -->
          <line x1="-8"  y1="453" x2="29"  y2="453"/>
          <line x1="67"  y1="453" x2="142" y2="453"/>
          <line x1="180" y1="453" x2="199" y2="453"/>

          <!-- Lewa ściana kabiny: ldr 140,440→140,380 -->
          <line x1="-8"  y1="453" x2="-8"  y2="425"/>
          <!-- Szyba przednia (ukośna): ldr 140,380→200,320 -->
          <line x1="-8"  y1="425" x2="20"  y2="396"/>
          <!-- Dach kabiny: ldr 200,320→300,320 -->
          <line x1="20"  y1="396" x2="67"  y2="396"/>
          <!-- Tylna ściana kabiny: ldr 300,320→300,440 -->
          <line x1="67"  y1="396" x2="67"  y2="453"/>
          <!-- Podłoga kabiny: ldr 140,380→300,380 -->
          <line x1="-8"  y1="425" x2="67"  y2="425"/>

          <!-- Prawa ściana (tył): ldr 580,380→580,440 -->
          <line x1="199" y1="425" x2="199" y2="453"/>
          <!-- Górna krawędź platformy: ldr 300,380→580,380 -->
          <line x1="67"  y1="425" x2="199" y2="425"/>

          <!-- Wysięgnik dolny: ldr 460,380→380,260 (w górę-lewo od platformy) -->
          <line x1="142" y1="425" x2="105" y2="368"/>
          <!-- Wysięgnik górny: do 2/3 siatki (L=67%, H=67%), kosz przy (265,208) -->
          <line x1="105" y1="368" x2="265" y2="208"/>

        </g>

        <!-- Kosz: L≈67%, H≈67% nowej siatki (x=105–345, y=128–368) -->
        <rect x="254" y="197" width="22" height="13" fill="#1565C0" rx="2" opacity="0.85"/>

        <!-- Siatka 5×5 — interaktywne komórki (48×48px, x od 105, y od 128) -->
        <template v-for="svgRow in 5" :key="svgRow">
          <template v-for="col in 5" :key="col">
            <rect
              :x="105 + (col-1)*48 + 1" :y="128 + (svgRow-1)*48 + 1"
              width="46" height="46" rx="4"
              :fill="cellFill(svgRow, col)"
              :stroke="isSelected(zone(svgRow,col)) ? '#0d47a1' : '#b3d4f5'"
              :stroke-width="isSelected(zone(svgRow,col)) ? 2 : 0.8"
              style="cursor:pointer"
              @click="toggleZone(zone(svgRow, col))"
            >
              <title>Strefa {{ zone(svgRow,col) }}: H={{ ROW_LABELS[svgRow-1] }}, L={{ COL_LABELS[col-1] }}</title>
            </rect>
            <text
              :x="129 + (col-1)*48"
              :y="152 + (svgRow-1)*48 + (pValStr(zone(svgRow,col)) ? -6 : 0)"
              text-anchor="middle" dominant-baseline="middle"
              :font-size="isSelected(zone(svgRow,col)) ? 12 : 10"
              font-weight="700"
              :fill="isSelected(zone(svgRow,col)) ? '#fff' : '#1565C0'"
              style="pointer-events:none;user-select:none"
            >{{ zone(svgRow, col) }}</text>
            <text v-if="pValStr(zone(svgRow, col))"
              :x="129 + (col-1)*48" :y="152 + (svgRow-1)*48 + 8"
              text-anchor="middle" dominant-baseline="middle"
              font-size="10" font-weight="700" fill="#fff"
              style="pointer-events:none;user-select:none"
            >{{ pValStr(zone(svgRow, col)) }}%</text>
          </template>
        </template>

        <!-- Obramowanie siatki -->
        <rect x="105" y="128" width="240" height="240" fill="none"
              stroke="#1565C0" stroke-width="1.5" rx="3"/>


      </svg>

      <!-- Panel inputów — po prawej -->
      <div class="inputs-panel">
        <div v-if="selectedZones.size === 0" class="no-sel">
          <q-icon name="touch_app" size="16px" class="q-mr-xs"/>
          Kliknij strefę na diagramie, podaj udział cykli p<sub>i</sub>&nbsp;(%). Suma p = 100%.
        </div>
        <template v-else>
          <div class="it-head">
            <span class="it-c-no">Nr</span>
            <span class="it-c-h">H zakres</span>
            <span class="it-c-l">L zakres</span>
            <span class="it-c-p">p<sub>i</sub> [%]</span>
            <span class="it-c-del"></span>
          </div>
          <div v-for="n in sortedSelected" :key="n" class="it-row">
            <span class="it-c-no">
              <span class="zone-dot">{{ n }}</span>
            </span>
            <span class="it-c-h">{{ ROW_LABELS[zoneRow(n) - 1] }}</span>
            <span class="it-c-l">{{ COL_LABELS[zoneCol(n) - 1] }}</span>
            <span class="it-c-p">
              <q-input
                :model-value="getNum('p_' + n)"
                @update:model-value="v => setNum('p_' + n, v)"
                type="number" dense outlined hide-bottom-space
                :min="0" :max="100" step="1"
                input-style="text-align:right;padding:0 4px"
                :color="pSumOk ? 'positive' : 'warning'"
                class="it-inp"
              />
            </span>
            <span class="it-c-del">
              <q-btn flat round dense icon="close" color="negative" size="xs"
                     @click="removeZone(n)"/>
            </span>
          </div>
          <div class="it-foot">
            <q-chip dense :color="pSumOk ? 'positive' : 'warning'"
                    text-color="white" icon="functions" size="sm">
              Σ p = {{ pSum }}%
            </q-chip>
            <span v-if="!pSumOk && pRemaining > 0" class="remain-hint">
              pozostało {{ pRemaining }}%
              <q-btn flat dense size="xs" color="primary" no-caps
                     label="dopełnij →" @click="fillRemaining"/>
            </span>
            <span v-else-if="!pSumOk && pRemaining < 0" class="remain-hint warn">
              przekroczono o {{ -pRemaining }}%
            </span>
          </div>
        </template>
      </div>

    </div><!-- /schem-body -->
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Notify } from 'quasar'

const props = defineProps({ data: { type: Object, required: true } })
const d = props.data

const ROW_LABELS = ['80–100%', '60–80%', '40–60%', '20–40%', '0–20%']
const COL_LABELS = ['0–20%', '20–40%', '40–60%', '60–80%', '80–100%']

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

function zone(svgRow, col) { return (svgRow - 1) * 5 + col }
function zoneRow(n) { return Math.ceil(n / 5) }
function zoneCol(n) { return ((n - 1) % 5) + 1 }
function isSelected(n) { return selectedZones.value.has(n) }

function pValStr(n) {
  const v = getNum(`p_${n}`)
  return (v != null && v !== '') ? String(v) : null
}

function cellFill(svgRow, col) {
  const n = zone(svgRow, col)
  if (!isSelected(n)) return 'transparent'
  const t = ((6 - svgRow) + (col - 1)) / 8
  const r = Math.round(13 + t * 8)
  const g = Math.round(71 + t * 20)
  const b = Math.round(192 - t * 30)
  return `rgb(${r},${g},${b})`
}

function toggleZone(n) {
  if (selectedZones.value.has(n)) {
    selectedZones.value.delete(n)
    clearNum(`p_${n}`)
  } else if (selectedZones.value.size >= 5) {
    Notify.create({ type: 'warning', message: 'Maksymalnie 5 stref', position: 'top', timeout: 2000 })
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
const pRemaining = computed(() => Math.round((100 - pSum.value) * 10) / 10)

function fillRemaining() {
  const last = sortedSelected.value[sortedSelected.value.length - 1]
  if (last == null || pRemaining.value <= 0) return
  const cur = Number(getNum(`p_${last}`) ?? 0)
  setNum(`p_${last}`, Math.min(100, cur + pRemaining.value))
}
</script>

<style scoped>
.schem-wrap {
  border: 1px solid rgba(21,101,192,0.18);
  border-radius: 10px;
  padding: 12px;
}
.body--dark .schem-wrap { border-color: rgba(144,202,249,0.22); }

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

/* Ciało: SVG + panel obok siebie */
.schem-body {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.schem-svg {
  flex: 0 0 30%;
  width: 30%;
  display: block;
}

/* Panel inputów po prawej */
.inputs-panel {
  flex: 0 0 auto;
}

/* Tabela inputów */
.it-head, .it-row {
  display: grid;
  grid-template-columns: 38px auto auto 80px 28px;
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
.it-c-p, .it-c-del { text-align: center; }

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

.it-c-h, .it-c-l {
  font-size: 10px;
  color: #546e7a;
  padding: 0 4px;
}
.body--dark .it-c-h, .body--dark .it-c-l { color: #90a4ae; }

.it-c-p { padding: 2px 3px; }
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
