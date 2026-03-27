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
        <p class="text-subtitle1 opacity-80 q-mb-none">{{ currentCalculatorDefinition.description }}</p>
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
                          <SchemKd v-else-if="currentCalculatorDefinition.fields[key].svg === 'schemat_kd'" ref="schemKdRef" :data="formData" @kg-to-t="onSchemKdKgToT" />
                          <SchemAd v-else-if="currentCalculatorDefinition.fields[key].svg === 'schemat_ad'" :data="formData" />
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
                  <q-btn :label="`Oblicz wyznaczenie resursu (${currentCost} pkt)`" type="submit" color="primary" :loading="calculating" icon="calculate" unelevated size="lg" class="q-px-xl" />
                  <q-btn label="Wyczyść arkusz" flat color="grey-7" icon="clear" no-caps @click="initializeFormData" />
                </div>
              </div>
            </q-form>

            <div ref="resultsRef"></div>

            <template v-if="calculatedResult">
              <div class="calc-section-bar q-mt-xl">
                <q-icon name="assessment" size="18px" />
                Wyniki analizy technicznej i resursu
              </div>

              <q-card-section class="q-pa-lg">
                <CalculationResultReport
                  :result="calculatedResult"
                  :user-premium="userStore.user?.premium ?? 0"
                  :unlocking="unlocking"
                  :downloading-pdf="downloadingPdf"
                  :logos="userStore.user?.logos"
                  v-model:selected-logo-id="selectedLogoId"
                  @unlock="unlockResult"
                  @download-pdf="downloadPdf()"
                />
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
            <div class="text-h6 opacity-80 q-mt-md">Brak zapisanych wyników.</div>
          </q-card>

          <template v-else>
            <q-card flat bordered class="shadow-1 overflow-hidden">
              <q-table :rows="savedResults" :columns="savedResultsColumns" row-key="id" flat :pagination="{ rowsPerPage: 10 }" @row-click="(evt, row) => selectSavedResult(row)">
                <template v-slot:body-cell-resurs="props">
                  <q-td :props="props">
                    <span v-if="props.row.is_locked" class="text-grey-6">—</span>
                    <span v-else>{{ props.row.output_data?.resurs_wykorzystanie ?? props.row.output_data?.resurs ?? 0 }}%</span>
                  </q-td>
                </template>
                <template v-slot:body-cell-status="props">
                  <q-td :props="props" class="text-center">
                    <q-badge v-if="props.row.is_locked" color="warning" outline>
                      <q-icon name="lock" size="12px" class="q-mr-xs" />Zablokowany
                    </q-badge>
                    <q-badge v-else color="positive" outline>
                      <q-icon name="check" size="12px" class="q-mr-xs" />Odblokowany
                    </q-badge>
                  </q-td>
                </template>
                <template v-slot:body-cell-actions="props">
                  <q-td :props="props" class="q-gutter-x-xs text-center">
                    <template v-if="props.row.is_locked">
                      <q-btn
                        v-if="(userStore.user?.premium ?? 0) >= (props.row.calculator_definition?.premium_cost ?? 0)"
                        icon="lock_open" color="primary" flat dense :loading="unlocking"
                        @click.stop="unlockSavedResult(props.row)"
                      >
                        <q-tooltip>Odblokuj wyniki</q-tooltip>
                      </q-btn>
                      <q-btn v-else icon="add_circle" color="warning" flat dense to="/pricing">
                        <q-tooltip>Doładuj konto (brak punktów)</q-tooltip>
                      </q-btn>
                    </template>
                    <template v-else>
                      <q-btn icon="picture_as_pdf" color="primary" flat dense @click.stop="downloadPdf(props.row.id)">
                        <q-tooltip>Pobierz PDF</q-tooltip>
                      </q-btn>
                    </template>
                    <q-btn icon="upload" color="primary" flat dense @click.stop="loadResultToForm(props.row)">
                      <q-tooltip>Wczytaj dane do formularza</q-tooltip>
                    </q-btn>
                    <q-btn icon="delete" color="negative" flat dense @click.stop="confirmDelete(props.row)">
                      <q-tooltip>Usuń</q-tooltip>
                    </q-btn>
                  </q-td>
                </template>
              </q-table>
            </q-card>

            <q-card v-if="selectedSavedResult" flat bordered class="q-mt-lg shadow-5 border-primary overflow-hidden">
              <q-card-section class="row items-center bg-primary text-white">
                <div class="text-subtitle1 text-weight-bolder">
                  Urządzenie nr fabr. {{ getSavedFieldValue(selectedSavedResult.input_data, 'nr_fabryczny') || '?' }} 
                  &nbsp;•&nbsp; 
                  Obliczenia z dnia {{ new Date(selectedSavedResult.created_at).toLocaleDateString('pl-PL') }}
                </div>
                <q-space />
                <q-btn flat dense icon="close" @click="selectedSavedResult = null" color="white" />
              </q-card-section>
              <q-card-section class="q-pa-lg">
                <CalculationResultReport
                  :result="selectedSavedResult"
                  :user-premium="userStore.user?.premium ?? 0"
                  :unlocking="unlocking"
                  :downloading-pdf="downloadingPdf"
                  :logos="userStore.user?.logos"
                  v-model:selected-logo-id="selectedLogoId"
                  @unlock="unlockSavedResult(selectedSavedResult)"
                  @download-pdf="downloadPdf(selectedSavedResult.id)"
                />
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
import CalculatorField from 'components/CalculatorField.vue'
import CalculationResultReport from 'components/CalculationResultReport.vue'
import SchemLdr from 'components/SchemLdr.vue'
import SchemHdr from 'components/SchemHdr.vue'
import SchemKd from 'components/SchemKd.vue'
import SchemAd from 'components/SchemAd.vue'
import calculatorFields from 'src/data/calculator_fields.json'
import { useUserStore } from 'stores/user-store'
import { downloadBlob } from 'src/utils/download'

const route = useRoute()
const $q = useQuasar()
const userStore = useUserStore()

const resultsRef = ref(null)
const activeTab = ref('calculator')
const formData = ref({})

// spec i ponowny_resurs są wzajemnie wykluczające
watch(() => formData.value.spec, v => { if (v === 'Tak') formData.value.ponowny_resurs = 'Nie' })
watch(() => formData.value.ponowny_resurs, v => { if (v === 'Tak') formData.value.spec = 'Nie' })

const calculatedResult = ref(null)
const loading = ref(true)
const calculating = ref(false)
const downloadingPdf = ref(false)
const unlocking = ref(false)
const currentResultId = ref(null)

const currentCost = ref(0)
const canAfford = ref(true)

// Pobiera koszt obliczenia dla aktualnych danych (reaguje na ponowny_resurs)
async function fetchCurrentCost() {
  if (!calculatorSlug.value) return
  try {
    const res = await api.post(`/calculators/definitions/${calculatorSlug.value}/get_cost/`, {
      input_data: formData.value
    })
    currentCost.value = res.data.cost
    canAfford.value = res.data.can_afford
  } catch (e) {
    console.error('Błąd pobierania kosztu:', e)
  }
}

// Reaguj na zmiany w formData, które wpływają na koszt (głównie ponowny_resurs)
watch(() => formData.value.ponowny_resurs, () => {
  fetchCurrentCost()
})

const savedResults = ref([])
const loadingResults = ref(false)
const selectedSavedResult = ref(null)
const selectedLogoId = ref(null)

watch(() => userStore.user?.logos, (logos) => {
  if (logos?.length && !selectedLogoId.value) {
    const def = logos.find(l => l.is_default) || logos[0]
    selectedLogoId.value = def.id
  }
}, { immediate: true })

const calculatorSlug = computed(() => route.params.slug)
const currentCalculatorDefinition = computed(() => calculatorFields[calculatorSlug.value] || null)

const units = ref({})
const deviceResults = ref([])
const selectedDeviceResult = ref(null)

const MECH_PARENT_DEVICES = {
  mech_podnoszenia: ['wciagarka', 'wciagnik', 'suwnica', 'zuraw', 'zuraw_przeladunkowy', 'ukladnica_magazynowa'],
  mech_jazdy_suwnicy: ['suwnica'],
  mech_jazdy_wciagarki: ['wciagarka'],
  mech_jazdy_zurawia: ['zuraw', 'zuraw_przeladunkowy'],
  mech_zmiany_wysiegu: ['zuraw', 'zuraw_przeladunkowy'],
  mech_zmiany_obrotu: ['zuraw', 'zuraw_przeladunkowy'],
}

const isMechanism = computed(() => calculatorSlug.value in MECH_PARENT_DEVICES)

// Wykrywanie zmiany kg → t w polach masy
const massFieldUnits = computed(() => {
  const result = {}
  const fields = currentCalculatorDefinition.value?.fields || {}
  for (const key in fields) {
    const f = fields[key]
    if (f.unit_type === 'mass' && f.type !== 'diagram') {
      const val = formData.value[key]
      if (val && typeof val === 'object') result[key] = val.unit
    }
  }
  return result
})

const schemKdRef = ref(null)
let askingMassUnit = false

function showMassUnitDialog() {
  askingMassUnit = true
  const fields = currentCalculatorDefinition.value?.fields || {}
  $q.dialog({
    title: 'Zmiana jednostki masy',
    message: 'Zmienić jednostkę masy na tony [t] we wszystkich polach?',
    cancel: { label: 'Tylko to pole', flat: true, color: 'primary' },
    ok: { label: 'Zmień wszędzie', color: 'primary', unelevated: true }
  }).onOk(() => {
    for (const k in fields) {
      if (fields[k].unit_type !== 'mass' || fields[k].type === 'diagram') continue
      if (formData.value[k] && typeof formData.value[k] === 'object') {
        formData.value[k] = { ...formData.value[k], unit: 't' }
      }
    }
    const kd = Array.isArray(schemKdRef.value) ? schemKdRef.value[0] : schemKdRef.value
    kd?.applyUnit?.('t')
  }).onDismiss(() => { askingMassUnit = false })
}

watch(massFieldUnits, (newUnits, oldUnits) => {
  if (askingMassUnit) return
  for (const key in newUnits) {
    if (oldUnits[key] === 'kg' && newUnits[key] === 't') {
      showMassUnitDialog()
      break
    }
  }
})

function onSchemKdKgToT() {
  if (askingMassUnit) return
  showMassUnitDialog()
}

const activeSections = computed(() => {
  const calc = currentCalculatorDefinition.value
  if (!calc?.fields) return []
  return (calc.sections || [])
    .map(s => ({ key: s.id, label: s.title, icon: s.icon, fieldKeys: s.fields.filter(k => calc.fields[k]) }))
    .filter(s => s.fieldKeys.some(k => isFieldVisible(k)))
})

const savedResultsColumns = [
  { name: 'created_at', label: 'Data', align: 'left', field: 'created_at', sortable: true, format: val => new Date(val).toLocaleString('pl-PL') },
  { name: 'resurs', label: 'Zużycie [%]', align: 'left', field: row => row.is_locked ? null : `${row.output_data?.resurs_wykorzystanie ?? row.output_data?.resurs ?? 0}%`, sortable: true },
  { name: 'status', label: 'Status', align: 'center' },
  { name: 'actions', label: 'Akcje', align: 'center' }
]

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
  return val.toLocaleString('pl-PL')
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




async function fetchSavedResults() {
  loadingResults.value = true
  try {
    const response = await api.get('/calculators/results/for_calculator/', {
      params: { slug: calculatorSlug.value }
    })
    savedResults.value = response.data
  } catch {
    Notify.create({ type: 'negative', message: 'Błąd pobierania historii.', position: 'top' })
  } finally {
    loadingResults.value = false
  }
}

function selectSavedResult(row) { selectedSavedResult.value = selectedSavedResult.value?.id === row.id ? null : row }


function loadResultToForm(row) {
  formData.value = JSON.parse(JSON.stringify(row.input_data))
  currentResultId.value = row.id
  activeTab.value = 'calculator'
  Notify.create({ type: 'info', message: 'Dane zostały wczytane do formularza.', position: 'top', timeout: 2000 })
}

function confirmDelete(row) {
  Dialog.create({
    title: 'Usunąć wynik?',
    message: `Czy na pewno chcesz usunąć wynik z dnia ${new Date(row.created_at).toLocaleDateString()}?`,
    cancel: { label: 'Anuluj', flat: true },
    ok: { label: 'Usuń', color: 'negative' },
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/calculators/results/${row.id}/`)
      savedResults.value = savedResults.value.filter(r => r.id !== row.id)
      if (selectedSavedResult.value?.id === row.id) selectedSavedResult.value = null
      Notify.create({ type: 'positive', message: 'Wynik usunięty.', position: 'top' })
    } catch {
      Notify.create({ type: 'negative', message: 'Błąd podczas usuwania.', position: 'top' })
    }
  })
}

async function downloadPdf(resultId = null) {
  const id = resultId || calculatedResult.value?.id
  if (!id) return
  downloadingPdf.value = true
  try {
    const params = {}
    if (selectedLogoId.value) params.logo_id = selectedLogoId.value
    const response = await api.get(`/calculators/results/${id}/pdf/`, { 
      params,
      responseType: 'blob' 
    })
    downloadBlob(response.data, `resurs_${id}.pdf`)
  } catch {
    Notify.create({ type: 'negative', message: 'Błąd podczas generowania PDF.', position: 'top' })
  } finally {
    downloadingPdf.value = false
  }
}

function getSavedFieldValue(input_data, key) {
  if (!input_data) return ''
  const val = input_data[key]
  if (val === null || val === undefined) return ''
  if (typeof val === 'object' && val.value !== undefined) return val.value
  return val
}



onMounted(async () => {
  await fetchUnits()
  initializeFormData()
  fetchDeviceResults()
  if (route.query.result_id) {
    await loadSingleResult(route.query.result_id)
  }
  loading.value = false
})

watch(calculatorSlug, async () => {
  await fetchUnits()
  initializeFormData()
  fetchDeviceResults()
  if (activeTab.value === 'results') fetchSavedResults()
})

watch(activeTab, (newTab) => {
  if (newTab === 'results') fetchSavedResults()
})
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
  currentResultId.value = null
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


async function fetchDeviceResults() {
  const parentSlugs = MECH_PARENT_DEVICES[calculatorSlug.value] || []
  if (!parentSlugs.length) return
  const all = []
  for (const slug of parentSlugs) {
    try {
      const res = await api.get('/calculators/results/for_calculator/', { params: { slug } })
      all.push(...res.data.map(r => ({ ...r, label: `${calculatorFields[slug]?.name || slug} — ${new Date(r.created_at).toLocaleDateString('pl-PL')}` })))
    } catch (error) {
      console.error(error)
    }
  }
  deviceResults.value = all
}

function loadFromDevice(result) {
  if (!result?.input_data) return
  // Pola nie wczytywane z urządzenia: widmo Kd (obliczane osobno dla mechanizmu)
  const SKIP_FIELDS = new Set(['diagram_kd', 'q_1', 'q_2', 'q_3', 'q_4', 'q_5', 'c_1', 'c_2', 'c_3', 'c_4', 'c_5'])
  Object.keys(currentCalculatorDefinition.value.fields).forEach(k => {
    if (!SKIP_FIELDS.has(k) && k in result.input_data) formData.value[k] = result.input_data[k]
  })
  Notify.create({ type: 'positive', message: 'Wczytano dane urządzenia (nr fabr., parametry). Kd wymaga osobnego obliczenia.' })
}


async function submitCalculation() {
  calculating.value = true
  try {
    let res
    if (currentResultId.value) {
      res = await api.patch(`/calculators/results/${currentResultId.value}/`, { input_data: formData.value })
    } else {
      res = await api.post(`/calculators/definitions/${calculatorSlug.value}/calculate/`, { input_data: formData.value })
    }
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
      Notify.create({ type: 'positive', message: currentResultId.value ? 'Zaktualizowano!' : 'Obliczono!' })
    }
  } catch (error) {
    Notify.create({ type: 'negative', message: error.response?.data?.detail || 'Błąd zapisu.' })
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

async function unlockSavedResult(row) {
  unlocking.value = true
  try {
    const res = await api.post(`/calculators/results/${row.id}/unlock/`)
    const idx = savedResults.value.findIndex(r => r.id === row.id)
    if (idx !== -1) {
      savedResults.value[idx] = { ...savedResults.value[idx], is_locked: false, output_data: res.data.output_data }
    }
    if (selectedSavedResult.value?.id === row.id) {
      selectedSavedResult.value = { ...selectedSavedResult.value, is_locked: false, output_data: res.data.output_data }
    }
    if (res.data.remaining_premium !== undefined && userStore.user) {
      userStore.user.premium = res.data.remaining_premium
    }
    Notify.create({ type: 'positive', message: 'Wyniki odblokowane pomyślnie!' })
  } catch (error) {
    Notify.create({ type: 'negative', message: error.response?.data?.detail || error.response?.data?.[0] || 'Błąd odblokowania.' })
  } finally { unlocking.value = false }
}


async function loadSingleResult(resultId) {
  try {
    const res = await api.get(`/calculators/results/${resultId}/`)
    const result = res.data
    // Wczytaj dane do formularza
    formData.value = JSON.parse(JSON.stringify(result.input_data))
    // Jeśli odblokowany, pokaż wyniki od razu
    if (!result.is_locked) {
      calculatedResult.value = result
      await nextTick()
      resultsRef.value?.scrollIntoView({ behavior: 'smooth' })
    } else {
      calculatedResult.value = { ...result, result_id: result.id }
    }
  } catch (error) {
    console.error('Błąd wczytywania wyniku:', error)
  }
}

onMounted(async () => {
  await fetchUnits()
  initializeFormData()
  fetchDeviceResults()
  if (route.query.result_id) {
    await loadSingleResult(route.query.result_id)
  }
  await fetchCurrentCost()
  loading.value = false
})
</script>

<style scoped>
.border-primary { border: 1px solid var(--q-primary); }
</style>
