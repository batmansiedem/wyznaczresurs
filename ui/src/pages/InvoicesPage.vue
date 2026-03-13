<template>
  <q-page padding class="container">
    <div class="row items-center q-mb-lg">
      <div class="col calc-page-header" style="margin-bottom:0">
        <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Faktury i rozliczenia</h1>
        <p class="text-subtitle1 text-grey-7 q-mb-none">
          {{ isAdmin ? 'Przegląd faktur wszystkich użytkowników.' : 'Twoja historia faktur i zakupionych punktów premium.' }}
        </p>
      </div>
    </div>

    <!-- Lista faktur -->
    <q-card flat bordered class="rounded-borders shadow-1">
      <q-table
        :rows="invoices"
        :columns="columns"
        row-key="id"
        :loading="loading"
        flat
        bordered
        no-data-label="Brak faktur do wyświetlenia"
        rows-per-page-label="Wierszy na stronę"
        :pagination="pagination"
      >
        <!-- Status KSeF -->
        <template v-slot:body-cell-ksef_status="props">
          <q-td :props="props">
            <q-chip
              :color="getStatusColor(props.row)"
              text-color="white"
              size="sm"
              dense
              class="text-weight-bold"
            >
              {{ getStatusLabel(props.row) }}
            </q-chip>
          </q-td>
        </template>

        <!-- Kwota brutto -->
        <template v-slot:body-cell-gross_amount="props">
          <q-td :props="props" class="text-weight-bold text-primary">
            {{ props.value }} PLN
          </q-td>
        </template>

        <!-- Akcje -->
        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat round dense color="primary" icon="visibility" @click="viewInvoice(props.row)">
              <q-tooltip>Podgląd szczegółów</q-tooltip>
            </q-btn>
            <q-btn
              flat round dense
              :color="(props.row.is_proforma || props.row.ksef_status === 'accepted') ? 'secondary' : 'grey-5'"
              icon="download"
              :disable="!props.row.is_proforma && props.row.ksef_status !== 'accepted'"
              @click="downloadInvoice(props.row)"
            >
              <q-tooltip>
                <span v-if="props.row.is_proforma">Pobierz PDF Proforma</span>
                <span v-else-if="props.row.ksef_status === 'accepted'">Pobierz PDF</span>
                <span v-else>PDF dostępny po akceptacji KSeF</span>
              </q-tooltip>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Dialog podglądu -->
    <q-dialog v-model="showDetailsDialog">
      <q-card v-if="selectedInvoice" style="min-width: 400px">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">Szczegóły Faktury {{ selectedInvoice.invoice_number }}</div>
        </q-card-section>
        <q-card-section class="q-pa-md">
          <q-list dense separator>
            <q-item><q-item-section><q-item-label caption>Status</q-item-label><q-item-label>{{ getStatusLabel(selectedInvoice) }}</q-item-label></q-item-section></q-item>
            <q-item><q-item-section><q-item-label caption>Numer KSeF</q-item-label><q-item-label class="text-mono">{{ selectedInvoice.ksef_reference_number }}</q-item-label></q-item-section></q-item>
            <q-item><q-item-section><q-item-label caption>Data wystawienia</q-item-label><q-item-label>{{ selectedInvoice.issue_date }}</q-item-label></q-item-section></q-item>
            <q-item><q-item-section><q-item-label caption>Nabywca</q-item-label><q-item-label>{{ selectedInvoice.buyer_name }} (NIP: {{ selectedInvoice.buyer_nip }})</q-item-label></q-item-section></q-item>
            <q-item><q-item-section><q-item-label caption>Kwota Brutto</q-item-label><q-item-label class="text-weight-bold">{{ selectedInvoice.gross_amount }} PLN</q-item-label></q-item-section></q-item>
            <q-item><q-item-section><q-item-label caption>Dodano punktów</q-item-label><q-item-label class="text-secondary text-weight-bold">+{{ selectedInvoice.points_added }} pkt</q-item-label></q-item-section></q-item>
          </q-list>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Zamknij" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useUserStore } from 'stores/user-store'

const $q = useQuasar()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.is_staff || userStore.user?.is_superuser)

const invoices = ref([])
const loading = ref(false)
const showDetailsDialog = ref(false)
const selectedInvoice = ref(null)

const pagination = ref({
  sortBy: 'issue_date',
  descending: true,
  page: 1,
  rowsPerPage: 10
})

const columns = computed(() => {
  const base = [
    { name: 'invoice_number', align: 'left', label: 'Nr faktury', field: 'invoice_number', sortable: true },
    { name: 'issue_date', align: 'left', label: 'Data', field: 'issue_date', sortable: true },
    { name: 'gross_amount', align: 'right', label: 'Suma Brutto', field: 'gross_amount', sortable: true },
    { name: 'points_added', align: 'center', label: 'Punkty', field: 'points_added', sortable: true },
    { name: 'ksef_status', align: 'center', label: 'Status KSeF', field: 'ksef_status', sortable: true },
    { name: 'actions', align: 'center', label: 'Opcje' }
  ]
  
  if (isAdmin.value) {
    base.splice(1, 0, { name: 'user_email', align: 'left', label: 'Użytkownik', field: 'user_email', sortable: true })
  }
  
  return base
})

const fetchInvoices = async () => {
  loading.value = true
  try {
    const response = await api.get('/billing/invoices/')
    invoices.value = response.data
  } catch {
    $q.notify({ color: 'negative', message: 'Błąd podczas pobierania faktur' })
  } finally {
    loading.value = false
  }
}

const viewInvoice = (invoice) => {
  selectedInvoice.value = invoice
  showDetailsDialog.value = true
}

const downloadInvoice = async (invoice) => {
  try {
    const response = await api.get(`/billing/invoices/${invoice.id}/download_pdf/`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Faktura_${invoice.invoice_number.replace(/\//g, '_')}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch {
    $q.notify({ color: 'negative', message: 'Błąd podczas pobierania pliku PDF' })
  }
}

const getStatusColor = (row) => {
  if (row.is_proforma) return 'grey-7'
  const status = row.ksef_status
  const map = {
    'accepted': 'positive',
    'pending': 'warning',
    'sent': 'info',
    'rejected': 'negative'
  }
  return map[status] || 'grey'
}

const getStatusLabel = (row) => {
  if (row.is_proforma) return 'PROFORMA'
  const status = row.ksef_status
  const map = {
    'accepted': 'ZAAKCEPTOWANA',
    'pending': 'OCZEKUJĄCA',
    'sent': 'WYSŁANA',
    'rejected': 'ODRZUCONA'
  }
  return map[status] || status.toUpperCase()
}

onMounted(() => {
  fetchInvoices()
})
</script>

<style scoped>
.text-mono { font-family: monospace; letter-spacing: 0.5px; }
</style>
