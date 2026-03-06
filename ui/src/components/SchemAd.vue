<template>
  <div class="schem-ad-wrap">

    <div class="schem-hd">
      <span class="schem-title">Współczynnik <em>α<sub>d</sub></em> — kąt między ścianą a drabiną windy</span>
    </div>

    <div class="ad-body">

      <!--
        GEOMETRIA: winda dekarska oparta o koniec ściany (płaski dach).
        Jedna drabina z ładunkiem — ilustracja czym jest kąt α.
        Oparcie: (185, 52) — koniec ściany (krawędź attyky / płaskiego dachu)
        Podstawa: (16, 215) — na ziemi
        Kierunek: (-169, 163), dł=235, α≈46° od ściany pionowej (ilustracyjne)
        Jedn. kierunku: (-0.7191, 0.6949); perp (CW): (0.6949, 0.7191)
      -->
      <svg viewBox="0 0 215 235" xmlns="http://www.w3.org/2000/svg" class="ad-svg">

        <!-- Podłoże -->
        <line x1="0" y1="215" x2="215" y2="215" stroke="#1565C0" stroke-width="1.5" opacity="0.4"/>

        <!-- ═══ Budynek z płaskim dachem ═══ -->
        <!-- Attyka / parapet (koniec ściany) -->
        <rect x="162" y="42" width="45" height="10" rx="1"
              fill="rgba(21,101,192,0.18)" stroke="#1565C0" stroke-width="1.5"/>
        <!-- Ściana budynku -->
        <rect x="185" y="52" width="22" height="163" rx="2"
              fill="rgba(21,101,192,0.07)" stroke="#1565C0" stroke-width="1.5"/>
        <line x1="185" y1="72"  x2="207" y2="52"  stroke="#1565C0" stroke-width="1" opacity="0.18"/>
        <line x1="185" y1="98"  x2="207" y2="78"  stroke="#1565C0" stroke-width="1" opacity="0.18"/>
        <line x1="185" y1="124" x2="207" y2="104" stroke="#1565C0" stroke-width="1" opacity="0.18"/>
        <line x1="185" y1="150" x2="207" y2="130" stroke="#1565C0" stroke-width="1" opacity="0.18"/>
        <line x1="185" y1="176" x2="207" y2="156" stroke="#1565C0" stroke-width="1" opacity="0.18"/>
        <line x1="185" y1="202" x2="207" y2="182" stroke="#1565C0" stroke-width="1" opacity="0.18"/>
        <!-- Okno -->
        <rect x="190" y="100" width="11" height="16" rx="1"
              fill="rgba(21,101,192,0.15)" stroke="#1565C0" stroke-width="1"/>

        <!-- ═══ Drabina windy dekarskiej ═══ -->
        <!-- Oparcie (185,52) → podstawa (16,215) -->
        <line x1="16" y1="215" x2="185" y2="52" stroke="#1565C0" stroke-width="2.5"/>
        <!-- Poprzeczki (prostopadle do osi, perp=(0.6949,0.7191)) -->
        <!-- t=65: center=(138.3,97.2), ±5*perp → (141.8,100.8)–(134.8,93.6) -->
        <line x1="141.8" y1="100.8" x2="134.8" y2="93.6"
              stroke="#1565C0" stroke-width="1.4" opacity="0.7"/>
        <!-- t=120: center=(99.1,135.4), ±5*perp → (102.6,139.0)–(95.6,131.8) -->
        <line x1="102.6" y1="139.0" x2="95.6" y2="131.8"
              stroke="#1565C0" stroke-width="1.4" opacity="0.7"/>
        <!-- t=175: center=(59.9,173.6), ±5*perp → (63.4,177.2)–(56.4,170.0) -->
        <line x1="63.4" y1="177.2" x2="56.4" y2="170.0"
              stroke="#1565C0" stroke-width="1.4" opacity="0.7"/>

        <!-- Platforma / ładunek (t=110 od góry, box 18×10 wzdłuż toru) -->
        <!-- center=(106.4,128.4); along*9=(-6.47,6.25); perp*5=(3.47,3.60) -->
        <polygon points="103.4,138.2 116.3,125.7 109.4,118.5 96.5,131.0"
                 fill="rgba(21,101,192,0.2)" stroke="#1565C0" stroke-width="1.8"/>

        <!-- ═══ Kąt α — między ścianą (pionową) a drabiną ═══ -->
        <!-- Arc przy (185,52): od (185,77) wzdłuż ściany do (166.9,69.4) wzdłuż drabiny.
             sweep=1 (CW w SVG) → łuk w WNĘTRZU kąta (między ścianą a drabiną). -->
        <path d="M185,77 A25,25 0 0,1 166.9,69.4"
              fill="none" stroke="#1565C0" stroke-width="1.5" opacity="0.9"/>
        <!-- Etykieta α wewnątrz łuku (środek łuku ≈ (175,75), odsunięcie w głąb kąta) -->
        <text x="163" y="83" fill="#1565C0" font-family="Roboto,sans-serif"
              font-size="15" font-weight="800" font-style="italic">α</text>

      </svg>

      <!-- Tabela 3 kątów -->
      <div class="ad-table">
        <div class="ad-head">
          <span class="ad-c-no">Kąt α</span>
          <span class="ad-c-c">a<sub>i</sub> [%]</span>
        </div>
        <div v-for="angle in ANGLES" :key="angle.key" class="ad-row">
          <span class="ad-c-no">
            <span class="angle-badge" :style="{ background: angle.color }">{{ angle.label }}</span>
          </span>
          <span class="ad-c-c">
            <q-input
              :model-value="getVal(angle.key)"
              @update:model-value="v => setVal(angle.key, v)"
              type="number" dense outlined hide-bottom-space
              :min="0" :max="100" step="1"
              input-style="text-align:right;padding:0 4px"
              :color="sumOk ? 'positive' : 'warning'"
              class="ad-inp"
            />
          </span>
        </div>
        <div class="ad-foot">
          <q-chip dense :color="sumOk ? 'positive' : 'warning'"
                  text-color="white" icon="functions" size="sm">
            Σ a = {{ aSum }}%
          </q-chip>
          <span v-if="!sumOk && remaining > 0" class="remain-hint">
            pozostało {{ remaining }}%
            <q-btn flat dense size="xs" color="primary" no-caps
                   label="dopełnij →" @click="fillRemaining"/>
          </span>
          <span v-else-if="!sumOk && remaining < 0" class="remain-hint warn">
            przekroczono o {{ -remaining }}%
          </span>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })
const d = props.data

const ANGLES = [
  { key: 'a_1', label: '30°', color: '#2E7D32' },
  { key: 'a_2', label: '60°', color: '#1565C0' },
  { key: 'a_3', label: '80°', color: '#EF6C00' },
]

function getVal(key) {
  const v = d[key]
  return v != null && typeof v === 'object' ? (v.value ?? null) : (v ?? null)
}

function setVal(key, rawVal) {
  d[key] = rawVal !== '' && rawVal != null ? Number(rawVal) : null
}

const aSum = computed(() => {
  let s = 0
  for (const a of ANGLES) s += Number(getVal(a.key) ?? 0)
  return Math.round(s * 10) / 10
})
const sumOk = computed(() => aSum.value === 100)
const remaining = computed(() => Math.round((100 - aSum.value) * 10) / 10)

function fillRemaining() {
  if (remaining.value <= 0) return
  setVal('a_3', Math.min(100, Number(getVal('a_3') ?? 0) + remaining.value))
}
</script>

<style scoped>
.schem-ad-wrap {
  border: 1px solid rgba(21,101,192,0.18);
  border-radius: 10px;
  padding: 12px;
  display: inline-block;
}
.body--dark .schem-ad-wrap { border-color: rgba(144,202,249,0.22); }

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

.ad-body {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.ad-svg {
  flex: 0 0 30%;
  width: 30%;
  display: block;
}

.ad-table { display: inline-block; }

.ad-head, .ad-row {
  display: grid;
  grid-template-columns: 72px 80px;
  align-items: center;
  gap: 0;
}
.ad-head {
  background: rgba(21,101,192,0.08);
  padding: 4px 6px;
  font-size: 11px;
  font-weight: 700;
  color: #1565C0;
  border-radius: 6px 6px 0 0;
  border: 1px solid rgba(21,101,192,0.18);
  border-bottom: none;
}
.body--dark .ad-head { background: rgba(21,101,192,0.2); color: #90caf9; border-color: rgba(144,202,249,0.2); }
.ad-head span { padding: 0 3px; display: flex; align-items: center; gap: 4px; }
.ad-c-c { text-align: center; }

.ad-row {
  border: 1px solid rgba(21,101,192,0.12);
  border-top: none;
  padding: 3px 6px;
}
.ad-row:last-of-type { border-radius: 0 0 6px 6px; }
.ad-row:nth-child(odd) { background: rgba(21,101,192,0.025); }
.body--dark .ad-row { border-color: rgba(144,202,249,0.15); }
.body--dark .ad-row:nth-child(odd) { background: rgba(21,101,192,0.08); }

.angle-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 24px;
  border-radius: 12px;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  padding: 0 8px;
}

.ad-c-c { padding: 2px 3px; }
.ad-inp { width: 100%; }

.ad-foot {
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
</style>
