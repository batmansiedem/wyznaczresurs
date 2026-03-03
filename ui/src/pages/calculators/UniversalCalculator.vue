<template>
  <q-page padding class="container">
    <div v-if="loading && !currentCalculatorDefinition" class="text-center q-pa-md">
      <q-spinner-dots color="primary" size="3em" />
      <div class="q-mt-md">Ładowanie kalkulatora...</div>
    </div>

    <div v-else-if="!currentCalculatorDefinition">
      <q-card flat bordered class="hover-primary">
        <q-card-section>
          <div class="text-h6 text-negative">Błąd: Kalkulator nie został znaleziony.</div>
          <p>Upewnij się, że URL jest poprawny lub kalkulator jest aktywny.</p>
        </q-card-section>
      </q-card>
    </div>

    <template v-else>
      <!-- Nagłówek strony -->
      <div class="calc-page-header q-mb-xl">
        <h1 class="text-h4 text-weight-bolder text-primary q-my-none">
          {{ currentCalculatorDefinition.name }}
        </h1>
        <p class="text-subtitle1 text-grey-7 q-mb-none">{{ currentCalculatorDefinition.description }}</p>
      </div>

      <q-tabs v-model="activeTab" align="left" class="text-primary q-mb-md" active-color="primary" indicator-color="primary" narrow-indicator>
        <q-tab name="calculator" icon="calculate" label="Arkusz obliczeniowy" no-caps />
        <q-tab name="results" icon="history" :label="`Zapisane wyniki (${savedResults.length})`" no-caps />
      </q-tabs>

      <q-tab-panels v-model="activeTab" animated class="bg-transparent">
        <!-- ==================== TAB 1: Arkusz obliczeniowy ==================== -->
        <q-tab-panel name="calculator" class="q-pa-none">
          <q-card flat bordered class="shadow-1 overflow-hidden">
            <q-form @submit="submitCalculation">
              <template v-if="isMechanism && deviceResults.length">
                <div class="calc-section-bar">
                  <q-icon name="link" size="14px" />
                  Wczytaj dane urządzenia
                </div>
                <div class="q-pa-md">
                  <div class="row q-col-gutter-sm items-center">
                    <div class="col">
                      <q-select v-model="selectedDeviceResult" :options="deviceResults" option-label="label" outlined dense color="primary" label="Wczytaj pola z zapisanego resursu urządzenia" clearable />
                    </div>
                    <div class="col-auto">
                      <q-btn label="Wczytaj dane" icon="upload" color="primary" outline dense no-caps :disabled="!selectedDeviceResult" @click="loadFromDevice(selectedDeviceResult)" class="q-px-md" />
                    </div>
                  </div>
                </div>
              </template>

              <template v-for="section in activeSections" :key="section.key">
                <div class="calc-section-bar">
                  <q-icon :name="section.icon" size="14px" />
                  {{ section.label }}
                </div>
                <div class="q-pa-lg">
                  <div class="row q-col-gutter-lg items-start">
                    <template v-for="key in section.fieldKeys" :key="key">
                      <!-- Pola kalkulatora pomocniczego nie są renderowane bezpośrednio -->
                      <template v-if="hasCycleHelper && CYCLE_HELPER_KEYS.includes(key)" />
                      <div v-else-if="currentCalculatorDefinition.fields[key] && isFieldVisible(key)" :class="fieldColClass(currentCalculatorDefinition.fields[key])">
                        <template v-if="currentCalculatorDefinition.fields[key].type === 'diagram'">
                          <SchemLdr v-if="currentCalculatorDefinition.fields[key].svg === 'schemat_ldr'" :data="formData" />
                          <SchemHdr v-else-if="currentCalculatorDefinition.fields[key].svg === 'schemat_hdr'" :data="formData" />
                        </template>
                        <template v-else>
                          <CalculatorField :field="currentCalculatorDefinition.fields[key]" v-model="formData[key]" :units="units" />
                          <!-- Kalkulator pomocniczy cykli — expansion po polu ilosc_cykli -->
                          <q-expansion-item
                            v-if="key === 'ilosc_cykli' && hasCycleHelper"
                            v-model="cycleHelperOpen"
                            dense
                            label="Pomocniczy kalkulator cykli (opcjonalnie)"
                            icon="auto_awesome"
                            header-class="text-primary text-weight-bold"
                            class="cycle-helper-box"
                          >
                            <div class="helper-content">
                              <div class="row q-col-gutter-md">
                                <div class="col-12 col-sm-4">
                                  <q-select
                                    v-model="cycleHelper.tryb_pracy"
                                    label="System pracy"
                                    :options="[
                                      { label: '1-zmianowy', value: 'jednozmianowy' },
                                      { label: '2-zmianowy', value: 'dwuzmianowy' },
                                      { label: '3-zmianowy', value: 'trzyzmianowy' }
                                    ]"
                                    emit-value map-options
                                    outlined dense
                                  />
                                </div>
                                <div class="col-6 col-sm-4">
                                  <q-input
                                    v-model.number="cycleHelper.cykle_zmiana"
                                    label="Cykli na zmianę"
                                    type="number"
                                    outlined dense
                                    input-class="eng-value"
                                    placeholder="np. 50"
                                  />
                                </div>
                                <div class="col-6 col-sm-4">
                                  <q-input
                                    v-model.number="cycleHelper.dni_robocze"
                                    label="Dni rob./rok"
                                    type="number"
                                    outlined dense
                                    input-class="eng-value"
                                    :rules="[val => !val || val <= 366 || 'Max 366 dni']"
                                    lazy-rules
                                  />
                                </div>
                                <div class="col-12">
                                  <div class="preview-banner text-caption q-mb-sm">
                                    <div class="row items-center justify-between">
                                      <span>Wynik dla {{ getLataPracy() }} lat:</span>
                                      <span class="text-h6 text-primary text-weight-bolder eng-value">
                                        {{ calculatePreviewCycles() }}
                                      </span>
                                    </div>
                                  </div>
                                  <q-btn
                                    label="Zastosuj obliczony wynik"
                                    icon="check"
                                    color="primary"
                                    unelevated no-caps
                                    class="full-width"
                                    @click="calculateClientCycles"
                                    :disable="!cycleHelper.cykle_zmiana || cycleHelper.dni_robocze > 366"
                                  />
                                </div>
                              </div>
                            </div>
                          </q-expansion-item>
                        </template>
                      </div>
                    </template>
                  </div>
                </div>
              </template>

              <div class="q-px-lg q-pb-lg">
                <q-separator class="q-mb-lg" />
                <div class="row q-gutter-md">
                  <q-btn label="Oblicz resurs" type="submit" color="primary" :loading="calculating" icon="calculate" unelevated size="lg" class="q-px-xl" />
                  <q-btn label="Wyczyść arkusz" flat color="grey-7" icon="clear" no-caps @click="initializeFormData" />
                </div>
              </div>
            </q-form>

            <div ref="resultsRef"></div>

            <template v-if="calculatedResult">
              <div class="calc-section-bar">
                <q-icon name="assessment" size="14px" />
                Wyniki analizy technicznej
              </div>

              <!-- Wyniki ZABLOKOWANE -->
              <q-card-section v-if="calculatedResult.is_locked" class="q-pa-xl text-center">
                <q-icon name="lock" size="4em" color="warning" class="q-mb-md" />
                <div class="text-h6 text-weight-bold q-mb-sm">Wyniki zablokowane</div>
                <div class="text-body2 text-grey-7 q-mb-lg">
                  Obliczenie zostało wykonane, ale wyświetlenie wyników wymaga
                  <strong>{{ calculatedResult.premium_cost ?? 80 }} punktów premium</strong>.
                  Masz teraz <strong>{{ calculatedResult.remaining_premium ?? userStore.user?.premium ?? 0 }}</strong> pkt.
                </div>
                <div class="row justify-center q-gutter-md">
                  <q-btn
                    v-if="(userStore.user?.premium ?? 0) >= (calculatedResult.premium_cost ?? 80)"
                    label="Odblokuj wyniki"
                    icon="lock_open"
                    color="primary"
                    unelevated
                    no-caps
                    :loading="unlocking"
                    @click="unlockResult"
                  />
                  <q-btn
                    v-else
                    label="Doładuj konto"
                    icon="add_circle"
                    color="primary"
                    unelevated
                    no-caps
                    to="/pricing"
                  />
                </div>
              </q-card-section>

              <!-- Wyniki ODBLOKOWANE -->
              <q-card-section v-else class="q-pa-lg">
                <div class="row q-col-gutter-sm q-mb-lg no-print items-center">
                  <div class="text-subtitle2 text-weight-bold q-mr-md">Akcje:</div>
                  <q-btn icon="picture_as_pdf" label="Pobierz PDF" color="primary" unelevated no-caps :loading="downloadingPdf" @click="downloadPdf" />
                  <q-btn icon="print" label="Drukuj" color="grey-7" flat no-caps @click="printPage" />
                </div>

                <div :class="['kpi-block shadow-1', kpiBlockClass]">
                  <div>
                    <div class="text-overline opacity-70">Zużycie resursu</div>
                    <div class="kpi-number text-h2 text-weight-bolder">
                      {{ calculatedResult.output_data.resurs_wykorzystanie ?? '-' }}%
                    </div>
                  </div>
                  <q-separator vertical inset class="q-mx-md gt-xs" />
                  <div class="col">
                    <div class="text-h6 text-weight-bold">{{ calculatedResult.output_data.resurs_message }}</div>
                    <div v-if="calculatedResult.output_data.resurs_prognoza_dni != null" class="text-subtitle2 opacity-80">
                      Prognoza 100%: <span class="text-weight-bolder">{{ formatOutputValue(calculatedResult.output_data.data_prognoza, {type:'date'}) }}</span>
                    </div>
                  </div>
                </div>

                <div class="row q-col-gutter-xl">
                  <div class="col-12 col-md-6">
                    <div class="section-label">Szczegóły techniczne</div>
                    <q-card flat bordered class="overflow-hidden">
                      <q-list separator dense>
                        <template v-for="(fieldDef, key) in outputFieldDefinitions" :key="key">
                          <q-item v-if="calculatedResult.output_data[key] !== undefined && !['resurs_message','data_prognoza','resurs_prognoza_dni','resurs_wykorzystanie'].includes(key)" class="q-py-sm">
                            <q-item-section><q-item-label class="opacity-70">{{ fieldDef.label }}</q-item-label></q-item-section>
                            <q-item-section side><q-item-label class="text-weight-bold text-primary result-value">{{ formatOutputValue(calculatedResult.output_data[key], fieldDef) }}</q-item-label></q-item-section>
                          </q-item>
                        </template>
                      </q-list>
                    </q-card>
                  </div>
                  <div class="col-12 col-md-6 text-center">
                    <div class="section-label">Wykres wykorzystania</div>
                    <VueApexCharts type="pie" :options="pieChartOptions" :series="pieChartSeries" height="250" />
                  </div>
                </div>
              </q-card-section>
            </template>
          </q-card>
        </q-tab-panel>

        <!-- ==================== TAB 2: Zapisane wyniki ==================== -->
        <q-tab-panel name="results" class="q-pa-none">
          <q-card flat bordered v-if="loadingResults" class="q-pa-xl text-center shadow-1">
            <q-spinner-dots color="primary" size="3em" />
          </q-card>

          <q-card flat bordered v-else-if="!savedResults.length" class="q-pa-xl text-center shadow-1 hover-primary">
            <q-icon name="history" size="4em" color="grey-4" />
            <div class="text-h6 text-grey-7 q-mt-md">Brak zapisanych wyników.</div>
          </q-card>

          <template v-else>
            <q-card flat bordered class="shadow-1 overflow-hidden">
              <q-table :rows="savedResults" :columns="savedResultsColumns" row-key="id" flat :pagination="{ rowsPerPage: 10 }" @row-click="(evt, row) => selectSavedResult(row)">
                <template v-slot:body-cell-actions="props">
                  <q-td :props="props" class="q-gutter-x-xs text-center">
                    <q-btn icon="picture_as_pdf" color="primary" flat dense @click.stop="downloadPdf(props.row.id)" />
                    <q-btn icon="upload" color="primary" flat dense @click.stop="loadResultToForm(props.row)" />
                    <q-btn icon="delete" color="negative" flat dense @click.stop="confirmDelete(props.row)" />
                  </q-td>
                </template>
              </q-table>
            </q-card>

            <q-card v-if="selectedSavedResult" flat bordered class="q-mt-lg shadow-5 border-primary overflow-hidden">
              <q-card-section class="row items-center bg-primary text-white">
                <div class="text-h6">Szczegóły z dnia {{ new Date(selectedSavedResult.created_at).toLocaleDateString() }}</div>
                <q-space />
                <q-btn flat dense icon="close" @click="selectedSavedResult = null" color="white" />
              </q-card-section>
              <q-card-section class="q-pa-lg">
                <div class="row q-col-gutter-lg">
                  <div class="col-12 col-md-6">
                    <div class="text-overline text-primary q-mb-md">Parametry wejściowe</div>
                    <q-list dense separator bordered class="rounded-borders">
                      <q-item v-for="(fieldDef, key) in inputFieldDefinitions" :key="key">
                        <q-item-section><q-item-label caption>{{ fieldDef.label }}</q-item-label></q-item-section>
                        <q-item-section side><q-item-label class="text-weight-bold">{{ formatSavedInputValue(selectedSavedResult.input_data[key]) }}</q-item-label></q-item-section>
                      </q-item>
                    </q-list>
                  </div>
                  <div class="col-12 col-md-6 text-center">
                    <div class="text-overline text-primary q-mb-md">Wynik analizy</div>
                    <div class="kpi-number text-h2 text-weight-bolder text-primary q-mb-md">
                      {{ (selectedSavedResult.output_data.resurs_wykorzystanie ?? selectedSavedResult.output_data.resurs) }}%
                    </div>
                    <VueApexCharts type="pie" :options="pieChartOptions" :series="selectedPieChartSeries" height="250" />
                  </div>
                </div>
              </q-card-section>
            </q-card>
          </template>
        </q-tab-panel>
      </q-tab-panels>
    </template>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar, Notify, Dialog } from 'quasar'
import VueApexCharts from 'vue3-apexcharts'
import CalculatorField from 'components/CalculatorField.vue'
import SchemLdr from 'components/SchemLdr.vue'
import SchemHdr from 'components/SchemHdr.vue'
import calculatorFields from 'src/data/calculator_fields.json'
import calculatorOutputFields from 'src/data/calculator_output_fields.json'
import { useUserStore } from 'stores/user-store'

const route = useRoute()
const $q = useQuasar()
const userStore = useUserStore()

const resultsRef = ref(null)
const activeTab = ref('calculator')
const formData = ref({})
const calculatedResult = ref(null)
const units = ref({})
const loading = ref(true)
const calculating = ref(false)
const downloadingPdf = ref(false)
const unlocking = ref(false)

const savedResults = ref([])
const loadingResults = ref(false)
const selectedSavedResult = ref(null)

const deviceResults = ref([])
const selectedDeviceResult = ref(null)

const MECH_PARENT_DEVICES = {
  mech_podnoszenia: ['suwnica', 'wciagarka', 'wciagnik', 'zuraw'],
  mech_jazdy_suwnicy: ['suwnica'],
  mech_jazdy_wciagarki: ['wciagarka'],
  mech_jazdy_zurawia: ['zuraw'],
  mech_zmiany_wysiegu: ['zuraw'],
  mech_zmiany_obrotu: ['zuraw'],
}

const isMechanism = computed(() => !!MECH_PARENT_DEVICES[calculatorSlug.value])
const calculatorSlug = computed(() => route.params.slug)
const currentCalculatorDefinition = computed(() => calculatorFields[calculatorSlug.value] || null)
const inputFieldDefinitions = computed(() => currentCalculatorDefinition.value?.fields || null)
const outputFieldDefinitions = computed(() => calculatorOutputFields[calculatorSlug.value]?.fields || null)

const activeSections = computed(() => {
  const calc = currentCalculatorDefinition.value
  if (!calc?.fields) return []
  return (calc.sections || [])
    .map(s => ({ key: s.id, label: s.title, icon: s.icon, fieldKeys: s.fields.filter(k => calc.fields[k]) }))
    .filter(s => s.fieldKeys.length > 0)
})

const savedResultsColumns = [
  { name: 'created_at', label: 'Data', align: 'left', field: 'created_at', sortable: true, format: val => new Date(val).toLocaleString() },
  { name: 'resurs', label: 'Zużycie [%]', align: 'left', field: row => `${row.output_data?.resurs_wykorzystanie ?? row.output_data?.resurs ?? 0}%`, sortable: true },
  { name: 'actions', label: 'Akcje', align: 'center' }
]

// Pola kalkulatora pomocniczego cykli — filtrowane z renderowania sekcji
const CYCLE_HELPER_KEYS = ['tryb_pracy', 'cykle_zmiana', 'dni_robocze']
const hasCycleHelper = computed(() =>
  CYCLE_HELPER_KEYS.every(k => currentCalculatorDefinition.value?.fields[k])
)
const cycleHelperOpen = ref(false)
const cycleHelper = reactive({ tryb_pracy: 'jednozmianowy', cykle_zmiana: null, dni_robocze: 250 })

function getLataPracy() {
  const lata = formData.value.lata_pracy
  if (typeof lata === 'object' && lata !== null) return parseFloat(lata.value) || 1
  return parseFloat(lata) || 1
}

function calculatePreviewCycles() {
  const shifts = { jednozmianowy: 1, dwuzmianowy: 2, trzyzmianowy: 3 }
  const lata = getLataPracy()
  const val = Math.round((cycleHelper.cykle_zmiana || 0) * (shifts[cycleHelper.tryb_pracy] || 1) * (cycleHelper.dni_robocze || 0) * lata)
  return val.toLocaleString()
}

function calculateClientCycles() {
  const shifts = { jednozmianowy: 1, dwuzmianowy: 2, trzyzmianowy: 3 }
  const lata = getLataPracy()
  const cykli = Math.round((cycleHelper.cykle_zmiana || 0) * (shifts[cycleHelper.tryb_pracy] || 1) * (cycleHelper.dni_robocze || 0) * lata)
  formData.value.ilosc_cykli = { value: cykli, unit: formData.value.ilosc_cykli?.unit || 'cykl' }
  cycleHelperOpen.value = false
}

function fieldColClass(field) {
  if (['textarea', 'radio', 'diagram', 'gnp_selector', 'inspection_status'].includes(field.type)) return 'col-12'
  return 'col-12 col-sm-6'
}

watch(currentCalculatorDefinition, (newDef) => {
  if (newDef) {
    initializeFormData()
    calculatedResult.value = null
    selectedSavedResult.value = null
    savedResults.value = []
    fetchSavedResults()
    fetchDeviceResults()
  }
}, { immediate: true })

function makeChartData(outputData) {
  if (!outputData) return { pie: [0, 100], bar: [] }
  const utilization = parseFloat(outputData.resurs_wykorzystanie ?? outputData.resurs)
  return { pie: [utilization, 100 - utilization], bar: [] }
}

const pieChartOptions = computed(() => ({
  chart: { type: 'pie', background: 'transparent' },
  theme: { mode: $q.dark.isActive ? 'dark' : 'light' },
  labels: ['Zużycie', 'Pozostało'],
  colors: [getComputedStyle(document.body).getPropertyValue('--q-primary') || '#1565C0', '#B0BEC5'],
  legend: { position: 'bottom' },
  stroke: { show: false }
}))

const pieChartSeries = computed(() => makeChartData(calculatedResult.value?.output_data).pie)
const selectedPieChartSeries = computed(() => makeChartData(selectedSavedResult.value?.output_data).pie)

const kpiBlockClass = computed(() => {
  const v = parseFloat(calculatedResult.value?.output_data?.resurs_wykorzystanie ?? 0)
  if (v >= 100) return 'kpi-block-danger'
  if (v >= 80) return 'kpi-block-warn'
  return 'kpi-block-ok'
})

function formatOutputValue(value, fieldDef) {
  if (value === null || value === undefined) return '-'
  if (fieldDef.type === 'percentage') return `${value}%`
  if (fieldDef.type === 'date') return new Date(value).toLocaleDateString()
  if (fieldDef.type === 'number' && fieldDef.unit) return `${value} ${fieldDef.unit}`
  return String(value)
}

function formatSavedInputValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object' && value.value !== undefined) return `${value.value}${value.unit ? ' ' + value.unit : ''}`
  return String(value)
}

async function fetchUnits() {
  try {
    const res = await api.get('/calculators/units/')
    units.value = res.data.reduce((acc, u) => {
      if (!acc[u.unit_type]) acc[u.unit_type] = []
      acc[u.unit_type].push(u)
      return acc
    }, {})
  } catch (error) {
    console.error(error)
  }
}

function initializeFormData() {
  if (!currentCalculatorDefinition.value?.fields) return
  const data = {}
  for (const key in currentCalculatorDefinition.value.fields) {
    const f = currentCalculatorDefinition.value.fields[key]
    if (f.type === 'diagram') continue
    if (f.type === 'number') {
      data[key] = { value: f.default_value ?? null, unit: f.default_unit || units.value[f.unit_type]?.[0]?.symbol || null }
    } else if (f.type === 'inspection_status' && f.options?.length) {
      // Domyślnie ostatnia opcja ("Nie dotyczy")
      const last = f.options[f.options.length - 1]
      data[key] = f.default_value ?? (typeof last === 'object' ? last.value : last)
    } else {
      data[key] = f.default_value ?? null
    }
  }
  formData.value = data
}

function isFieldVisible(key) {
  const f = currentCalculatorDefinition.value?.fields[key]
  if (!f?.show_if) return true
  const cur = formData.value[f.show_if.field]
  const matched = Array.isArray(f.show_if.value)
    ? f.show_if.value.some(v => String(cur ?? '').includes(v))
    : cur === f.show_if.value
  return f.show_if.negate ? !matched : matched
}

async function fetchSavedResults() {
  loadingResults.value = true
  try {
    const res = await api.get('/calculators/results/for_calculator/', { params: { slug: calculatorSlug.value } })
    savedResults.value = res.data
  } catch (error) {
    console.error(error)
  } finally { loadingResults.value = false }
}

async function fetchDeviceResults() {
  const parentSlugs = MECH_PARENT_DEVICES[calculatorSlug.value] || []
  if (!parentSlugs.length) return
  const all = []
  for (const slug of parentSlugs) {
    try {
      const res = await api.get('/calculators/results/for_calculator/', { params: { slug } })
      all.push(...res.data.map(r => ({ ...r, label: `${calculatorFields[slug]?.name || slug} — ${new Date(r.created_at).toLocaleDateString()}` })))
    } catch (error) {
      console.error(error)
    }
  }
  deviceResults.value = all
}

function loadFromDevice(result) {
  if (!result?.input_data) return
  Object.keys(currentCalculatorDefinition.value.fields).forEach(k => { if (k in result.input_data) formData.value[k] = result.input_data[k] })
  Notify.create({ type: 'positive', message: 'Wczytano dane urządzenia.' })
}

function selectSavedResult(row) { selectedSavedResult.value = selectedSavedResult.value?.id === row.id ? null : row }
function loadResultToForm(res) { formData.value = JSON.parse(JSON.stringify(res.input_data)); activeTab.value = 'calculator' }

function confirmDelete(row) {
  Dialog.create({ title: 'Usuń wynik', message: 'Czy na pewno?', cancel: true, persistent: true }).onOk(async () => {
    try {
      await api.delete(`/calculators/results/${row.id}/`)
      savedResults.value = savedResults.value.filter(r => r.id !== row.id)
      Notify.create({ type: 'positive', message: 'Usunięto.' })
    } catch (error) {
      console.error(error)
    }
  })
}

async function submitCalculation() {
  calculating.value = true
  try {
    const res = await api.post(`/calculators/definitions/${calculatorSlug.value}/calculate/`, { input_data: formData.value })
    calculatedResult.value = res.data
    if (res.data.remaining_premium !== undefined && userStore.user) {
      userStore.user.premium = res.data.remaining_premium
    }
    await nextTick()
    resultsRef.value?.scrollIntoView({ behavior: 'smooth' })
    fetchSavedResults()
    if (res.data.is_locked) {
      Notify.create({ type: 'warning', message: 'Obliczono, ale wyniki są zablokowane — brak punktów premium.' })
    } else {
      Notify.create({ type: 'positive', message: 'Obliczono!' })
    }
  } catch (error) {
    console.error(error)
  } finally { calculating.value = false }
}

async function unlockResult() {
  if (!calculatedResult.value?.result_id) return
  unlocking.value = true
  try {
    const res = await api.post(`/calculators/results/${calculatedResult.value.result_id}/unlock/`)
    calculatedResult.value = { ...calculatedResult.value, ...res.data }
    if (res.data.remaining_premium !== undefined && userStore.user) {
      userStore.user.premium = res.data.remaining_premium
    }
    fetchSavedResults()
    Notify.create({ type: 'positive', message: 'Wyniki odblokowane pomyślnie!' })
  } catch (error) {
    Notify.create({ type: 'negative', message: error.response?.data?.detail || error.response?.data?.[0] || 'Błąd odblokowania.' })
  } finally { unlocking.value = false }
}

function printPage() { window.print() }
async function downloadPdf(id = null) {
  const rid = id ?? calculatedResult.value?.result_id
  if (!rid) return
  downloadingPdf.value = true
  try {
    const res = await api.get(`/calculators/results/${rid}/pdf/`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a'); a.href = url; a.download = `resurs_${calculatorSlug.value}.pdf`; a.click()
  } catch (error) {
    console.error(error)
  } finally { downloadingPdf.value = false }
}

onMounted(async () => { await fetchUnits(); loading.value = false })
</script>

<style scoped>
.border-primary { border: 1px solid var(--q-primary); }
</style>
