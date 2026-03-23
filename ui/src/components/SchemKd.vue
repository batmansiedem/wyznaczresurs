<template>
  <div class="schem-kd-wrap">

    <!-- Nagłówek z formułą -->
    <div class="schem-hd">
      <span class="schem-title">Współczynnik widma obciążeń — <em>K<sub>d</sub></em></span>
      <span class="schem-formula">= Σ [ c<sub>i</sub>/100 · (q<sub>i</sub>/q<sub>max</sub>)<sup>3</sup> ]</span>
    </div>

    <!-- Ciało: SVG po lewej, tabela po prawej -->
    <div class="kd-body">

    <!-- SVG: suwnica pomostowa — ładunek Q podnoszony za środek -->
    <svg viewBox="0 0 320 320" xmlns="http://www.w3.org/2000/svg"
         class="kd-svg">

      <!-- ═══ Szyny (tory suwnicy) — dwie kolumny ═══ -->
      <!-- Lewa kolumna / słup -->
      <rect x="20" y="30" width="18" height="220" rx="3"
            fill="rgba(21,101,192,0.1)" stroke="#1565C0" stroke-width="2.5"/>
      <!-- Ukośne stężenia lewe -->
      <line x1="20" y1="80"  x2="38" y2="110" stroke="#1565C0" stroke-width="1.5" opacity="0.45"/>
      <line x1="20" y1="140" x2="38" y2="170" stroke="#1565C0" stroke-width="1.5" opacity="0.45"/>
      <line x1="20" y1="200" x2="38" y2="230" stroke="#1565C0" stroke-width="1.5" opacity="0.45"/>
      <!-- Prawa kolumna / słup -->
      <rect x="282" y="30" width="18" height="220" rx="3"
            fill="rgba(21,101,192,0.1)" stroke="#1565C0" stroke-width="2.5"/>
      <!-- Ukośne stężenia prawe -->
      <line x1="300" y1="80"  x2="282" y2="110" stroke="#1565C0" stroke-width="1.5" opacity="0.45"/>
      <line x1="300" y1="140" x2="282" y2="170" stroke="#1565C0" stroke-width="1.5" opacity="0.45"/>
      <line x1="300" y1="200" x2="282" y2="230" stroke="#1565C0" stroke-width="1.5" opacity="0.45"/>

      <!-- Podstawy słupów -->
      <rect x="10"  y="248" width="38" height="10" rx="2" fill="#1565C0" opacity="0.7"/>
      <rect x="272" y="248" width="38" height="10" rx="2" fill="#1565C0" opacity="0.7"/>

      <!-- ═══ Szyny górne (na których jedzie most) ═══ -->
      <rect x="10"  y="26" width="38" height="8" rx="2" fill="#1565C0"/>
      <rect x="272" y="26" width="38" height="8" rx="2" fill="#1565C0"/>

      <!-- ═══ Most suwnicy (belka jezdna) ═══ -->
      <!-- Belka górna dwuteownika -->
      <rect x="38" y="34" width="244" height="10" rx="2"
            fill="rgba(21,101,192,0.15)" stroke="#1565C0" stroke-width="2.5"/>
      <!-- Środnik dwuteownika -->
      <rect x="155" y="44" width="10" height="24" fill="rgba(21,101,192,0.2)" stroke="#1565C0" stroke-width="1.5"/>
      <!-- Belka dolna dwuteownika -->
      <rect x="38" y="68" width="244" height="10" rx="2"
            fill="rgba(21,101,192,0.15)" stroke="#1565C0" stroke-width="2.5"/>

      <!-- ═══ Wózek (jeździ po moście) — na środku ═══ -->
      <rect x="138" y="55" width="44" height="22" rx="3"
            fill="rgba(21,101,192,0.18)" stroke="#1565C0" stroke-width="2"/>
      <!-- Koła wózka (4 kółka) -->
      <circle cx="148" cy="54" r="5" fill="white" stroke="#1565C0" stroke-width="2"/>
      <circle cx="172" cy="54" r="5" fill="white" stroke="#1565C0" stroke-width="2"/>
      <!-- Bęben / silnik wciągnika -->
      <rect x="148" y="60" width="24" height="14" rx="2"
            fill="rgba(21,101,192,0.3)" stroke="#1565C0" stroke-width="1.5"/>
      <circle cx="160" cy="67" r="5" fill="#1565C0" opacity="0.6"/>

      <!-- ═══ Lina / cięgno — od bębna do haka ═══ -->
      <line x1="160" y1="77" x2="160" y2="172"
            stroke="#1565C0" stroke-width="2" stroke-dasharray="5,3"/>

      <!-- ═══ Hak — J-kształt wystarczająco szeroki by ring siedział wewnątrz:
           szyjka (x=160) to lewa ściana, ciało haka (x≈172) to prawa ściana,
           ring (cx=168) opiera się między nimi jak w realu ═══ -->
      <path d="M160,172 L160,183 C180,195 184,205 181,190 C178,176 167,172 166,179"
            fill="none" stroke="#1565C0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>

      <!-- ═══ Śruba oczkowa — ring siedzi wewnątrz haka, dolna krawędź na powierzchni ładunku ═══ -->
      <circle cx="168" cy="191" r="5"
              fill="rgba(21,101,192,0.08)" stroke="#1565C0" stroke-width="1.5"/>

      <!-- ═══ Ładunek ═══ -->
      <rect x="96" y="196" width="128" height="72" rx="5"
            fill="rgba(21,101,192,0.1)" stroke="#1565C0" stroke-width="3"/>
      <!-- Kreskowanie ładunku -->
      <line x1="108" y1="196" x2="96"  y2="212" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="124" y1="196" x2="96"  y2="230" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="140" y1="196" x2="96"  y2="248" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="156" y1="196" x2="110" y2="268" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="172" y1="196" x2="126" y2="268" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="188" y1="196" x2="142" y2="268" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="204" y1="196" x2="158" y2="268" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>
      <line x1="220" y1="196" x2="174" y2="268" stroke="#1565C0" stroke-width="1.2" opacity="0.3"/>

      <!-- Etykieta Q -->
      <text x="160" y="232" fill="#1565C0" font-family="'Segoe UI',Roboto,sans-serif"
            font-size="22" font-weight="800" text-anchor="middle" dominant-baseline="middle">Q</text>

      <!-- ═══ Pionowa strzałka Q — siła ciężkości ładunku ═══ -->
      <line x1="160" y1="272" x2="160" y2="296"
            stroke="#1565C0" stroke-width="2.5"/>
      <polygon points="154,292 166,292 160,304" fill="#1565C0"/>

      <!-- ═══ Linia środka (oś symetrii) ═══ -->
      <line x1="160" y1="20" x2="160" y2="75"
            stroke="#1565C0" stroke-width="1" stroke-dasharray="6,4" opacity="0.3"/>


    </svg>

    <!-- Tabela 5 klas -->
    <div class="kd-table">
      <div class="kd-head">
        <span class="kd-c-no">Klasa</span>
        <span class="kd-c-q">
          q<sub>i</sub>
          <q-select
            v-model="massUnit"
            :options="MASS_UNITS"
            dense outlined hide-bottom-space
            class="unit-sel"
            @update:model-value="applyUnit"
          />
        </span>
        <span class="kd-c-c">c<sub>i</sub> [%]</span>
      </div>
      <div v-for="i in 5" :key="i" class="kd-row">
        <span class="kd-c-no">
          <span class="cls-dot">{{ i }}</span>
        </span>
        <span class="kd-c-q">
          <q-input
            :model-value="getNum('q_' + i)"
            @update:model-value="v => setQ('q_' + i, v)"
            type="number" dense outlined hide-bottom-space
            :min="0" step="0.1" input-style="text-align:right;padding:0 4px"
            class="kd-inp"
          />
        </span>
        <span class="kd-c-c">
          <q-input
            :model-value="getNum('c_' + i)"
            @update:model-value="v => setNum('c_' + i, v)"
            type="number" dense outlined hide-bottom-space
            :min="0" :max="100" step="1" input-style="text-align:right;padding:0 4px"
            :color="cSumOk ? 'positive' : 'warning'"
            class="kd-inp"
          />
        </span>
      </div>
      <div class="kd-foot">
        <q-chip dense :color="cSumOk ? 'positive' : 'warning'"
                text-color="white" icon="functions" size="sm">
          Σ c = {{ cSum }}%
        </q-chip>
        <span v-if="!cSumOk && cRemaining > 0" class="remain-hint">
          pozostało {{ cRemaining }}%
          <q-btn flat dense size="xs" color="primary" no-caps
                 label="dopełnij →" @click="fillRemaining"/>
        </span>
        <span v-else-if="!cSumOk && cRemaining < 0" class="remain-hint warn">
          przekroczono o {{ -cRemaining }}%
        </span>
      </div>
    </div>

    </div><!-- /kd-body -->
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })
const emit = defineEmits(['kg-to-t'])
const d = props.data

const MASS_UNITS = ['kg', 't']

// Odczytaj jednostkę z istniejących danych lub ustaw domyślnie kg
const initUnit = (() => {
  for (let i = 1; i <= 5; i++) {
    const v = d[`q_${i}`]
    if (v != null && typeof v === 'object' && v.unit) return v.unit
  }
  return 'kg'
})()
const massUnit = ref(initUnit)

// Flaga: true gdy zmiana jednostki pochodzi od rodzica (applyUnit) — nie emitujemy wtedy kg-to-t
let _parentControlled = false

// Gdy user zmieni kg→t w SchemKd, powiadom rodzica (UniversalCalculator)
watch(massUnit, (newVal, oldVal) => {
  if (_parentControlled) return
  if (oldVal === 'kg' && newVal === 't') emit('kg-to-t')
})

function getNum(key) {
  const v = d[key]
  return v != null && typeof v === 'object' ? (v.value ?? null) : (v ?? null)
}

// q_i zawsze zapisywane z jednostką {value, unit}
function setQ(key, rawVal) {
  const num = rawVal !== '' && rawVal != null ? Number(rawVal) : null
  d[key] = { value: num, unit: massUnit.value }
}

// c_i to procenty — bez jednostki
function setNum(key, rawVal) {
  const num = rawVal !== '' && rawVal != null ? Number(rawVal) : null
  const existing = d[key]
  d[key] = existing != null && typeof existing === 'object'
    ? { ...existing, value: num } : num
}

// Przy zmianie jednostki zaktualizuj unit we wszystkich q_i (wartości bez konwersji)
// Wywołane z rodzica — ustawia flagę żeby watcher nie emitował kg-to-t (zapobiega podwójnemu dialogowi)
function applyUnit(newUnit) {
  _parentControlled = true
  massUnit.value = newUnit
  for (let i = 1; i <= 5; i++) {
    const v = d[`q_${i}`]
    if (v != null && typeof v === 'object') {
      d[`q_${i}`] = { ...v, unit: newUnit }
    } else if (v != null) {
      d[`q_${i}`] = { value: v, unit: newUnit }
    }
  }
  // Reset po następnym cyklu reaktywności — watcher już się wykonał z flagą
  nextTick(() => { _parentControlled = false })
}

// Eksponuj applyUnit dla rodzica (gdy "Zmień wszędzie" z innego pola)
defineExpose({ applyUnit })

const cSum = computed(() => {
  let s = 0
  for (let i = 1; i <= 5; i++) s += Number(getNum(`c_${i}`) ?? 0)
  return Math.round(s * 10) / 10
})
const cSumOk = computed(() => cSum.value === 100)
const cRemaining = computed(() => Math.round((100 - cSum.value) * 10) / 10)

function fillRemaining() {
  if (cRemaining.value <= 0) return
  const cur = Number(getNum('c_5') ?? 0)
  setNum('c_5', Math.min(100, cur + cRemaining.value))
}
</script>

<style scoped>
.schem-kd-wrap {
  border: 1px solid rgba(21,101,192,0.18);
  border-radius: 10px;
  padding: 12px;
  display: inline-block;
}
.body--dark .schem-kd-wrap { border-color: rgba(144,202,249,0.22); }

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

.kd-body {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.kd-svg {
  flex: 0 0 30%;
  width: 30%;
  display: block;
}

.kd-table { display: inline-block; }

.kd-head, .kd-row {
  display: grid;
  grid-template-columns: 52px 110px 80px;
  align-items: center;
  gap: 0;
}
.kd-head {
  background: rgba(21,101,192,0.08);
  padding: 4px 6px;
  font-size: 11px;
  font-weight: 700;
  color: #1565C0;
  border-radius: 6px 6px 0 0;
  border: 1px solid rgba(21,101,192,0.18);
  border-bottom: none;
}
.body--dark .kd-head { background: rgba(21,101,192,0.2); color: #90caf9; border-color: rgba(144,202,249,0.2); }
.kd-head span {
  padding: 0 3px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.kd-c-q, .kd-c-c { text-align: center; }

.unit-sel {
  width: 58px;
  font-size: 11px;
}
/* Zmniejsz padding wewnątrz selecta jednostki */
.unit-sel :deep(.q-field__control) { min-height: 24px; padding: 0 4px; }
.unit-sel :deep(.q-field__native) { min-height: 24px; font-size: 11px; padding: 0; }

.kd-row {
  border: 1px solid rgba(21,101,192,0.12);
  border-top: none;
  padding: 3px 6px;
}
.kd-row:last-of-type { border-radius: 0 0 6px 6px; }
.kd-row:nth-child(odd) { background: rgba(21,101,192,0.025); }
.body--dark .kd-row { border-color: rgba(144,202,249,0.15); }
.body--dark .kd-row:nth-child(odd) { background: rgba(21,101,192,0.08); }

.cls-dot {
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

.kd-c-q, .kd-c-c { padding: 2px 3px; }
.kd-inp { width: 100%; }

.kd-foot {
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
