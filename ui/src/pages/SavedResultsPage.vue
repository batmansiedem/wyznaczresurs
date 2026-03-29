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
            <q-td :props="props" class="q-gutter-x-sm text-center">
              <q-btn icon="open_in_new" label="Kalkulator" color="primary" flat dense no-caps
                :to="`/calculators/${props.row.calculator_slug}?result_id=${props.row.id}`" />
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
              <q-btn icon="delete" color="negative" flat dense
                @click="confirmDelete(props.row)" />
            </q-td>
          </template>
        </q-table>
      </q-card>
    </template>

    <!-- Dialog szczegółów -->
    <q-dialog v-model="showDetailsDialog" :maximized="$q.screen.lt.md" @show="() => window.dispatchEvent(new Event('resize'))">
      <q-card class="result-dialog-card">
        <q-card-section class="row items-center bg-primary text-white no-wrap">
          <div class="text-h6 text-weight-bold ellipsis">
            {{ selectedResult?.calculator_name }} — Szczegóły obliczeń
          </div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup color="white" class="q-ml-sm flex-shrink-0" />
        </q-card-section>

        <q-card-section v-if="selectedResult" class="q-pa-md q-pa-lg-lg result-dialog-body">
          <div class="row items-center justify-between q-mb-md text-caption text-grey-6">
            <span>Data: <b class="text-grey-8">{{ new Date(selectedResult.created_at).toLocaleString('pl-PL') }}</b></span>
            <span>ID: <b class="text-grey-8">{{ selectedResult.id }}</b></span>
          </div>
          <CalculationResultReport
            :result="selectedResult"
            :user-premium="userStore.user?.premium ?? 0"
            :unlocking="unlocking"
            :downloading-pdf="downloadingPdf"
            @unlock="unlockResult(selectedResult)"
            @download-pdf="downloadPdf(selectedResult)"
          />
        </q-card-section>

        <q-card-actions align="right" class="q-pa-sm q-px-md border-top flex-shrink-0">
          <q-btn flat label="Zamknij" color="grey-7" v-close-popup no-caps />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar, Notify, Dialog } from 'quasar'
import CalculationResultReport from 'components/CalculationResultReport.vue'
import { useUserStore } from 'stores/user-store'
import { downloadBlob } from 'src/utils/download'

const $q = useQuasar()
const userStore = useUserStore()
const results = ref([])
const loading = ref(true)
const showDetailsDialog = ref(false)
const selectedResult = ref(null)
const unlocking = ref(false)
const downloadingPdf = ref(false)
const columns = [
  { name: 'calculator_name', required: true, label: 'Urządzenie', align: 'left', field: 'calculator_name', sortable: true },
  { name: 'created_at', label: 'Data obliczeń', align: 'left', field: 'created_at', sortable: true, format: val => new Date(val).toLocaleDateString('pl-PL') },
  { name: 'status', label: 'Status', align: 'center', field: 'is_locked' },
  { name: 'actions', label: 'Dostępne akcje', align: 'center' }
]

async function fetchResults() {
  loading.value = true
  try {
    const response = await api.get('/calculators/results/')
    results.value = response.data
  } catch {
    Notify.create({ type: 'negative', message: 'Nie udało się załadować wyników.', position: 'top' })
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
      Notify.create({ type: 'positive', message: 'Wynik został usunięty.', position: 'top' })
    } catch {
      Notify.create({ type: 'negative', message: 'Błąd podczas usuwania.', position: 'top' })
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
    Notify.create({ type: 'positive', message: 'Wyniki odblokowane pomyślnie!', position: 'top' })
  } catch (error) {
    Notify.create({ type: 'negative', message: error.response?.data?.detail || 'Błąd odblokowania.', position: 'top' })
  } finally { unlocking.value = false }
}

async function downloadPdf(row) {
  if (row.is_locked) { Notify.create({ type: 'warning', message: 'Odblokuj wyniki, aby pobrać PDF.', position: 'top' }); return }
  downloadingPdf.value = true
  try {
    const res = await api.get(`/calculators/results/${row.id}/pdf/`, { responseType: 'blob' })
    const cd = res.headers['content-disposition'] || ''
    const match = cd.match(/filename="([^"]+)"/)
    downloadBlob(res.data, match?.[1] || `resurs_${row.id}.pdf`)
  } catch { Notify.create({ type: 'negative', message: 'Błąd pobierania PDF.', position: 'top' }) }
  finally { downloadingPdf.value = false }
}

onMounted(fetchResults)
</script>

<style scoped>
.min-height-unset { min-height: unset; }

.result-dialog-card {
  width: 980px;
  max-width: 98vw;
  height: 92vh;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.result-dialog-body {
  flex: 1 1 0;
  overflow: auto;
}

.border-top {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.body--dark .border-top {
  border-top-color: rgba(255, 255, 255, 0.08);
}

/* Pełny ekran na mobile – nadpisz border-radius */
:deep(.q-dialog--maximized) .result-dialog-card {
  border-radius: 0;
  max-height: 100vh;
}
</style>
