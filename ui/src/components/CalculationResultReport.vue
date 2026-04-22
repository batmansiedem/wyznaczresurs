<template>
  <div class="calculation-result-report">

    <!-- ==================== ZABLOKOWANE ==================== -->
    <div v-if="result.is_locked" class="locked-state">
      <div class="locked-icon-wrap">
        <q-icon name="lock" size="40px" color="warning" />
      </div>
      <div class="text-h5 text-weight-bolder q-mb-xs">Wyniki są zablokowane</div>
      <div class="text-body1 text-grey-7 q-mb-lg locked-desc">
        Obliczenie zostało wykonane pomyślnie. Wyświetlenie wyników i wygenerowanie protokołu PDF
        wymaga <span class="text-weight-bold text-primary">{{ result.calculator_definition?.premium_cost ?? 80 }} pkt&nbsp;premium</span>.
      </div>
      <q-btn
        v-if="userPremium >= (result.calculator_definition?.premium_cost ?? 80)"
        label="Odblokuj wyniki"
        icon="lock_open"
        color="primary"
        unelevated
        class="q-px-xl"
        :loading="unlocking"
        @click="$emit('unlock')"
      />
      <q-btn
        v-else
        label="Doładuj punkty premium"
        icon="add_circle"
        color="primary"
        unelevated
        class="q-px-xl"
        to="/pricing"
      />
    </div>

    <!-- ==================== ODBLOKOWANE ==================== -->
    <div v-else>

      <!-- Baner krytyczny -->
      <div v-if="result.output_data?.technical_state_reached" class="technical-banner q-mb-md">
        <q-icon name="report_problem" size="28px" class="flex-shrink-0" />
        <div>
          <div class="text-subtitle2 text-weight-bolder">URZĄDZENIE WYMAGA PRZEGLĄDU SPECJALNEGO</div>
          <div class="text-caption opacity-90 q-mt-xs">Krytyczne wady techniczne powodują natychmiastowe wyczerpanie resursu.</div>
        </div>
      </div>

      <!-- KPI Hero -->
      <div :class="['kpi-hero', kpiClass, 'q-mb-lg']">
        <div class="kpi-main">
          <div class="kpi-label">Wykorzystanie resursu</div>
          <div class="kpi-number">{{ resursValue }}<span class="kpi-pct">%</span></div>
        </div>
        <div class="kpi-divider" />
        <div class="kpi-details">
          <div class="text-weight-bold q-mb-xs kpi-message">
            <span v-html="result.output_data?.resurs_message || '—'"></span>
          </div>
          <div v-if="result.output_data?.resurs_prognoza_dni != null && !result.output_data?.technical_state_reached" class="text-caption kpi-sub">
            Prognoza wyczerpania:
            <strong>{{ formatValue(result.output_data.data_prognoza, { type: 'date' }) }}</strong>
          </div>
          <div class="text-caption kpi-meta q-mt-xs">
            {{ result.calculator_definition?.name || '' }}<template v-if="nrFabryczny"> &middot; nr {{ nrFabryczny }}</template>
          </div>
        </div>
        <q-icon :name="kpiIcon" size="56px" class="kpi-bg-icon" />
      </div>

      <!-- Główna siatka -->
      <div class="row q-col-gutter-lg">

        <!-- LEWA: Parametry wejściowe + wyniki techniczne -->
        <div class="col-12 col-lg-6">

          <!-- Parametry wejściowe -->
          <q-card flat bordered class="overflow-hidden q-mb-lg shadow-1">
            <div class="calc-section-bar">
              <q-icon name="input" size="14px" />
              Parametry wejściowe
            </div>
            <div class="params-table">
              <template v-for="(fieldDef, key) in inputFields" :key="key">
                <div v-if="hasValue(result.input_data?.[key]) && isFieldVisible(fieldDef)" class="params-row">
                  <div class="params-label" v-html="fieldDef.label" />
                  <div class="params-value">{{ formatValue(result.input_data[key], fieldDef) }}</div>
                </div>
              </template>
            </div>
          </q-card>

          <!-- Wyniki obliczeń -->
          <q-card flat bordered class="overflow-hidden shadow-1">
            <div class="calc-section-bar">
              <q-icon name="analytics" size="14px" />
              Wyniki obliczeń
            </div>
            <div class="params-table">
              <template v-for="(fieldDef, key) in outputFields" :key="key">
                <div
                  v-if="hasValue(result.output_data?.[key]) && !SUMMARY_KEYS.includes(key)"
                  class="params-row"
                >
                  <div class="params-label" v-html="fieldDef.label" />
                  <div class="params-value params-value--accent eng-value">{{ formatValue(result.output_data[key], fieldDef) }}</div>
                </div>
              </template>
            </div>
          </q-card>

        </div>

        <!-- PRAWA: Wykresy + PDF -->
        <div class="col-12 col-lg-6">

          <!-- Wykres radialny -->
          <q-card flat bordered class="q-mb-lg shadow-1" style="overflow: visible">
            <div class="calc-section-bar" style="overflow: hidden; border-radius: inherit">
              <q-icon name="donut_large" size="14px" />
              Stopień zużycia resursu
            </div>
            <VueApexCharts
              type="radialBar"
              :options="radialChartOptions"
              :series="[resursValue]"
              height="280"
            />
          </q-card>

          <!-- Wykres słupkowy -->
          <q-card v-if="barChartSeries.length" flat bordered class="q-mb-lg shadow-1">
            <div class="calc-section-bar">
              <q-icon name="bar_chart" size="14px" />
              Zestawienie pracy
            </div>
            <VueApexCharts
              type="bar"
              :options="barChartOptions"
              :series="barChartSeries"
              height="210"
            />
          </q-card>

          <!-- PDF -->
          <q-card v-if="showPdfActions" flat bordered class="shadow-1">
            <div class="calc-section-bar">
              <q-icon name="picture_as_pdf" size="14px" />
              Protokół PDF
            </div>
            <div class="q-pa-md">
              <q-btn
                icon="picture_as_pdf"
                label="Pobierz raport PDF"
                color="primary"
                unelevated
                size="md"
                :loading="downloadingPdf"
                @click="$emit('download-pdf')"
                class="full-width"
              />
            </div>
          </q-card>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, nextTick, ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import VueApexCharts from 'vue3-apexcharts'
import { api } from 'src/boot/axios.js'

const SUMMARY_KEYS = ['resurs_message', 'data_prognoza', 'resurs_prognoza_dni', 'resurs_wykorzystanie', 'technical_state_reached', 'resurs']

const props = defineProps({
  result: { type: Object, required: true },
  userPremium: { type: Number, default: 0 },
  unlocking: { type: Boolean, default: false },
  downloadingPdf: { type: Boolean, default: false },
  showPdfActions: { type: Boolean, default: true },
})

defineEmits(['unlock', 'download-pdf'])

onMounted(async () => {
  await nextTick()
  window.dispatchEvent(new Event('resize'))
})

const $q = useQuasar()

const slug = computed(() => props.result.calculator_definition?.slug || props.result.calculator_slug)

const deviceConfig = ref({})

async function fetchDeviceConfig(s) {
  if (!s) return
  try {
    const res = await api.get(`/calculators/definitions/${s}/schema/`)
    deviceConfig.value = res.data
  } catch (error) {
    console.error('Błąd pobierania konfiguracji urządzenia:', error)
  }
}

watch(slug, (s) => fetchDeviceConfig(s), { immediate: true })

const inputFields = computed(() => deviceConfig.value?.fields || {})
const outputFields = computed(() => deviceConfig.value?.output_fields || {})

const resursValue = computed(() => {
  const v = props.result.output_data?.resurs_wykorzystanie ?? props.result.output_data?.resurs ?? 0
  return parseFloat(v) || 0
})

const kpiClass = computed(() => {
  if (resursValue.value >= 100) return 'kpi-hero--danger'
  if (resursValue.value >= 80) return 'kpi-hero--warn'
  return 'kpi-hero--ok'
})

const kpiIcon = computed(() => {
  if (resursValue.value >= 100) return 'dangerous'
  if (resursValue.value >= 80) return 'warning'
  return 'check_circle'
})

const nrFabryczny = computed(() => {
  const v = props.result.input_data?.nr_fabryczny
  if (!v) return null
  return typeof v === 'object' ? v.value : v
})

function isFieldVisible(fieldDef) {
  const showIf = fieldDef?.show_if
  if (!showIf) return true
  let cur = props.result.input_data?.[showIf.field]
  if (cur !== null && typeof cur === 'object') cur = cur?.value
  const curStr = cur != null ? String(cur) : ''
  const required = showIf.value
  const matched = Array.isArray(required)
    ? required.some(v => curStr.includes(String(v)))
    : curStr === String(required)
  return showIf.negate ? !matched : matched
}

function hasValue(v) {
  if (v === undefined || v === null || v === '-' || v === '') return false
  if (typeof v === 'object') {
    const inner = v.value
    return inner !== undefined && inner !== null && inner !== '-' && inner !== ''
  }
  return true
}

function fmtNum(v) {
  if (v === null || v === undefined || v === '') return '-'
  const n = parseFloat(String(v).replace(',', '.').replace(/\s/g, ''))
  if (isNaN(n)) return String(v)
  if (Number.isInteger(n) && Math.abs(n) < 1e12) return n.toLocaleString('pl-PL')
  // Dla małych wartości współczynników (np. Kd < 0.01) używaj 4 lub 6 miejsc dziesiętnych
  let prec = 2
  if (n !== 0 && Math.abs(n) < 0.01) {
    prec = 4
    if (Math.abs(n) < 0.0001) prec = 6
  }
  return n.toLocaleString('pl-PL', { minimumFractionDigits: prec, maximumFractionDigits: prec })
}

function formatValue(value, fieldDef) {
  if (value === null || value === undefined) return '-'
  if (!fieldDef) return String(value)
  const rawValue = (typeof value === 'object' && value !== null) ? value.value : value
  const unit = (typeof value === 'object' && value !== null) ? value.unit : fieldDef.unit
  switch (fieldDef.type) {
    case 'number': {
      const formatted = fmtNum(rawValue)
      return unit ? `${formatted} ${unit}` : formatted
    }
    case 'percentage': return `${fmtNum(rawValue)}%`
    case 'date': return rawValue ? new Date(rawValue).toLocaleDateString('pl-PL') : '-'
    case 'boolean': return (rawValue === 'Tak' || rawValue === true) ? 'Tak' : 'Nie'
    case 'inspection_status': {
      // Pokaż etykietę wybranej opcji zamiast surowej wartości
      if (!fieldDef.options?.length) return String(rawValue)
      const found = fieldDef.options.find(o => {
        const optVal = typeof o === 'object' ? String(o.value) : String(o)
        return optVal === String(rawValue)
      })
      if (!found) return String(rawValue)
      return typeof found === 'object' ? found.label : found
    }
    default: return String(rawValue)
  }
}

// --- Wykresy ---

const primaryColor = computed(() =>
  getComputedStyle(document.body).getPropertyValue('--q-primary').trim() || '#1565C0'
)

const accentColor = computed(() => {
  if (resursValue.value >= 100) return '#d32f2f'
  if (resursValue.value >= 80) return '#f57c00'
  return primaryColor.value
})

const radialChartOptions = computed(() => ({
  chart: { type: 'radialBar', background: 'transparent' },
  theme: { mode: $q.dark.isActive ? 'dark' : 'light' },
  plotOptions: {
    radialBar: {
      startAngle: -135,
      endAngle: 135,
      hollow: { size: '68%' },
      track: {
        background: $q.dark.isActive ? 'rgba(255,255,255,0.06)' : '#f0f0f0',
        strokeWidth: '67%'
      },
      dataLabels: {
        name: {
          show: true,
          color: $q.dark.isActive ? '#bdbdbd' : '#9e9e9e',
          offsetY: -12,
          fontSize: '12px',
          fontWeight: 600
        },
        value: {
          show: true,
          color: $q.dark.isActive ? '#ffffff' : '#212121',
          offsetY: 10,
          fontSize: '30px',
          fontWeight: 800,
          formatter: (val) => val + '%'
        }
      }
    }
  },
  fill: { type: 'solid', colors: [accentColor.value] },
  stroke: { lineCap: 'round' },
  labels: ['Stopień zużycia']
}))

const barChartSeries = computed(() => {
  const out = props.result?.output_data
  const inp = props.result?.input_data
  if (!out) return []
  const fx = parseFloat(out.F_X ?? 1) || 1
  let val1, val2, limit, unit

  if (out.U_WSK != null) {
    limit = parseFloat(out.U_WSK)
    const isPonowny = inp?.ponowny_resurs === 'Tak'
    if (isPonowny) {
      // Ponowny resurs: pokaż skumulowane cykle (bieżący okres + poprzedni)
      // spójne z wykresem radialnym (resurs_wykorzystanie obejmuje oba okresy)
      const resursPercent = parseFloat(out.resurs_wykorzystanie ?? 0)
      val2 = resursPercent > 0 && limit > 0 ? Math.round(resursPercent / 100 * limit) : 0
      val1 = fx > 1 ? Math.round(val2 / fx * 100) / 100 : val2
    } else {
      // Zwykłe obliczenie — bieżący okres
      val1 = parseFloat(out.ilosc_cykli ?? inp?.ilosc_cykli?.value ?? inp?.ilosc_cykli ?? 0)
      val2 = Math.round(val1 * fx)
    }
    unit = 'cykli'
  } else if (out.T_WSK != null) {
    // Kalkulatory czasowe (motogodziny)
    const tWsk = out.T_WSK
    limit = (tWsk !== null && typeof tWsk === 'object') ? parseFloat(tWsk.value ?? 0) : parseFloat(tWsk ?? 0)

    if (out.czas_uzytkowania_mech != null) {
      // Mechanizmy: czas_uzytkowania_mech już zawiera F_X
      val2 = parseFloat(out.czas_uzytkowania_mech)
      val1 = Math.round(val2 / fx * 100) / 100
    } else if (out.moto_efektywne != null) {
      // podest_ruchomy BUMAR: efektywne motogodziny (bez F_X)
      val1 = parseFloat(out.moto_efektywne)
      val2 = Math.round(val1 * fx * 100) / 100
    } else if (out.ilosc_moto_cal != null) {
      // wozek_specjalizowany (wózek widłowy/ładowarka)
      val1 = parseFloat(out.ilosc_moto_cal)
      val2 = Math.round(val1 * fx * 100) / 100
    } else {
      val1 = parseFloat(inp?.ilosc_mth?.value ?? inp?.ilosc_mth ?? inp?.ilosc_godzin?.value ?? inp?.ilosc_godzin ?? 0)
      val2 = Math.round(val1 * fx * 100) / 100
    }

    const isPonowny = inp?.ponowny_resurs === 'Tak'
    if (isPonowny && limit > 0) {
      const ostatniPct = parseFloat(inp?.ostatni_resurs?.value ?? inp?.ostatni_resurs ?? 0)
      if (ostatniPct > 0) {
        // Dodaj motogodziny odpowiadające procentowi poprzedniego resursu
        const ostatniMth = (ostatniPct / 100) * limit
        val2 += ostatniMth
        // val1 (Bez Fx) też powinno zawierać bazę z poprzedniego resursu? 
        // Tak, dla spójności zestawienia "całościowego"
        val1 += ostatniMth
      }
    }
    unit = 'mth'
    } else {
    return []
  }

  // Fallback: gdy wartości wyszły 0 lub NaN (np. ponowny_resurs=Tak bez nowych danych),
  // wylicz z procentu zużycia — zawsze spójne z wykresem radialnym
  if (limit > 0 && (isNaN(val2) || val2 === 0)) {
    const resursPercent = parseFloat(out.resurs_wykorzystanie ?? 0)
    if (resursPercent > 0) {
      val2 = Math.round(resursPercent / 100 * limit * 100) / 100
      val1 = fx > 1 ? Math.round(val2 / fx * 100) / 100 : val2
    }
  }
  if (isNaN(val1)) val1 = 0
  if (isNaN(val2)) val2 = 0

  return [{
    name: 'Wartość',
    data: [
      { x: `Limit (${unit})`, y: limit },
      { x: 'Bez F\u2093', y: val1 },
      { x: 'Z F\u2093', y: val2 }
    ]
  }]
})

const barChartOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: $q.dark.isActive ? 'dark' : 'light' },
  plotOptions: {
    bar: { horizontal: false, columnWidth: '52%', borderRadius: 6, distributed: true, dataLabels: { position: 'top' } }
  },
  colors: ['#9e9e9e', primaryColor.value, accentColor.value],
  dataLabels: {
    enabled: true,
    formatter: (val) => val.toLocaleString('pl-PL'),
    offsetY: -18,
    style: { fontSize: '11px', colors: [$q.dark.isActive ? '#eeeeee' : '#424242'], fontWeight: 'bold' }
  },
  xaxis: {
    categories: barChartSeries.value[0]?.data.map(d => d.x) || [],
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: { style: { fontWeight: 600, fontSize: '11px' } }
  },
  yaxis: { show: false },
  grid: { show: false },
  tooltip: { y: { formatter: (val) => val.toLocaleString('pl-PL') } },
  legend: { show: false }
}))
</script>

<style scoped>
/* ==============================
   Stan zablokowany
   ============================== */
.locked-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 56px 24px;
}
.locked-icon-wrap {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: rgba(255, 183, 77, 0.1);
  border: 2px solid rgba(255, 183, 77, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}
.locked-desc {
  max-width: 480px;
}
.body--dark .locked-icon-wrap {
  background: rgba(255, 183, 77, 0.07);
}

/* ==============================
   Baner krytyczny
   ============================== */
.technical-banner {
  background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%);
  color: white;
  padding: 14px 20px;
  border-radius: 10px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.flex-shrink-0 { flex-shrink: 0; }

/* ==============================
   KPI Hero block
   ============================== */
.kpi-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 24px 28px;
  border-radius: 14px;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}
.kpi-hero--ok {
  background: linear-gradient(to right, rgba(76, 175, 80, 0.07), transparent);
  border-color: rgba(76, 175, 80, 0.25);
  color: #2e7d32;
}
.kpi-hero--warn {
  background: linear-gradient(to right, rgba(245, 124, 0, 0.07), transparent);
  border-color: rgba(245, 124, 0, 0.25);
  color: #e65100;
}
.kpi-hero--danger {
  background: linear-gradient(to right, rgba(211, 47, 47, 0.07), transparent);
  border-color: rgba(211, 47, 47, 0.25);
  color: #b71c1c;
}
.body--dark .kpi-hero--ok    { background: linear-gradient(to right, rgba(76, 175, 80, 0.12), transparent); color: #66bb6a; }
.body--dark .kpi-hero--warn  { background: linear-gradient(to right, rgba(245, 124, 0, 0.12), transparent); color: #ffa726; }
.body--dark .kpi-hero--danger { background: linear-gradient(to right, rgba(211, 47, 47, 0.12), transparent); color: #ef5350; }

.kpi-main {
  flex-shrink: 0;
}
.kpi-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.65;
  margin-bottom: 2px;
}
.kpi-number {
  font-size: 3.2rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -2px;
  font-family: 'Roboto Mono', monospace;
}
.kpi-pct {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -1px;
  opacity: 0.7;
  margin-left: 2px;
}
.kpi-divider {
  width: 1px;
  height: 56px;
  background: currentColor;
  opacity: 0.15;
  flex-shrink: 0;
}
@media (max-width: 479px) {
  .kpi-divider { display: none; }
}
.kpi-details {
  flex: 1;
  min-width: 180px;
}
.kpi-message {
  font-size: 1rem;
  line-height: 1.35;
}
.kpi-sub {
  opacity: 0.8;
  margin-top: 2px;
}
.kpi-meta {
  opacity: 0.5;
}
.kpi-bg-icon {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.07;
  pointer-events: none;
}

/* ==============================
   Tabela parametrów
   ============================== */
.params-table {
  display: flex;
  flex-direction: column;
}
.params-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px 16px;
  padding: 9px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  font-size: 0.85rem;
}
.params-row:last-child {
  border-bottom: none;
}
.body--dark .params-row {
  border-bottom-color: rgba(255, 255, 255, 0.05);
}
.params-label {
  color: #616161;
  font-weight: 500;
  flex: 1;
  min-width: 120px;
}
.params-value {
  font-weight: 700;
  text-align: right;
  word-break: break-word;
}
.params-value--accent {
  color: var(--q-primary);
}
.body--dark .params-label {
  color: #9e9e9e;
}
</style>
