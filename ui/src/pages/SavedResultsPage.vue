<template>
  <q-page padding class="container">
    <div class="calc-page-header q-mb-xl">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Zapisane wyniki</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">Historia Twoich obliczeń i wygenerowanych raportów</p>
    </div>

    <q-card v-if="loading" flat bordered class="shadow-1 q-pa-xl text-center">
      <q-spinner-dots color="primary" size="3em" />
      <div class="text-grey-7 q-mt-md">Ładowanie Twoich wyników...</div>
    </q-card>

    <q-card v-else-if="!results.length" flat bordered class="shadow-1 q-pa-xl text-center hover-primary">
      <q-icon name="history" size="4em" color="grey-4" />
      <div class="text-h6 text-grey-7 q-mt-md">Brak zapisanych wyników.</div>
      <p class="text-grey-6">Wykonaj pierwsze obliczenia, aby zobaczyć tutaj historię.</p>
      <q-btn unelevated color="primary" label="Przejdź do kalkulatorów" to="/calculators" class="q-mt-md" />
    </q-card>

    <template v-else>
      <div class="section-label">Twoje obliczenia</div>
      <q-card flat bordered class="shadow-1 overflow-hidden">
        <q-table
          :rows="results"
          :columns="columns"
          row-key="id"
          flat
          :pagination="{ rowsPerPage: 10 }"
        >
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
            <q-td :props="props" class="q-gutter-x-sm">
              <q-btn icon="visibility" label="Szczegóły" color="primary" flat dense
                @click="showDetails(props.row)" no-caps />
              <q-btn
                v-if="!props.row.is_locked"
                icon="picture_as_pdf" color="primary" flat dense
                @click="downloadPdf(props.row)" :loading="downloadingPdf"
              >
                <q-tooltip>Pobierz PDF</q-tooltip>
              </q-btn>
              <q-btn
                v-else-if="(userStore.user?.premium ?? 0) >= (props.row.calculator_definition?.premium_cost ?? 0)"
                icon="lock_open" color="warning" flat dense
                :loading="unlocking" @click="unlockResult(props.row)"
              >
                <q-tooltip>Odblokuj ({{ props.row.calculator_definition?.premium_cost ?? '?' }} pkt)</q-tooltip>
              </q-btn>
              <q-btn v-else icon="add_circle" color="warning" flat dense to="/pricing">
                <q-tooltip>Brak punktów — doładuj konto</q-tooltip>
              </q-btn>
              <q-btn icon="delete" color="negative" flat dense
                @click="confirmDelete(props.row)" />
            </q-td>
          </template>
        </q-table>
      </q-card>
    </template>

    <!-- Dialog szczegółów -->
    <q-dialog v-model="showDetailsDialog">
      <q-card style="min-width: 600px; border-radius: 12px;">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6 text-weight-bold text-primary">Szczegóły obliczeń</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section v-if="selectedResult" class="q-pt-lg">
          <div class="row q-col-gutter-md q-mb-lg">
            <div class="col-12 col-sm-6">
              <div class="text-overline text-grey-6">Kalkulator</div>
              <div class="text-subtitle1 text-weight-bold">{{ selectedResult.calculator_name }}</div>
            </div>
            <div class="col-12 col-sm-6 text-right">
              <div class="text-overline text-grey-6">Data wykonania</div>
              <div class="text-subtitle1 text-weight-medium">{{ new Date(selectedResult.created_at).toLocaleString() }}</div>
            </div>
          </div>

          <q-separator class="q-mb-lg" />
          
          <div class="row q-col-gutter-lg">
            <div v-if="inputFieldDefinitions" class="col-12 col-md-6">
              <div class="text-overline text-primary q-mb-md">Dane wejściowe</div>
              <q-list dense>
                <q-item v-for="(fieldDef, key) in inputFieldDefinitions" :key="key" class="q-px-none min-height-unset">
                  <q-item-section>
                    <q-item-label class="text-grey-7">{{ fieldDef.label }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-item-label class="text-weight-bold">{{ formatValue(selectedResult.input_data[key], fieldDef) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>

            <div class="col-12 col-md-6">
              <div class="text-overline text-secondary q-mb-md">Wyniki analizy</div>
              <template v-if="selectedResult?.is_locked">
                <div class="text-center q-pa-lg">
                  <q-icon name="lock" size="3em" color="warning" class="q-mb-sm" />
                  <div class="text-body2 text-grey-7 q-mb-sm">Wyniki zablokowane — wymagają punktów premium.</div>
                  <div class="text-caption text-grey-6 q-mb-md">
                    Koszt odblokowania: <strong>{{ selectedResult.calculator_definition?.premium_cost ?? '?' }} pkt</strong>
                    &nbsp;·&nbsp; Twoje saldo: <strong>{{ userStore.user?.premium ?? 0 }} pkt</strong>
                  </div>
                  <q-btn
                    v-if="(userStore.user?.premium ?? 0) >= (selectedResult.calculator_definition?.premium_cost ?? 0)"
                    label="Odblokuj wyniki"
                    icon="lock_open"
                    color="primary"
                    unelevated no-caps
                    :loading="unlocking"
                    @click="unlockResult(selectedResult)"
                  />
                  <q-btn
                    v-else
                    label="Doładuj konto"
                    icon="add_circle"
                    color="primary"
                    unelevated no-caps
                    to="/pricing"
                    v-close-popup
                  />
                </div>
              </template>
              <q-card v-else-if="outputFieldDefinitions" flat bordered :class="$q.dark.isActive ? 'bg-grey-9' : 'bg-grey-1'">
                <q-list dense>
                  <q-item v-for="(fieldDef, key) in outputFieldDefinitions" :key="key" class="q-py-sm">
                    <q-item-section>
                      <q-item-label class="text-grey-8">{{ fieldDef.label }}</q-item-label>
                    </q-item-section>
                    <q-item-section side>
                      <q-item-label class="text-weight-bolder text-primary">{{ formatValue(selectedResult.output_data[key], fieldDef) }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-card>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right" class="q-pa-md">
          <q-btn flat label="Zamknij" color="grey-7" v-close-popup no-caps />
          <q-btn unelevated label="Pobierz PDF" color="primary" icon="picture_as_pdf" no-caps
            :loading="downloadingPdf" :disable="selectedResult?.is_locked"
            @click="downloadPdf(selectedResult)"
          >
            <q-tooltip v-if="selectedResult?.is_locked">Odblokuj wyniki, aby pobrać PDF</q-tooltip>
          </q-btn>
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'
import calculatorFields from 'src/data/calculator_fields.json'
import calculatorOutputFields from 'src/data/calculator_output_fields.json'
import { useUserStore } from 'stores/user-store'

const downloadingPdf = ref(false)

const userStore = useUserStore()
const results = ref([])
const loading = ref(true)
const showDetailsDialog = ref(false)
const selectedResult = ref(null)
const unlocking = ref(false)

async function downloadPdf(row) {
  if (row.is_locked) { Notify.create({ type: 'warning', message: 'Odblokuj wyniki, aby pobrać PDF.' }); return }
  downloadingPdf.value = true
  try {
    const res = await api.get(`/calculators/results/${row.id}/pdf/`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a'); a.href = url; a.download = `resurs_${row.id}.pdf`; a.click()
  } catch { Notify.create({ type: 'negative', message: 'Błąd pobierania PDF.' }) }
  finally { downloadingPdf.value = false }
}

const columns = [
  { name: 'calculator_name', required: true, label: 'Urządzenie', align: 'left', field: 'calculator_name', sortable: true },
  { name: 'created_at', label: 'Data obliczeń', align: 'left', field: 'created_at', sortable: true, format: val => new Date(val).toLocaleDateString() },
  { name: 'status', label: 'Status', align: 'center', field: 'is_locked' },
  { name: 'actions', label: 'Dostępne akcje', align: 'center' }
]

const inputFieldDefinitions = computed(() => {
  if (selectedResult.value && selectedResult.value.calculator_definition) {
    const slug = selectedResult.value.calculator_definition.slug;
    return calculatorFields[slug] ? calculatorFields[slug].fields : null;
  }
  return null;
});

const outputFieldDefinitions = computed(() => {
  if (selectedResult.value && selectedResult.value.calculator_definition) {
    const slug = selectedResult.value.calculator_definition.slug;
    return calculatorOutputFields[slug] ? calculatorOutputFields[slug].fields : null;
  }
  return null;
});

function formatValue(value, fieldDef) {
  if (value === null || value === undefined) return '-';
  switch (fieldDef.type) {
    case 'number': return `${value} ${fieldDef.unit || ''}`.trim();
    case 'percentage': return `${value}%`.trim();
    case 'date': return new Date(value).toLocaleDateString();
    case 'boolean': return value ? 'Tak' : 'Nie';
    default: return String(value);
  }
}

async function fetchResults() {
  loading.value = true
  try {
    const response = await api.get('/calculators/results/')
    results.value = response.data
  } catch {
    Notify.create({ type: 'negative', message: 'Nie udało się załadować wyników.' })
  } finally {
    loading.value = false
  }
}

function showDetails(row) {
  selectedResult.value = row
  showDetailsDialog.value = true
}

function confirmDelete(row) {
  Dialog.create({
    title: 'Usunąć wynik?',
    message: `Czy na pewno chcesz usunąć wynik "${row.calculator_name}"?`,
    cancel: { label: 'Anuluj', flat: true },
    ok: { label: 'Usuń', color: 'negative' },
    persistent: true,
  }).onOk(async () => {
    try {
      await api.delete(`/calculators/results/${row.id}/`)
      results.value = results.value.filter(r => r.id !== row.id)
      Notify.create({ type: 'positive', message: 'Wynik został usunięty.' })
    } catch {
      Notify.create({ type: 'negative', message: 'Błąd podczas usuwania.' })
    }
  })
}

async function unlockResult(row) {
  unlocking.value = true
  try {
    const res = await api.post(`/calculators/results/${row.id}/unlock/`)
    const idx = results.value.findIndex(r => r.id === row.id)
    if (idx !== -1) {
      results.value[idx] = { ...results.value[idx], is_locked: false, output_data: res.data.output_data }
    }
    if (selectedResult.value?.id === row.id) {
      selectedResult.value = { ...selectedResult.value, is_locked: false, output_data: res.data.output_data }
    }
    if (res.data.remaining_premium !== undefined && userStore.user) {
      userStore.user.premium = res.data.remaining_premium
    }
    Notify.create({ type: 'positive', message: 'Wyniki odblokowane pomyślnie!' })
  } catch (error) {
    Notify.create({ type: 'negative', message: error.response?.data?.detail || error.response?.data?.[0] || 'Błąd odblokowania.' })
  } finally { unlocking.value = false }
}

onMounted(fetchResults)
</script>

<style scoped>
.bg-card { background-color: var(--q-bg-color); }
.min-height-unset { min-height: unset; }
</style>
