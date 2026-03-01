<template>
  <q-page padding class="container">
    <div class="row items-center q-mb-lg">
      <div class="col calc-page-header" style="margin-bottom:0">
        <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Faktury i rozliczenia</h1>
        <p class="text-subtitle1 text-grey-7 q-mb-none">
          {{ isAdmin ? 'Zarządzanie fakturami wszystkich użytkowników i doładowywanie punktów.' : 'Twoja historia faktur i zakupionych punktów premium.' }}
        </p>
      </div>
      <div class="col-auto q-pl-md" v-if="isAdmin">
        <q-btn
          color="primary"
          icon="add"
          label="Wystaw fakturę"
          unelevated
          no-caps
          class="rounded-borders q-px-md shadow-2"
          @click="showInvoiceDialog = true"
        />
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
              :color="getStatusColor(props.value)"
              text-color="white"
              size="sm"
              dense
              class="text-weight-bold"
            >
              {{ getStatusLabel(props.value) }}
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
            <q-btn flat round dense color="secondary" icon="download" @click="downloadInvoice(props.row)">
              <q-tooltip>Pobierz PDF</q-tooltip>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Dialog wystawiania faktury (ADMIN ONLY) -->
    <q-dialog v-model="showInvoiceDialog" persistent>
      <q-card style="min-width: 500px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Wystaw nową fakturę</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md">
          <q-form @submit="onSubmitInvoice">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-select
                  v-model="newInvoice.user"
                  :options="userOptions"
                  option-label="email"
                  label="Wybierz użytkownika *"
                  outlined dense use-input input-debounce="300"
                  @filter="filterUsers"
                  hint="Wpisz email, aby wyszukać"
                  :rules="[val => !!val || 'Użytkownik jest wymagany']"
                >
                  <template v-slot:option="scope">
                    <q-item v-bind="scope.itemProps">
                      <q-item-section>
                        <q-item-label>{{ scope.opt.email }}</q-item-label>
                        <q-item-label caption>
                          {{ scope.opt.is_company ? scope.opt.company_name : scope.opt.first_name + ' ' + scope.opt.last_name }}
                        </q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <q-chip size="xs" color="blue-1" text-color="primary">{{ scope.opt.premium }} pkt</q-chip>
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="newInvoice.net_amount" type="number" label="Kwota netto (PLN) *"
                  outlined dense step="0.01" suffix="PLN"
                  :rules="[val => val > 0 || 'Kwota musi być większa od 0']" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="newInvoice.points_to_add" type="number" label="Punkty do doładowania *"
                  outlined dense suffix="pkt"
                  :rules="[val => val >= 0 || 'Punkty nie mogą być ujemne']" />
              </div>
              <div class="col-12">
                <div class="bg-grey-2 q-pa-sm rounded-borders text-caption text-grey-8">
                  <div class="row justify-between">
                    <span>VAT (23%):</span>
                    <span>{{ (newInvoice.net_amount * 0.23).toFixed(2) }} PLN</span>
                  </div>
                  <div class="row justify-between text-weight-bold text-dark q-mt-xs">
                    <span>Łącznie brutto:</span>
                    <span>{{ (newInvoice.net_amount * 1.23).toFixed(2) }} PLN</span>
                  </div>
                </div>
              </div>
              <div class="col-12">
                <q-banner dense class="bg-blue-1 text-primary rounded-borders">
                  <template v-slot:avatar><q-icon name="info" color="primary" /></template>
                  Faktura zostanie automatycznie wysłana do środowiska testowego <strong>KSeF</strong>.
                </q-banner>
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn label="Anuluj" flat v-close-popup />
                  <q-btn label="Wystaw i doładuj punkty" color="primary" unelevated type="submit" :loading="submitting" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Dialog podglądu (mock) -->
    <q-dialog v-model="showDetailsDialog">
      <q-card v-if="selectedInvoice" style="min-width: 400px">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">Szczegóły Faktury {{ selectedInvoice.invoice_number }}</div>
        </q-card-section>
        <q-card-section class="q-pa-md">
          <q-list dense separator>
            <q-item><q-item-section><q-item-label caption>Status KSeF</q-item-label><q-item-label>{{ getStatusLabel(selectedInvoice.ksef_status) }}</q-item-label></q-item-section></q-item>
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
const submitting = ref(false)
const showInvoiceDialog = ref(false)
const showDetailsDialog = ref(false)
const selectedInvoice = ref(null)

const allUsers = ref([])
const userOptions = ref([])

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

const newInvoice = ref({
  user: null,
  net_amount: 100,
  points_to_add: 100,
  buyer_name: '',
  buyer_nip: '',
  buyer_address: ''
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

const fetchUsers = async () => {
  if (!isAdmin.value) return
  try {
    const response = await api.get('/billing/admin/users/')
    allUsers.value = response.data
    userOptions.value = response.data
  } catch (error) {
    console.error('Błąd pobierania użytkowników', error)
  }
}

const filterUsers = (val, update) => {
  if (val === '') {
    update(() => { userOptions.value = allUsers.value })
    return
  }
  update(() => {
    const needle = val.toLowerCase()
    userOptions.value = allUsers.value.filter(v => v.email.toLowerCase().indexOf(needle) > -1)
  })
}

const onSubmitInvoice = async () => {
  submitting.value = true
  try {
    const payload = {
      user_id: newInvoice.value.user.id,
      net_amount: newInvoice.value.net_amount,
      points_to_add: newInvoice.value.points_to_add
    }
    
    await api.post('/billing/invoices/', payload)
    $q.notify({ color: 'positive', message: 'Faktura wystawiona pomyślnie. Punkty dodane.', icon: 'check' })
    showInvoiceDialog.value = false
    fetchInvoices()
    // Odśwież dane użytkownika (jeśli to admin doładowuje sam siebie, albo żeby zaktualizować state jeśli to możliwe)
    if (newInvoice.value.user.id === userStore.user.id) {
       userStore.fetchUser()
    }
  } catch (error) {
    const detail = error.response?.data?.detail || 'Błąd podczas wystawiania faktury'
    $q.notify({ color: 'negative', message: detail })
  } finally {
    submitting.value = false
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

const getStatusColor = (status) => {
  const map = {
    'accepted': 'positive',
    'pending': 'warning',
    'sent': 'info',
    'rejected': 'negative'
  }
  return map[status] || 'grey'
}

const getStatusLabel = (status) => {
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
  if (isAdmin.value) fetchUsers()
})
</script>

<style scoped>
.text-mono { font-family: monospace; letter-spacing: 0.5px; }
</style>
