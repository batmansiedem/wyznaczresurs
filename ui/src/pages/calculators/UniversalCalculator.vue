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
                  <span v-html="section.label" />
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
                          <CalculatorField :field="currentCalculatorDefinition.fields[key]" v-model="formData[key]" :units="units" :disabled="!!currentResultId && ['nr_fabryczny', 'lata_pracy', 'data_resurs', 'ostatni_resurs'].includes(key)" />
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
                  <!-- Stan obciążenia live — pokazuj po sekcji kd -->
                  <div v-if="section.fieldKeys.includes('diagram_kd') && liveStanObciazenia" class="q-mt-md">
                    <div :class="['stan-obciazenia-callout', `stan-${liveStanObciazenia.cls}`]">
                      <q-icon :name="liveStanObciazenia.icon" size="20px" class="q-mr-sm flex-shrink-0" />
                      <div>
                        <div class="text-weight-bold">{{ liveStanObciazenia.label }}</div>
                        <div class="text-caption q-mt-xs">{{ liveStanObciazenia.opis }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Baner trybu modyfikacji -->
              <div v-if="currentResultId" class="q-px-lg q-pb-sm">
                <div class="mode-banner">
                  <q-icon name="edit_note" size="20px" class="q-mr-sm flex-shrink-0" />
                  <span>Modyfikujesz istniejące obliczenia — <strong>nr fabryczny</strong>, <strong>lata pracy</strong> i dane ponownego resursu są zablokowane.</span>
                  <q-space />
                  <q-btn flat dense no-caps size="sm" icon="add_circle_outline" label="Zamiast tego — nowe obliczenia" color="primary" class="q-ml-md flex-shrink-0" @click="startNewFromLoaded" />
                </div>
              </div>
              <div class="q-px-lg q-pb-lg">
                <q-separator class="q-mb-lg" />
                <div class="row q-gutter-md items-center">
                  <q-btn
                    :label="currentResultId ? 'Zapisz zmiany (0 pkt)' : `Oblicz wyznaczenie resursu (${currentCost} pkt)`"
                    type="submit" color="primary" :loading="calculating" icon="calculate" unelevated size="lg" class="q-px-xl"
                  />
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
                  @unlock="unlockResult"
                  @download-pdf="downloadPdf()"
                />
              </q-card-section>
            </template>
          </q-card>

          <!-- Sekcja mechanizmów powiązanych (tylko dla urządzeń nadrzędnych) -->
          <q-card v-if="childMechs.length" flat bordered class="shadow-1 overflow-hidden q-mt-lg">
            <div class="calc-section-bar">
              <q-icon name="settings" size="14px" />
              Mechanizmy powiązane
            </div>
            <div class="q-pa-md">
              <p class="text-body2 text-grey-7 q-mb-md">
                Wyznacz resurs mechanizmów napędowych tego urządzenia:
              </p>
              <div class="row q-gutter-sm">
                <q-btn
                  v-for="mech in childMechs"
                  :key="mech.slug"
                  :label="mech.name"
                  :to="`/calculators/${mech.slug}`"
                  outline
                  color="primary"
                  no-caps
                  icon="arrow_forward"
                />
              </div>
            </div>
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

const calculatorConfigs = ref({})

const calculatorSlug = computed(() => route.params.slug)
const currentCalculatorDefinition = computed(() => calculatorConfigs.value[calculatorSlug.value] || null)

const units = ref({})
const deviceResults = ref([])
const selectedDeviceResult = ref(null)

// Mechanizmy: slug → lista urządzeń nadrzędnych (z pola parent_devices w konfiguracji)
const mechParentDevices = computed(() => {
  const map = {}
  for (const [slug, def] of Object.entries(calculatorConfigs.value)) {
    if (def.parent_devices?.length) map[slug] = def.parent_devices
  }
  return map
})

const deviceChildMechs = computed(() => {
  const map = {}
  for (const [slug, def] of Object.entries(calculatorConfigs.value)) {
    if (!def.parent_devices?.length) continue
    for (const parent of def.parent_devices) {
      if (!map[parent]) map[parent] = []
      map[parent].push({ slug, name: def.name || slug })
    }
  }
  return map
})

const isMechanism = computed(() => calculatorSlug.value in mechParentDevices.value)
const childMechs = computed(() => deviceChildMechs.value[calculatorSlug.value] || [])

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

// ── Live stan obciążenia na podstawie wartości q/c w formularzu ────────────
// Warunki: suma c_i = 100%, tam gdzie c_i > 0 musi być q_i > 0 (nie wszystkie rzędy muszą być wypełnione)
function toKg(raw) {
  if (raw == null) return 0
  const v = typeof raw === 'object' ? parseFloat(raw.value) || 0 : parseFloat(raw) || 0
  const unit = typeof raw === 'object' ? (raw.unit || 'kg') : 'kg'
  return unit === 't' ? v * 1000 : v
}
const liveWspKdr = computed(() => {
  const fd = formData.value
  const qMax = toKg(fd.q_max)
  if (!qMax) return null
  let kd = 0
  let cSum = 0
  for (let i = 1; i <= 5; i++) {
    const qi = toKg(fd[`q_${i}`])
    const ci = parseFloat(typeof fd[`c_${i}`] === 'object' ? fd[`c_${i}`]?.value : fd[`c_${i}`]) || 0
    if (ci > 0) {
      if (qi <= 0) return null   // c > 0 bez q — dane niepełne
      cSum += ci
      kd += (ci / 100) * Math.pow(qi / qMax, 3)
    }
  }
  if (Math.abs(cSum - 100) > 0.5) return null  // suma c_i ≠ 100%
  return kd > 0 ? kd : null
})

const STAN_TABLE_Q = [
  { max: 0.125, label: 'Q1 — lekki', cls: 'q1', icon: 'sentiment_very_satisfied', opis: 'Ładunek nominalny podnoszony bardzo rzadko, zwykle ładunki znacznie mniejsze od nominalnego' },
  { max: 0.25,  label: 'Q2 — przeciętny', cls: 'q2', icon: 'sentiment_satisfied', opis: 'Ładunek nominalny podnoszony rzadko, zwykle ładunki zbliżone do połowy ładunku nominalnego' },
  { max: 0.5,   label: 'Q3 — ciężki', cls: 'q3', icon: 'sentiment_dissatisfied', opis: 'Ładunek nominalny podnoszony często, zwykle ładunki większe od połowy ładunku nominalnego' },
  { max: 1.0,   label: 'Q4 — bardzo ciężki', cls: 'q4', icon: 'sentiment_very_dissatisfied', opis: 'Ładunek nominalny podnoszony regularnie i ładunki bliskie nominalnemu' },
]
const STAN_TABLE_L = [
  { max: 0.125, label: 'L1 — lekki', cls: 'q1', icon: 'sentiment_very_satisfied', opis: 'Obciążenie mechanizmu bardzo lekkie, ładunki znacznie mniejsze od nominalnego' },
  { max: 0.25,  label: 'L2 — przeciętny', cls: 'q2', icon: 'sentiment_satisfied', opis: 'Obciążenie mechanizmu przeciętne, ładunki zbliżone do połowy ładunku nominalnego' },
  { max: 0.5,   label: 'L3 — ciężki', cls: 'q3', icon: 'sentiment_dissatisfied', opis: 'Obciążenie mechanizmu ciężkie, ładunki często bliskie nominalnemu' },
  { max: 1.0,   label: 'L4 — bardzo ciężki', cls: 'q4', icon: 'sentiment_very_dissatisfied', opis: 'Obciążenie mechanizmu bardzo ciężkie, ładunki regularnie bliskie nominalnemu' },
]

const liveStanObciazenia = computed(() => {
  const kd = liveWspKdr.value
  if (kd === null) return null
  const table = isMechanism.value ? STAN_TABLE_L : STAN_TABLE_Q
  return table.find(s => kd <= s.max) || table[table.length - 1]
})

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


function _applyLoadedData(loaded, resultId) {
  for (const k of Object.keys(formData.value)) {
    if (!(k in loaded)) delete formData.value[k]
  }
  Object.assign(formData.value, loaded)
  const kdRef = Array.isArray(schemKdRef.value) ? schemKdRef.value[0] : schemKdRef.value
  if (kdRef) {
    for (let i = 1; i <= 5; i++) {
      const v = loaded[`q_${i}`]
      if (v != null && typeof v === 'object' && v.unit) { kdRef.applyUnit(v.unit); break }
    }
  }
  currentResultId.value = resultId
  activeTab.value = 'calculator'
}

function loadResultToForm(row) {
  const loaded = JSON.parse(JSON.stringify(row.input_data))
  const date = new Date(row.created_at).toLocaleDateString('pl-PL')
  Dialog.create({
    title: 'Co chcesz zrobić z tymi danymi?',
    message: `Obliczenia z dnia <b>${date}</b>`,
    html: true,
    options: {
      type: 'radio',
      model: 'modify',
      items: [
        {
          label: 'Zaktualizuj istniejący wynik (bezpłatnie)',
          description: 'Zmień parametry i nadpisz ten wynik. Nr fabryczny i lata pracy pozostają zablokowane.',
          value: 'modify',
          color: 'primary',
        },
        {
          label: `Stwórz nowe obliczenia (${currentCost.value} pkt)`,
          description: 'Dane zostaną wczytane, ale wynik zostanie zapisany jako nowy. Wszystkie pola odblokowane.',
          value: 'new',
          color: 'secondary',
        },
      ],
    },
    cancel: { label: 'Anuluj', flat: true },
    ok: { label: 'Wczytaj dane', color: 'primary', unelevated: true },
    persistent: true,
  }).onOk(mode => {
    _applyLoadedData(loaded, mode === 'modify' ? row.id : null)
    const msg = mode === 'modify'
      ? 'Dane wczytane — tryb modyfikacji (bezpłatny).'
      : 'Dane wczytane — tryb nowych obliczeń.'
    Notify.create({ type: 'info', message: msg, position: 'top', timeout: 2500 })
  })
}

function startNewFromLoaded() {
  currentResultId.value = null
  Notify.create({ type: 'info', message: 'Tryb nowych obliczeń — wszystkie pola odblokowane.', position: 'top', timeout: 2000 })
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
    const response = await api.get(`/calculators/results/${id}/pdf/`, { responseType: 'blob' })
    const cd = response.headers['content-disposition'] || ''
    const match = cd.match(/filename="([^"]+)"/)
    const filename = match?.[1] || `resurs_${id}.pdf`
    downloadBlob(response.data, filename)
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
  const newData = {}
  for (const key in currentCalculatorDefinition.value.fields) {
    const f = currentCalculatorDefinition.value.fields[key]
    if (f.type === 'diagram') continue
    if (f.type === 'number') {
      newData[key] = { value: f.default_value ?? null, unit: f.default_unit || units.value[f.unit_type]?.[0]?.symbol || null }
    } else if (f.type === 'inspection_status' && f.options?.length) {
      // Domyślnie ostatnia opcja ("Nie dotyczy")
      const last = f.options[f.options.length - 1]
      newData[key] = f.default_value ?? (typeof last === 'object' ? last.value : last)
    } else {
      newData[key] = f.default_value ?? null
    }
  }
  // Mutuj istniejący obiekt zamiast go zamieniać — SchemKd trzyma referencję do tego samego obiektu
  for (const k of Object.keys(formData.value)) delete formData.value[k]
  Object.assign(formData.value, newData)
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
  const parentSlugs = mechParentDevices.value[calculatorSlug.value] || []
  if (!parentSlugs.length) return
  const all = []
  for (const slug of parentSlugs) {
    try {
      const res = await api.get('/calculators/results/for_calculator/', { params: { slug } })
      all.push(...res.data.map(r => {
        const name = calculatorConfigs.value[slug]?.name || slug
        const nrFab = r.input_data?.nr_fabryczny || ''
        const date = new Date(r.created_at).toLocaleDateString('pl-PL')
        const label = nrFab ? `${name} — nr fab. ${nrFab} — ${date}` : `${name} — ${date}`
        return { ...r, label }
      }))
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
  // ── Walidacja diagramów KD / LDR / HDR / AD ───────────────────────────────
  const _fields = currentCalculatorDefinition.value?.fields || {}
  const _fd = formData.value

  function _getNum(raw) {
    if (raw == null) return 0
    return Number(typeof raw === 'object' ? (raw?.value ?? 0) : raw) || 0
  }

  if (_fields.diagram_kd && isFieldVisible('diagram_kd')) {
    let cSum = 0, missingQ = false
    for (let i = 1; i <= 5; i++) {
      const c = Number(_fd[`c_${i}`] ?? 0)
      cSum += c
      if (c > 0 && !_getNum(_fd[`q_${i}`])) missingQ = true
    }
    if (cSum === 0) {
      Notify.create({ type: 'negative', position: 'top', message: 'Widmo K_d: wypełnij co najmniej jedną klasę obciążeń (c_i > 0).' })
      return
    }
    if (Math.round(cSum * 10) / 10 !== 100) {
      Notify.create({ type: 'negative', position: 'top', message: `Widmo K_d: suma udziałów c musi wynosić 100% (aktualnie ${Math.round(cSum * 10) / 10}%).` })
      return
    }
    if (missingQ) {
      Notify.create({ type: 'negative', position: 'top', message: 'Widmo K_d: dla każdej klasy z c_i > 0 należy podać masę q_i.' })
      return
    }
  }

  if (_fields.diagram_ldr && isFieldVisible('diagram_ldr')) {
    let pSum = 0
    for (let i = 1; i <= 25; i++) pSum += Number(_fd[`p_${i}`] ?? 0)
    if (pSum === 0) {
      Notify.create({ type: 'negative', position: 'top', message: 'Widmo LDR: zaznacz co najmniej jedną strefę i podaj udział p_i.' })
      return
    }
    if (Math.round(pSum * 10) / 10 !== 100) {
      Notify.create({ type: 'negative', position: 'top', message: `Widmo LDR: suma udziałów p musi wynosić 100% (aktualnie ${Math.round(pSum * 10) / 10}%).` })
      return
    }
  }

  if (_fields.diagram_hdr && isFieldVisible('diagram_hdr')) {
    let ccSum = 0, missingH = false
    for (let i = 1; i <= 5; i++) {
      const cc = Number(_fd[`cc_${i}`] ?? 0)
      ccSum += cc
      if (cc > 0 && !_getNum(_fd[`h_${i}`])) missingH = true
    }
    if (ccSum === 0) {
      Notify.create({ type: 'negative', position: 'top', message: 'Widmo HDR: zaznacz co najmniej jedną strefę wysokości i podaj udział czasu cc_i.' })
      return
    }
    if (Math.round(ccSum * 10) / 10 !== 100) {
      Notify.create({ type: 'negative', position: 'top', message: `Widmo HDR: suma udziałów czasu musi wynosić 100% (aktualnie ${Math.round(ccSum * 10) / 10}%).` })
      return
    }
    if (missingH) {
      Notify.create({ type: 'negative', position: 'top', message: 'Widmo HDR: dla każdej strefy z cc_i > 0 należy podać wysokość h_i.' })
      return
    }
  }

  if (_fields.diagram_ad && isFieldVisible('diagram_ad')) {
    const aSum = [1, 2, 3].reduce((s, i) => s + Number(_fd[`a_${i}`] ?? 0), 0)
    if (aSum === 0) {
      Notify.create({ type: 'negative', position: 'top', message: 'Kąt α_d: wypełnij co najmniej jeden udział procentowy.' })
      return
    }
    if (Math.round(aSum * 10) / 10 !== 100) {
      Notify.create({ type: 'negative', position: 'top', message: `Kąt α_d: suma udziałów musi wynosić 100% (aktualnie ${Math.round(aSum * 10) / 10}%).` })
      return
    }
  }

  calculating.value = true
  try {
    let res
    if (currentResultId.value) {
      res = await api.patch(`/calculators/results/${currentResultId.value}/`, { input_data: formData.value })
    } else {
      res = await api.post(`/calculators/definitions/${calculatorSlug.value}/calculate/`, { input_data: formData.value })
    }
    if (currentResultId.value) {
      calculatedResult.value = res.data
    } else {
      calculatedResult.value = {
        ...res.data,
        id: res.data.result_id,
        input_data: JSON.parse(JSON.stringify(formData.value)),
        calculator_definition: {
          slug: calculatorSlug.value,
          name: currentCalculatorDefinition.value?.name || calculatorSlug.value,
          premium_cost: res.data.premium_cost || currentCalculatorDefinition.value?.premium_cost || 0,
        },
      }
    }
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
    const loaded = JSON.parse(JSON.stringify(result.input_data))
    const date = new Date(result.created_at).toLocaleDateString('pl-PL')

    // Wstępnie wypełnij formData żeby fetchCurrentCost zwrócił właściwy koszt
    Object.assign(formData.value, loaded)
    await fetchCurrentCost()

    Dialog.create({
      title: 'Co chcesz zrobić z tymi danymi?',
      message: `Obliczenia z dnia <b>${date}</b>`,
      html: true,
      options: {
        type: 'radio',
        model: 'modify',
        items: [
          {
            label: 'Zaktualizuj istniejący wynik (bezpłatnie)',
            description: 'Zmień parametry i nadpisz ten wynik. Nr fabryczny i lata pracy pozostają zablokowane.',
            value: 'modify',
            color: 'primary',
          },
          {
            label: `Stwórz nowe obliczenia (${currentCost.value} pkt)`,
            description: 'Dane zostaną wczytane, ale wynik zostanie zapisany jako nowy. Wszystkie pola odblokowane.',
            value: 'new',
            color: 'secondary',
          },
        ],
      },
      cancel: { label: 'Anuluj', flat: true },
      ok: { label: 'Wczytaj dane', color: 'primary', unelevated: true },
      persistent: true,
    }).onOk(mode => {
      _applyLoadedData(loaded, mode === 'modify' ? result.id : null)
      if (mode === 'modify' && !result.is_locked) {
        calculatedResult.value = result
        nextTick(() => resultsRef.value?.scrollIntoView({ behavior: 'smooth' }))
      }
      const msg = mode === 'modify'
        ? 'Dane wczytane — tryb modyfikacji (bezpłatny).'
        : 'Dane wczytane — tryb nowych obliczeń.'
      Notify.create({ type: 'info', message: msg, position: 'top', timeout: 2500 })
    })
  } catch (error) {
    console.error('Błąd wczytywania wyniku:', error)
  }
}

async function fetchCalculatorConfigs() {
  try {
    const res = await api.get('/calculators/definitions/schemas/')
    calculatorConfigs.value = res.data
  } catch (error) {
    console.error('Błąd pobierania konfiguracji kalkulatorów:', error)
  }
}

onMounted(async () => {
  await fetchCalculatorConfigs()
  await fetchUnits()
  initializeFormData()
  fetchDeviceResults()
  fetchSavedResults()
  if (route.query.result_id) {
    await loadSingleResult(route.query.result_id)
  }
  await fetchCurrentCost()
  loading.value = false
})
</script>

<style scoped>
.border-primary { border: 1px solid var(--q-primary); }

.mode-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(21, 101, 192, 0.07);
  border: 1px solid rgba(21, 101, 192, 0.2);
  border-left: 4px solid var(--q-primary);
  font-size: 13px;
  color: #1565c0;
  flex-wrap: wrap;
}
.body--dark .mode-banner {
  background: rgba(144, 202, 249, 0.08);
  border-color: rgba(144, 202, 249, 0.25);
  color: #90caf9;
}

.stan-obciazenia-callout {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  border-left: 4px solid;
  margin-top: 4px;
  &.stan-q1 { background: rgba(46, 125, 50, 0.08); border-color: #2E7D32; color: #1b5e20; }
  &.stan-q2 { background: rgba(249, 168, 37, 0.08); border-color: #F9A825; color: #e65100; }
  &.stan-q3 { background: rgba(230, 81, 0, 0.10); border-color: #E65100; color: #bf360c; }
  &.stan-q4 { background: rgba(183, 28, 28, 0.10); border-color: #B71C1C; color: #7f0000; }
}
.body--dark {
  .stan-obciazenia-callout {
    &.stan-q1 { background: rgba(46, 125, 50, 0.15); color: #81c784; }
    &.stan-q2 { background: rgba(249, 168, 37, 0.15); color: #ffcc80; }
    &.stan-q3 { background: rgba(230, 81, 0, 0.15); color: #ffb74d; }
    &.stan-q4 { background: rgba(183, 28, 28, 0.15); color: #ef9a9a; }
  }
}
</style>
