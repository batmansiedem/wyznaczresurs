<template>
  <q-page padding class="container">

    <!-- NAGŁÓWEK -->
    <div class="calc-page-header">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Panel Administratora</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">Zarządzanie użytkownikami, transakcjami i fakturami.</p>
    </div>

    <!-- ZAKŁADKI GŁÓWNE -->
    <q-tabs v-model="mainTab" dense align="left" class="q-mb-md" indicator-color="primary" active-color="primary">
      <q-tab name="users" icon="group" label="Użytkownicy" />
      <q-tab name="transactions" icon="swap_horiz" label="Transakcje" />
      <q-tab name="invoices" icon="receipt_long" label="Faktury / Zestawienia" />
      <q-tab name="pricing" icon="payments" label="Cennik" />
      <q-tab name="stats" icon="bar_chart" label="Statystyki" />
    </q-tabs>

    <q-separator class="q-mb-md" />

    <q-tab-panels v-model="mainTab" animated keep-alive>

      <!-- ==================== TAB: UŻYTKOWNICY ==================== -->
      <q-tab-panel name="users" class="q-pa-none">
        <!-- Pasek filtrów -->
        <q-card flat bordered class="rounded-borders q-mb-md">
          <q-card-section class="q-py-sm">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm">
                <q-input v-model="userSearch" debounce="400" outlined dense clearable
                  label="Szukaj: email, imię, firma, NIP…"
                  @update:model-value="fetchUsers">
                  <template #prepend><q-icon name="search" /></template>
                </q-input>
              </div>
              <div class="col-6 col-sm-2" style="min-width:120px">
                <q-select v-model="userFilterActive" :options="activeOptions" emit-value map-options
                  outlined dense label="Status" @update:model-value="fetchUsers" />
              </div>
              <div class="col-6 col-sm-2" style="min-width:130px">
                <q-select v-model="userFilterCompany" :options="companyOptions" emit-value map-options
                  outlined dense label="Typ konta" @update:model-value="fetchUsers" />
              </div>
              <div class="col-12 col-sm-auto">
                <q-btn icon="person_add" label="Dodaj użytkownika" color="primary" unelevated
                  class="rounded-borders full-width" @click="openCreateUserDialog" />
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Tabela użytkowników -->
        <q-card flat bordered class="rounded-borders shadow-1">
          <q-table
            :rows="users"
            :columns="userColumns"
            row-key="id"
            :loading="usersLoading"
            flat
            no-data-label="Brak użytkowników"
            rows-per-page-label="Wierszy na stronę"
            :rows-per-page-options="[15, 25, 50]"
            @row-click="(_, row) => openUserDetail(row)"
            class="cursor-pointer"
          >
            <template #body-cell-display_name="props">
              <q-td :props="props">
                <div class="text-weight-medium">{{ props.row.display_name }}</div>
                <div class="text-caption text-grey-6">{{ props.row.email }}</div>
              </q-td>
            </template>
            <template #body-cell-account_type="props">
              <q-td :props="props">
                <q-chip :color="props.row.is_company ? 'blue' : 'grey-5'" text-color="white" size="sm" dense>
                  {{ props.row.is_company ? 'Firma' : 'Osoba' }}
                </q-chip>
                <q-chip v-if="props.row.is_superuser" color="red-7" text-color="white" size="sm" dense class="q-ml-xs">Admin</q-chip>
                <q-chip v-else-if="props.row.is_staff" color="orange" text-color="white" size="sm" dense class="q-ml-xs">Staff</q-chip>
              </q-td>
            </template>
            <template #body-cell-is_active="props">
              <q-td :props="props" class="text-center">
                <q-icon :name="props.row.is_active ? 'check_circle' : 'cancel'"
                  :color="props.row.is_active ? 'positive' : 'negative'" />
              </q-td>
            </template>
            <template #body-cell-last_login="props">
              <q-td :props="props">
                <span v-if="props.row.last_login">{{ formatDate(props.row.last_login) }}</span>
                <span v-else class="text-grey-4">—</span>
              </q-td>
            </template>
            <template #body-cell-premium="props">
              <q-td :props="props" class="text-center">
                <q-chip color="primary" text-color="white" size="sm" icon="stars" dense>{{ props.row.premium }}</q-chip>
              </q-td>
            </template>
            <template #body-cell-actions="props">
              <q-td :props="props" @click.stop>
                <q-btn flat round dense icon="person_search" color="primary" size="sm" @click="openUserDetail(props.row)">
                  <q-tooltip>Szczegóły / obliczenia</q-tooltip>
                </q-btn>
                <q-btn flat round dense icon="edit" color="secondary" size="sm" @click="openEditUserDialog(props.row)">
                  <q-tooltip>Edytuj</q-tooltip>
                </q-btn>
                <q-btn flat round dense icon="delete" color="negative" size="sm" @click="confirmDeleteUser(props.row)">
                  <q-tooltip>Usuń</q-tooltip>
                </q-btn>
              </q-td>
            </template>
          </q-table>
        </q-card>
      </q-tab-panel>

      <!-- ==================== TAB: TRANSAKCJE ==================== -->
      <q-tab-panel name="transactions" class="q-pa-none">
        <q-card flat bordered class="rounded-borders q-mb-md">
          <q-card-section class="q-py-sm">
            <div class="row q-col-gutter-md items-center">
              <div class="col-12 col-sm">
                <q-input v-model="txSearch" debounce="400" outlined dense clearable
                  label="Szukaj: kalkulator, email, firma…"
                  @update:model-value="fetchAllTransactions">
                  <template #prepend><q-icon name="search" /></template>
                </q-input>
              </div>
              <div class="col-6 col-sm-2" style="min-width:100px">
                <q-select v-model="txYear" :options="yearOptions" emit-value map-options
                  outlined dense clearable label="Rok" @update:model-value="fetchAllTransactions" />
              </div>
              <div class="col-6 col-sm-2" style="min-width:120px">
                <q-select v-model="txMonth" :options="monthOptions" emit-value map-options
                  outlined dense clearable label="Miesiąc" @update:model-value="fetchAllTransactions" />
              </div>
              <div class="col-12 col-sm-auto">
                <q-chip icon="swap_horiz" color="primary" text-color="white" outline>
                  {{ allTransactions.length }} wyników
                </q-chip>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <q-card flat bordered class="rounded-borders shadow-1 q-mb-xl">
          <q-table
            :rows="allTransactions"
            :columns="txColumns"
            row-key="id"
            :loading="txLoading"
            flat
            no-data-label="Brak transakcji"
            rows-per-page-label="Wierszy na stronę"
            :rows-per-page-options="[20, 50, 100]"
          >
            <template #body-cell-user_display="props">
              <q-td :props="props">
                <div class="text-weight-medium">{{ props.row.user_display }}</div>
                <div class="text-caption text-grey-6">{{ props.row.user_email }}</div>
              </q-td>
            </template>
            <template #body-cell-device_info="props">
              <q-td :props="props">
                <span class="text-weight-medium">{{ props.row.nr_fabryczny || '—' }}</span>
                <span v-if="props.row.typ" class="text-caption text-grey-6 q-ml-xs">({{ props.row.typ }})</span>
              </q-td>
            </template>
            <template #body-cell-is_locked="props">
              <q-td :props="props" class="text-center">
                <q-chip :color="props.row.is_locked ? 'negative' : 'positive'" text-color="white" size="sm" dense>
                  {{ props.row.is_locked ? 'Zablokowane' : 'Dostępne' }}
                </q-chip>
              </q-td>
            </template>
            <template #body-cell-created_at="props">
              <q-td :props="props">{{ formatDate(props.row.created_at) }}</q-td>
            </template>
            <template #body-cell-tx_pdf="props">
              <q-td :props="props" class="text-center">
                <q-btn flat round dense icon="picture_as_pdf" color="deep-orange" size="sm"
                  :loading="pdfLoadingId === props.row.id"
                  :disable="props.row.is_locked"
                  @click="downloadUserResultPdf(props.row)">
                  <q-tooltip>{{ props.row.is_locked ? 'Wynik zablokowany' : 'Pobierz PDF (wygląd użytkownika)' }}</q-tooltip>
                </q-btn>
              </q-td>
            </template>
          </q-table>
        </q-card>

        <!-- Analiza per kalkulator -->
        <div class="text-subtitle1 text-weight-bold q-mb-sm">
          <q-icon name="analytics" color="primary" class="q-mr-xs" />Analiza per kalkulator
        </div>
        <q-card flat bordered class="rounded-borders shadow-1">
          <q-table
            :rows="txAnalysis"
            :columns="txAnalysisColumns"
            row-key="calculator_name"
            flat dense
            hide-bottom
            :rows-per-page-options="[0]"
            no-data-label="Brak danych"
          />
        </q-card>
      </q-tab-panel>

      <!-- ==================== TAB: FAKTURY / ZESTAWIENIA ==================== -->
      <q-tab-panel name="invoices" class="q-pa-none">
        <q-card flat bordered class="rounded-borders q-mb-md">
          <q-card-section class="q-py-sm">
            <div class="row q-col-gutter-md items-center">
              <div class="col-6 col-sm-2" style="min-width:100px">
                <q-select v-model="invYear" :options="yearOptions" emit-value map-options
                  outlined dense clearable label="Rok" @update:model-value="fetchInvoiceReport" />
              </div>
              <div class="col-6 col-sm-2" style="min-width:120px">
                <q-select v-model="invMonth" :options="monthOptions" emit-value map-options
                  outlined dense clearable label="Miesiąc" @update:model-value="fetchInvoiceReport" />
              </div>
              <div class="col-12 col-sm-3">
                <q-select v-model="invStatus" :options="ksefStatusOptions" emit-value map-options
                  outlined dense clearable label="Status KSeF" @update:model-value="fetchInvoiceReport" />
              </div>
              <div class="col-12 col-sm-auto">
                <div class="row q-gutter-sm justify-end">
                  <q-btn icon="print" label="Drukuj" color="secondary" unelevated no-caps
                    class="rounded-borders" :disable="!invoiceReport" @click="printInvoiceReport" />
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Podsumowanie -->
        <div v-if="invoiceReport" class="row q-col-gutter-md q-mb-md">
          <div class="col-6 col-md-3">
            <q-card flat bordered class="rounded-borders text-center q-pa-md">
              <div class="text-caption text-grey-6">Liczba faktur</div>
              <div class="text-h5 text-weight-bold text-primary">{{ invoiceReport.summary.count }}</div>
            </q-card>
          </div>
          <div class="col-6 col-md-3">
            <q-card flat bordered class="rounded-borders text-center q-pa-md">
              <div class="text-caption text-grey-6">Łącznie netto</div>
              <div class="text-h5 text-weight-bold">{{ formatAmount(invoiceReport.summary.total_net) }} zł</div>
            </q-card>
          </div>
          <div class="col-6 col-md-3">
            <q-card flat bordered class="rounded-borders text-center q-pa-md">
              <div class="text-caption text-grey-6">Łącznie VAT</div>
              <div class="text-h5 text-weight-bold">{{ formatAmount(invoiceReport.summary.total_vat) }} zł</div>
            </q-card>
          </div>
          <div class="col-6 col-md-3">
            <q-card flat bordered class="rounded-borders text-center q-pa-md">
              <div class="text-caption text-grey-6">Łącznie brutto</div>
              <div class="text-h5 text-weight-bold text-positive">{{ formatAmount(invoiceReport.summary.total_gross) }} zł</div>
            </q-card>
          </div>
        </div>

        <q-card flat bordered class="rounded-borders shadow-1">
          <q-table
            :rows="invoiceReport ? invoiceReport.invoices : []"
            :columns="invColumns"
            row-key="id"
            :loading="invLoading"
            flat
            no-data-label="Brak faktur"
            rows-per-page-label="Wierszy na stronę"
            :rows-per-page-options="[20, 50, 0]"
          >
            <template #body-cell-ksef_status="props">
              <q-td :props="props" class="text-center">
                <q-chip :color="ksefColor(props.row.ksef_status)" text-color="white" size="sm" dense class="text-weight-bold">
                  {{ ksefLabel(props.row.ksef_status) }}
                </q-chip>
              </q-td>
            </template>
            <template #body-cell-gross_amount="props">
              <q-td :props="props" class="text-right text-weight-bold text-primary">
                {{ formatAmount(props.row.gross_amount) }} PLN
              </q-td>
            </template>
            <template #body-cell-actions="props">
              <q-td :props="props" class="text-center">
                <q-btn flat round dense icon="picture_as_pdf" color="primary" size="sm"
                  @click="downloadInvoicePdf(props.row)">
                  <q-tooltip>Pobierz PDF</q-tooltip>
                </q-btn>
              </q-td>
            </template>
          </q-table>
        </q-card>
      </q-tab-panel>

      <!-- ==================== TAB: CENNIK GŁÓWNY ==================== -->
      <q-tab-panel name="pricing" class="q-pa-none">
        <div class="row items-center q-mb-md">
          <div class="col">
            <div class="text-h6 text-weight-bold">Cennik globalny kalkulatorów</div>
            <div class="text-caption text-grey-7">Zdefiniuj domyślne ceny punktowe dla wszystkich użytkowników.</div>
          </div>
          <div class="col-auto">
            <q-btn icon="save" label="Zapisz wszystkie zmiany" color="primary" unelevated
              :loading="pricingLoading" @click="saveAllPrices" />
          </div>
        </div>

        <q-card flat bordered class="rounded-borders shadow-1">
          <q-table
            :rows="allCalculators"
            :columns="pricingColumns"
            row-key="id"
            flat
            hide-bottom
            :pagination="{ rowsPerPage: 0 }"
            :loading="pricingLoading"
          >
            <template #body-cell-premium_cost="props">
              <q-td :props="props">
                <q-input v-model.number="props.row.premium_cost" type="number" outlined dense suffix="pkt" style="width:120px" />
              </q-td>
            </template>
            <template #body-cell-premium_cost_recurring="props">
              <q-td :props="props">
                <q-input v-model.number="props.row.premium_cost_recurring" type="number" outlined dense suffix="pkt" style="width:120px" />
              </q-td>
            </template>
          </q-table>
        </q-card>
      </q-tab-panel>

      <!-- ==================== TAB: STATYSTYKI ==================== -->
      <q-tab-panel name="stats" class="q-pa-none">
        <div v-if="statsLoading" class="text-center q-pa-xl">
          <q-spinner size="3rem" color="primary" />
        </div>
        <div v-else-if="stats">
          <!-- Liczniki główne -->
          <div class="row q-col-gutter-md q-mb-lg">
            <div v-for="s in statsCards" :key="s.label" class="col-6 col-md-3">
              <q-card flat bordered class="rounded-borders text-center q-pa-md hover-primary">
                <q-icon :name="s.icon" size="2.5rem" :color="s.color" />
                <div class="text-h4 text-weight-bold q-mt-sm" :class="`text-${s.color}`">{{ s.value }}</div>
                <div class="text-caption text-grey-6 q-mt-xs">{{ s.label }}</div>
              </q-card>
            </div>
          </div>

          <!-- Wykresy trendów -->
          <div class="row q-col-gutter-lg">
            <!-- Wykres aktywności -->
            <div class="col-12 col-md-6">
              <q-card flat bordered class="rounded-borders q-pa-md shadow-1">
                <div class="text-subtitle1 text-weight-bold q-mb-md">Wzrost i aktywność (ostatnie 6 m-cy)</div>
                <VueApexCharts height="300" type="line" :options="trendChartOptions" :series="activitySeries" />
              </q-card>
            </div>
            <!-- Wykres przychodów -->
            <div class="col-12 col-md-6">
              <q-card flat bordered class="rounded-borders q-pa-md shadow-1">
                <div class="text-subtitle1 text-weight-bold q-mb-md">Przychody brutto (ostatnie 6 m-cy)</div>
                <VueApexCharts height="300" type="bar" :options="revenueChartOptions" :series="revenueSeries" />
              </q-card>
            </div>
          </div>
        </div>
      </q-tab-panel>

    </q-tab-panels>

    <!-- ===================== DRAWER SZCZEGÓŁÓW UŻYTKOWNIKA ===================== -->
    <q-dialog v-model="userDetailOpen" maximized transition-show="slide-left" transition-hide="slide-right">
      <q-card style="max-width:1000px;width:100%;margin-left:auto;border-radius:0">

        <q-card-section class="bg-primary text-white row items-center">
          <q-icon name="person" size="1.5rem" class="q-mr-sm" />
          <div>
            <div class="text-h6 text-weight-bold">{{ selectedUser?.display_name }}</div>
            <div class="text-caption" style="opacity:.8">{{ selectedUser?.email }}</div>
          </div>
          <q-space />
          <q-btn icon="edit" flat dense label="Edytuj" class="q-mr-sm" @click="openEditUserDialog(selectedUser)" />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section v-if="selectedUser" class="q-pa-md">
          <!-- Dane użytkownika — dwie kolumny -->
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-12 col-md-6">
              <q-list dense bordered separator class="rounded-borders">
                <q-item v-if="selectedUser.nip">
                  <q-item-section avatar><q-icon name="corporate_fare" color="primary" size="xs" /></q-item-section>
                  <q-item-section><q-item-label overline>NIP</q-item-label><q-item-label>{{ selectedUser.nip }}</q-item-label></q-item-section>
                </q-item>
                <q-item v-if="selectedUser.address_line">
                  <q-item-section avatar><q-icon name="location_on" color="primary" size="xs" /></q-item-section>
                  <q-item-section><q-item-label overline>Adres</q-item-label><q-item-label>{{ selectedUser.address_line }}, {{ selectedUser.postal_code }} {{ selectedUser.city }}</q-item-label></q-item-section>
                </q-item>
                <q-item>
                  <q-item-section avatar><q-icon name="stars" color="primary" size="xs" /></q-item-section>
                  <q-item-section><q-item-label overline>Punkty Premium</q-item-label><q-item-label class="text-weight-bold text-primary">{{ selectedUser.premium }} pkt</q-item-label></q-item-section>
                </q-item>
              </q-list>
            </div>
            <div class="col-12 col-md-6">
              <q-list dense bordered separator class="rounded-borders">
                <q-item>
                  <q-item-section avatar><q-icon name="login" color="secondary" size="xs" /></q-item-section>
                  <q-item-section><q-item-label overline>Ostatnie logowanie</q-item-label><q-item-label>{{ selectedUser.last_login ? formatDate(selectedUser.last_login) : 'Brak' }}</q-item-label></q-item-section>
                </q-item>
                <q-item>
                  <q-item-section avatar><q-icon name="event" color="secondary" size="xs" /></q-item-section>
                  <q-item-section><q-item-label overline>Data rejestracji</q-item-label><q-item-label>{{ formatDate(selectedUser.date_joined) }}</q-item-label></q-item-section>
                </q-item>
                <q-item>
                  <q-item-section avatar><q-icon name="calculate" color="info" size="xs" /></q-item-section>
                  <q-item-section><q-item-label overline>Obliczenia / Faktury</q-item-label><q-item-label>{{ selectedUser.transaction_count }} obliczeń &bull; {{ selectedUser.invoice_count }} faktur</q-item-label></q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>

          <!-- Zakładki: Obliczenia | Faktury | Indywidualne ceny | Logotypy | Podpisy -->
          <q-tabs v-model="detailTab" dense indicator-color="primary" active-color="primary" align="left" class="q-mb-sm">
            <q-tab name="obliczenia" icon="calculate" :label="`Obliczenia (${userTransactions.length})`" />
            <q-tab name="faktury" icon="receipt_long" :label="`Faktury (${userInvoices.length})`" />
            <q-tab name="znizka" icon="percent" label="Zniżka" />
            <q-tab name="logotypy" icon="photo_library" :label="`Logotypy (${userLogos.length})`" />
            <q-tab name="podpisy" icon="draw" :label="`Podpisy (${userSignatures.length})`" />
          </q-tabs>

          <q-tab-panels v-model="detailTab" animated>

            <!-- ---- OBLICZENIA ---- -->
            <q-tab-panel name="obliczenia" class="q-pa-none">
              <q-card flat bordered class="rounded-borders q-mb-sm">
                <q-card-section class="q-py-sm">
                  <div class="row q-col-gutter-md items-center">
                    <div class="col-6 col-sm-2" style="min-width:100px">
                      <q-select v-model="detailTxYear" :options="yearOptions" emit-value map-options
                        outlined dense clearable label="Rok" @update:model-value="fetchUserTransactions" />
                    </div>
                    <div class="col-6 col-sm-2" style="min-width:120px">
                      <q-select v-model="detailTxMonth" :options="monthOptions" emit-value map-options
                        outlined dense clearable label="Miesiąc" @update:model-value="fetchUserTransactions" />
                    </div>
                    <div class="col-12 col-sm">
                      <q-input v-model="detailTxSearch" debounce="400" outlined dense clearable
                        label="Szukaj kalkulatora…" @update:model-value="fetchUserTransactions">
                        <template #prepend><q-icon name="search" /></template>
                      </q-input>
                    </div>
                    <div class="col-12 col-sm-auto">
                      <q-btn icon="upload" color="secondary" unelevated no-caps
                        label="Przekaż moje obliczenie"
                        class="rounded-borders full-width"
                        @click="openPickMyResult">
                        <q-tooltip>Wybierz ze swoich obliczeń i skopiuj do tego użytkownika</q-tooltip>
                      </q-btn>
                    </div>
                  </div>
                </q-card-section>
              </q-card>

              <q-card flat bordered class="rounded-borders">
                <q-table
                  :rows="userTransactions"
                  :columns="userTxColumns"
                  row-key="id"
                  :loading="userTxLoading"
                  flat dense
                  no-data-label="Brak obliczeń"
                  rows-per-page-label="Wierszy na stronę"
                  :rows-per-page-options="[10, 25, 50, 0]"
                >
                  <template #body-cell-device="props">
                    <q-td :props="props">
                      <div class="text-weight-medium">{{ props.row.calculator_definition?.name || props.row.calculator_name }}</div>
                      <div class="text-caption text-grey-6 q-gutter-x-sm">
                        <span><b>{{ getField(props.row, 'nr_fabryczny') || '—' }}</b> / {{ getField(props.row, 'typ') || '—' }}</span>
                        <span v-if="getField(props.row, 'nr_udt')" class="q-ml-md">Nr UDT: {{ getField(props.row, 'nr_udt') }}</span>
                      </div>
                    </q-td>
                  </template>
                  <template #body-cell-result="props">
                    <q-td :props="props">
                      <span v-if="getResult(props.row)" class="text-weight-bold text-primary">{{ getResult(props.row) }}</span>
                      <span v-else class="text-grey-4">—</span>
                    </q-td>
                  </template>
                  <template #body-cell-is_locked="props">
                    <q-td :props="props" class="text-center">
                      <q-chip :color="props.row.is_locked ? 'negative' : 'positive'" text-color="white" size="sm" dense>
                        {{ props.row.is_locked ? 'Zablok.' : 'OK' }}
                      </q-chip>
                    </q-td>
                  </template>
                  <template #body-cell-created_at="props">
                    <q-td :props="props">{{ formatDate(props.row.created_at) }}</q-td>
                  </template>
                  <template #body-cell-tx_actions="props">
                    <q-td :props="props" class="text-center" style="white-space:nowrap">
                      <q-btn flat round dense icon="visibility" color="primary" size="sm"
                        @click="openTxDetail(props.row)">
                        <q-tooltip>Pełne dane</q-tooltip>
                      </q-btn>
                      <q-btn flat round dense icon="picture_as_pdf" color="deep-orange" size="sm"
                        :loading="pdfLoadingId === props.row.id"
                        :disable="props.row.is_locked"
                        @click="downloadUserResultPdf(props.row)">
                        <q-tooltip>{{ props.row.is_locked ? 'Wynik zablokowany' : 'Pobierz PDF (wygląd użytkownika)' }}</q-tooltip>
                      </q-btn>
                      <q-btn flat round dense icon="save" color="secondary" size="sm"
                        @click="() => { selectedTx = props.row; copyResultToAdmin() }">
                        <q-tooltip>Zapisz na moje konto</q-tooltip>
                      </q-btn>
                    </q-td>
                  </template>
                </q-table>
              </q-card>
            </q-tab-panel>

            <!-- ---- FAKTURY ---- -->
            <q-tab-panel name="faktury" class="q-pa-none">
              <div class="row justify-end q-mb-md">
                <q-btn icon="add" label="Wystaw nową fakturę" color="primary" unelevated no-caps
                  class="rounded-borders shadow-2" @click="openNewInvoiceForUser" />
              </div>

              <div v-if="userInvLoading" class="text-center q-pa-lg"><q-spinner color="primary" /></div>
              <q-card v-else flat bordered class="rounded-borders">
                <q-table
                  :rows="userInvoices"
                  :columns="userInvColumns"
                  row-key="id"
                  flat dense
                  no-data-label="Brak faktur"
                  rows-per-page-label="Wierszy na stronę"
                  :rows-per-page-options="[10, 25, 0]"
                >
                  <template #body-cell-ksef_status="props">
                    <q-td :props="props" class="text-center">
                      <q-chip v-if="props.row.is_proforma" color="grey-7" text-color="white" size="sm" dense class="text-weight-bold">
                        PROFORMA
                      </q-chip>
                      <template v-else>
                        <q-chip v-if="props.row.is_correction" color="orange-8" text-color="white" size="sm" dense class="text-weight-bold q-mr-xs">
                          KOREKTA
                        </q-chip>
                        <q-chip :color="ksefColor(props.row.ksef_status)" text-color="white" size="sm" dense class="text-weight-bold">
                          {{ ksefLabel(props.row.ksef_status) }}
                        </q-chip>
                      </template>
                    </q-td>
                  </template>
                  <template #body-cell-gross_amount="props">
                    <q-td :props="props" class="text-right text-weight-bold text-primary">
                      {{ formatAmount(props.row.gross_amount) }} PLN
                    </q-td>
                  </template>
                  <template #body-cell-inv_actions="props">
                    <q-td :props="props" class="text-center" style="white-space:nowrap">
                      <q-btn v-if="props.row.is_proforma" flat round dense icon="check_circle" color="positive" size="sm"
                        @click="approveProforma(props.row)">
                        <q-tooltip>Zatwierdź i wyślij do KSeF</q-tooltip>
                      </q-btn>
                      <q-btn
                        v-if="!props.row.is_proforma && props.row.ksef_status === 'accepted' && !props.row.is_correction"
                        flat round dense icon="receipt" color="warning" size="sm"
                        @click="startCorrection(props.row)">
                        <q-tooltip>Wystaw fakturę korygującą</q-tooltip>
                      </q-btn>
                      <q-btn v-if="props.row.ksef_status === 'accepted'" flat round dense icon="qr_code" color="secondary" size="sm"
                        @click="refreshInvoiceQr(props.row)">
                        <q-tooltip>Odśwież QR (KSeF)</q-tooltip>
                      </q-btn>
                      <q-btn flat round dense icon="picture_as_pdf" color="primary" size="sm"
                        @click="downloadInvoicePdf(props.row)">
                        <q-tooltip>Pobierz PDF</q-tooltip>
                      </q-btn>
                    </q-td>
                  </template>
                </q-table>
              </q-card>

              <div v-if="userInvoices.length" class="row q-gutter-sm q-mt-sm">
                <q-chip color="positive" text-color="white" icon="payments">
                  Razem brutto: {{ formatAmount(userInvoices.reduce((s, i) => s + parseFloat(i.gross_amount || 0), 0)) }} PLN
                </q-chip>
                <q-chip color="info" text-color="white" icon="stars">
                  Łącznie punktów: {{ userInvoices.reduce((s, i) => s + (i.points_added || 0), 0) }}
                </q-chip>
              </div>
            </q-tab-panel>

            <!-- ---- ZNIŻKA ---- -->
            <q-tab-panel name="znizka" class="q-pa-md">
              <q-card flat bordered class="rounded-borders">
                <q-card-section>
                  <div class="text-subtitle1 text-weight-bold q-mb-md">Indywidualna zniżka użytkownika</div>
                  <div class="row q-col-gutter-md items-center">
                    <div class="col-12 col-sm-6">
                      <q-input
                        v-model.number="selectedUser.discount_percent"
                        label="Zniżka procentowa (%)"
                        outlined dense type="number"
                        min="0" max="100" suffix="%"
                        hint="Zniżka naliczana od ceny punktowej każdego kalkulatora"
                      />
                    </div>
                    <div class="col-12 col-sm-auto">
                      <q-btn
                        label="Zastosuj zniżkę"
                        color="primary" unelevated
                        icon="save"
                        @click="updateUserAdminSettings"
                      />
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </q-tab-panel>

            <!-- ---- LOGOTYPY ---- -->
            <q-tab-panel name="logotypy" class="q-pa-none">
              <div class="row justify-end q-mb-md">
                <q-btn icon="add_photo_alternate" label="Dodaj logo użytkownikowi" color="primary" unelevated no-caps
                  class="rounded-borders shadow-2" @click="openAdminAddLogo" />
              </div>

              <div v-if="userLogosLoading" class="text-center q-pa-lg"><q-spinner color="primary" /></div>
              <q-card v-else flat bordered class="rounded-borders">
                <q-table
                  :rows="userLogos"
                  :columns="userLogoColumns"
                  row-key="id"
                  flat dense
                  no-data-label="Brak logotypów"
                  rows-per-page-label="Wierszy na stronę"
                  :rows-per-page-options="[10, 25, 0]"
                >
                  <template #body-cell-image="props">
                    <q-td :props="props" class="text-center">
                      <img :src="getFullLogoUrl(props.row.image)" style="height: 30px; max-width: 80px; object-fit: contain" class="bg-grey-2 rounded-borders q-pa-xs" />
                    </q-td>
                  </template>
                  <template #body-cell-settings="props">
                    <q-td :props="props">
                      <div class="text-caption">
                        {{ props.row.width }}x{{ props.row.height }}mm | {{ props.row.position }}
                        <div :style="{ color: props.row.theme_color }" class="text-weight-bold">
                          {{ props.row.theme_color }}
                        </div>
                      </div>
                    </q-td>
                  </template>
                  <template #body-cell-is_default="props">
                    <q-td :props="props" class="text-center">
                      <q-icon v-if="props.row.is_default" name="check_circle" color="primary" size="sm" />
                      <q-btn v-else flat round dense icon="radio_button_unchecked" color="grey-4" size="sm" @click="setAdminDefaultLogo(props.row.id)" />
                    </q-td>
                  </template>
                  <template #body-cell-logo_actions="props">
                    <q-td :props="props" class="text-center">
                      <q-btn flat round dense icon="edit" color="secondary" size="sm" @click="openEditLogo(props.row)">
                        <q-tooltip>Edytuj logo</q-tooltip>
                      </q-btn>
                      <q-btn flat round dense icon="delete" color="negative" size="sm" @click="deleteUserLogo(props.row.id)">
                        <q-tooltip>Usuń logo</q-tooltip>
                      </q-btn>
                    </q-td>
                  </template>
                </q-table>
              </q-card>
            </q-tab-panel>

            <!-- ---- PODPISY ---- -->
            <q-tab-panel name="podpisy" class="q-pa-none">
              <div class="row items-center q-mb-md">
                <div class="col">
                  <q-toggle
                    v-model="selectedUser.show_signature_on_pdf"
                    label="Pokazuj podpis na obliczeniu PDF dla tego użytkownika"
                    color="primary"
                    left-label
                    @update:model-value="updateUserPdfSettings"
                  />
                </div>
                <div class="col-auto">
                  <q-btn icon="draw" label="Dodaj podpis użytkownikowi" color="primary" unelevated no-caps
                    class="rounded-borders shadow-2" @click="openAdminAddSignature" />
                </div>
              </div>

              <div v-if="userSignaturesLoading" class="text-center q-pa-lg"><q-spinner color="primary" /></div>
              <q-card v-else flat bordered class="rounded-borders">
                <q-table
                  :rows="userSignatures"
                  :columns="userSignatureColumns"
                  row-key="id"
                  flat dense
                  no-data-label="Brak podpisów"
                  rows-per-page-label="Wierszy na stronę"
                  :rows-per-page-options="[10, 25, 0]"
                >
                  <template #body-cell-image="props">
                    <q-td :props="props" class="text-center">
                      <img :src="getFullLogoUrl(props.row.image)" style="height: 30px; max-width: 80px; object-fit: contain" class="bg-grey-2 rounded-borders q-pa-xs" />
                    </q-td>
                  </template>
                  <template #body-cell-settings="props">
                    <q-td :props="props">
                      <div class="text-caption">
                        {{ props.row.width }}x{{ props.row.height }}mm | {{ props.row.position }}
                      </div>
                    </q-td>
                  </template>
                  <template #body-cell-is_default="props">
                    <q-td :props="props" class="text-center">
                      <q-icon v-if="props.row.is_default" name="check_circle" color="primary" size="sm" />
                      <q-btn v-else flat round dense icon="radio_button_unchecked" color="grey-4" size="sm" @click="setAdminDefaultSignature(props.row.id)" />
                    </q-td>
                  </template>
                  <template #body-cell-sig_actions="props">
                    <q-td :props="props" class="text-center">
                      <q-btn flat round dense icon="delete" color="negative" size="sm" @click="deleteUserSignature(props.row.id)">
                        <q-tooltip>Usuń podpis</q-tooltip>
                      </q-btn>
                    </q-td>
                  </template>
                </q-table>
              </q-card>
            </q-tab-panel>

          </q-tab-panels>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG NOWEJ FAKTURY ===================== -->
    <q-dialog v-model="newInvoiceDialog" persistent>
      <q-card style="min-width:500px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Wystaw nową fakturę</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md" v-if="selectedUser">
          <div class="q-mb-md bg-blue-1 q-pa-sm rounded-borders text-primary row items-center">
            <q-icon name="person" class="q-mr-sm" />
            Dla: <b>{{ selectedUser.display_name }}</b> ({{ selectedUser.email }})
          </div>

          <q-form @submit="submitInvoice">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="invoice.service_name" label="Nazwa usługi na fakturze *" outlined dense
                  :rules="[v => !!v || 'Wymagane']" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="invoice.net_amount" label="Kwota netto (PLN) *" outlined dense
                  type="number" min="0" step="0.01" suffix="PLN"
                  @update:model-value="onNetUpdate"
                  :rules="[v => v > 0 || 'Kwota musi być większa od 0']" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="invoice.gross_amount" label="Kwota brutto (PLN) *" outlined dense
                  type="number" min="0" step="0.01" suffix="PLN"
                  @update:model-value="onGrossUpdate"
                  :rules="[v => v > 0 || 'Kwota musi być większa od 0']" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="invoice.points_to_add" label="Punkty do dodania *" outlined dense
                  type="number" min="0" suffix="pkt"
                  :rules="[v => v >= 0 || 'Nie może być ujemne']" />
              </div>
              <div class="col-12 col-sm-6">
                <q-select v-model="invoice.payment_terms" label="Warunki płatności *" outlined dense
                  :options="[
                    { label: 'Zapłacono przelewem', value: 'paid' },
                    { label: 'Do zapłaty w ciągu 7 dni', value: '7_days' },
                    { label: 'Do zapłaty w ciągu 14 dni', value: '14_days' },
                    { label: 'Do zapłaty w ciągu 30 dni', value: '30_days' }
                  ]"
                  emit-value map-options
                  :rules="[v => !!v || 'Wybierz warunki płatności']"
                  lazy-rules="ondemand" />
              </div>

              <!-- OPCJA SAMORZĄD -->
              <div class="col-12">
                <q-expansion-item
                  v-model="invoice.use_custom_buyer"
                  icon="business"
                  label="Inny Nabywca / Odbiorca (np. Samorząd)"
                  header-class="rounded-borders"
                  class="rounded-borders border-grey shadow-1"
                >
                  <q-card>
                    <q-card-section class="q-gutter-y-sm">
                      <div class="text-subtitle2 text-primary">Dane Nabywcy (Płatnik)</div>
                      <q-input v-model="invoice.buyer_name" label="Nazwa Nabywcy" outlined dense />
                      <q-input v-model="invoice.buyer_nip" label="NIP Nabywcy" outlined dense />
                      <q-input v-model="invoice.buyer_address" label="Adres Nabywcy" outlined dense type="textarea" rows="2" />
                      
                      <q-separator class="q-my-md" />
                      
                      <div class="text-subtitle2 text-secondary">Dane Odbiorcy (opcjonalnie)</div>
                      <q-input v-model="invoice.recipient_name" label="Nazwa Odbiorcy" outlined dense placeholder="Pozostaw puste, jeśli brak" />
                      <q-input v-model="invoice.recipient_address" label="Adres Odbiorcy" outlined dense type="textarea" rows="2" />
                    </q-card-section>
                  </q-card>
                </q-expansion-item>
              </div>

              <div class="col-12">
                <q-checkbox v-model="invoice.is_proforma" label="Wystaw jako PROFORMA (nie wysyłaj do KSeF)" color="primary" />
              </div>
              <div class="col-12" v-if="invoice.net_amount">
                <div class="bg-grey-2 q-pa-sm rounded-borders text-caption text-grey-8">
                  <div class="row justify-between">
                    <span>VAT (23%):</span><span>{{ formatAmount(invoice.net_amount * 0.23) }} PLN</span>
                  </div>
                  <div class="row justify-between text-weight-bold text-dark q-mt-xs">
                    <span>Łącznie brutto:</span><span>{{ formatAmount(invoice.net_amount * 1.23) }} PLN</span>
                  </div>
                </div>
              </div>
              <div class="col-12">
                <q-banner dense :class="invoice.is_proforma ? 'bg-grey-2 text-grey-8' : 'bg-blue-1 text-primary'" class="rounded-borders">
                  <template #avatar><q-icon :name="invoice.is_proforma ? 'description' : 'info'" :color="invoice.is_proforma ? 'grey-7' : 'primary'" /></template>
                  <span v-if="invoice.is_proforma">Dokument <strong>Proforma</strong> nie jest wysyłany do KSeF ani nie doładowuje punktów do czasu zatwierdzenia.</span>
                  <span v-else>Faktura zostanie wysłana do środowiska testowego <strong>KSeF</strong>.</span>
                </q-banner>
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Wystaw i doładuj punkty" color="primary" unelevated type="submit" :loading="invoiceLoading" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG FAKTURY KORYGUJĄCEJ ===================== -->
    <q-dialog v-model="correctionDialog" persistent>
      <q-card style="min-width:480px" class="rounded-borders">
        <q-card-section class="bg-warning text-white row items-center">
          <q-icon name="receipt" size="sm" class="q-mr-sm" />
          <div class="text-h6 text-weight-bold col">Faktura korygująca</div>
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md" v-if="correctionInvoice">
          <div class="q-mb-md bg-orange-1 q-pa-sm rounded-borders text-warning row items-center">
            <q-icon name="info" class="q-mr-sm" />
            Korekta do: <b class="q-ml-xs">{{ correctionInvoice.invoice_number }}</b>
            &nbsp;({{ formatAmount(correctionInvoice.gross_amount) }} PLN brutto)
          </div>

          <q-form @submit="submitCorrection">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6">
                <q-input
                  v-model.number="correctionForm.net_amount"
                  label="Skorygowana kwota netto (PLN) *"
                  outlined dense type="number" min="0" step="0.01" suffix="PLN"
                  @update:model-value="onNetUpdateCorrection"
                  hint="Wpisz kwotę po korekcie"
                  :rules="[v => v >= 0 || 'Kwota nie może być ujemna']"
                />
              </div>
              <div class="col-12 col-sm-6">
                <q-input
                  v-model.number="correctionForm.gross_amount"
                  label="Skorygowana kwota brutto (PLN) *"
                  outlined dense type="number" min="0" step="0.01" suffix="PLN"
                  @update:model-value="onGrossUpdateCorrection"
                  hint="Wpisz kwotę po korekcie"
                  :rules="[v => v >= 0 || 'Kwota nie może być ujemna']"
                />
              </div>
              <div class="col-12" v-if="correctionForm.net_amount !== null && correctionForm.net_amount >= 0">
                <div class="bg-grey-2 q-pa-sm rounded-borders text-caption text-grey-8">
                  <div class="row justify-between">
                    <span>VAT (23%):</span><span>{{ formatAmount(correctionForm.net_amount * 0.23) }} PLN</span>
                  </div>
                  <div class="row justify-between text-weight-bold text-dark q-mt-xs">
                    <span>Brutto po korekcie:</span><span>{{ formatAmount(correctionForm.net_amount * 1.23) }} PLN</span>
                  </div>
                </div>
              </div>
              <div class="col-12">
                <q-input
                  v-model="correctionForm.reason"
                  label="Powód korekty *"
                  outlined dense type="textarea" rows="3"
                  :rules="[v => !!v || 'Podaj powód korekty']"
                />
              </div>
              <div class="col-12">
                <q-banner dense class="bg-orange-1 text-warning rounded-borders">
                  <template #avatar><q-icon name="warning" color="warning" /></template>
                  Faktura korygująca zostanie wysłana do <strong>KSeF</strong> jako dokument ustrukturyzowany FA(3).
                </q-banner>
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Zatwierdź i wyślij do KSeF" color="warning" unelevated type="submit" :loading="correctionLoading" icon="send" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG SZCZEGÓŁÓW TRANSAKCJI ===================== -->
    <q-dialog v-model="txDetailOpen" maximized>
      <q-card v-if="selectedTx" style="max-width:860px;width:100%;margin:auto" class="rounded-borders">

        <q-card-section class="bg-primary text-white row items-center">
          <q-icon name="calculate" size="1.5rem" class="q-mr-sm" />
          <div>
            <div class="text-h6 text-weight-bold">{{ selectedTx.calculator_definition?.name || selectedTx.calculator_name }}</div>
            <div class="text-caption" style="opacity:.8">{{ formatDate(selectedTx.created_at) }}</div>
          </div>
          <q-space />
          <q-btn icon="content_copy" flat dense no-caps label="Kopiuj tekst" class="q-mr-xs" @click="copyTxToClipboard" />
          <q-btn icon="save" flat dense no-caps label="Na moje konto" class="q-mr-xs"
            :loading="copyLoading" @click="copyResultToAdmin">
            <q-tooltip>Zapisz obliczenie na swoje konto</q-tooltip>
          </q-btn>
          <q-btn v-if="selectedUser" icon="save" flat dense no-caps
            :label="`Zapisz do: ${selectedUser.display_name}`"
            class="q-mr-xs" :loading="copyToUserLoading" @click="copyResultToUser(selectedUser.id)">
            <q-tooltip>Zapisz obliczenie na konto użytkownika (widoczne w jego wynikach)</q-tooltip>
          </q-btn>
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pa-md" style="max-height:80vh;overflow-y:auto">

          <!-- Identyfikacja urządzenia (computed, bez v-if na elemencie v-for) -->
          <div class="text-subtitle2 text-weight-bold text-primary q-mb-xs">
            <q-icon name="info" class="q-mr-xs" />Identyfikacja urządzenia
          </div>
          <div class="row q-col-gutter-sm q-mb-md">
            <div v-for="item in filteredIdentFields" :key="item.key" class="col-6 col-md-4">
              <div class="ident-chip">
                <div class="text-caption text-grey-6">{{ item.label }}</div>
                <div class="text-weight-bold">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <q-separator class="q-mb-md" />

          <!-- Dane wejściowe -->
          <div class="text-subtitle2 text-weight-bold q-mb-sm">
            <q-icon name="input" color="secondary" class="q-mr-xs" />Dane wejściowe
          </div>
          <q-card flat bordered class="rounded-borders q-mb-md">
            <div v-for="(val, key) in nonIdentInputData" :key="key" class="data-row">
              <span class="data-key" v-html="fieldLabel(key)"></span>
              <span class="data-val">{{ formatVal(val) }}</span>
            </div>
          </q-card>

          <q-separator class="q-mb-md" />

          <!-- Wyniki -->
          <div class="text-subtitle2 text-weight-bold q-mb-sm">
            <q-icon name="assessment" color="positive" class="q-mr-xs" />Wyniki obliczeń
          </div>
          <div v-if="selectedTx.is_locked" class="text-center q-pa-md text-grey-6">
            <q-icon name="lock" size="2rem" />
            <div>Wyniki zablokowane — brak punktów premium</div>
          </div>
          <div v-if="selectedTx.output_data" class="q-mt-md">
            <div class="calc-section-bar q-mb-md">
              <q-icon name="assessment" size="14px" />
              Pełny raport obliczeń (widok użytkownika)
            </div>
            <q-card flat bordered class="q-pa-md bg-white text-black">
              <CalculationResultReport
                :result="selectedTx"
                :show-pdf-actions="false"
              />
            </q-card>
          </div>

          <q-card v-else flat bordered class="rounded-borders q-mb-md">
            <div v-for="(val, key) in selectedTx.output_data" :key="key"
              class="data-row" :class="isKeyResult(key) ? 'data-row--highlight' : ''">
              <span class="data-key" v-html="fieldLabel(key)"></span>
              <span class="data-val text-weight-bold">{{ formatVal(val) }}</span>
            </div>
          </q-card>

          <!-- Tekst do wysłania -->
          <q-separator class="q-mb-md" />
          <div class="text-subtitle2 text-weight-bold q-mb-sm">
            <q-icon name="send" color="info" class="q-mr-xs" />Tekst do wysłania klientowi
          </div>
          <q-input
            :model-value="txSummaryText"
            type="textarea"
            outlined readonly
            rows="10"
            class="font-mono"
          >
            <template #append>
              <q-btn flat round dense icon="content_copy" color="grey-7" @click="copyText(txSummaryText)">
                <q-tooltip>Kopiuj</q-tooltip>
              </q-btn>
            </template>
          </q-input>

        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG TWORZENIA UŻYTKOWNIKA ===================== -->
    <q-dialog v-model="createUserDialog" persistent>
      <q-card style="min-width:500px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Dodaj użytkownika</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md">
          <q-form @submit="submitCreateUser">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="newUser.email" label="Email *" outlined dense type="email"
                  :rules="[v => !!v || 'Wymagane']" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="newUser.first_name" label="Imię" outlined dense />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="newUser.last_name" label="Nazwisko" outlined dense />
              </div>
              <div class="col-12">
                <q-toggle v-model="newUser.is_company" label="Konto firmowe" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="newUser.company_name" :label="newUser.is_company ? 'Nazwa firmy *' : 'Nazwa firmy'"
                  outlined dense />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="newUser.nip" :label="newUser.is_company ? 'NIP *' : 'NIP (opcjonalnie)'"
                  outlined dense />
              </div>
              <div class="col-12">
                <q-input v-model="newUser.address_line" label="Adres" outlined dense />
              </div>
              <div class="col-6 col-sm-4">
                <q-input v-model="newUser.postal_code" label="Kod pocztowy" outlined dense />
              </div>
              <div class="col-6 col-sm-8">
                <q-input v-model="newUser.city" label="Miasto" outlined dense />
              </div>
              <div class="col-12 col-sm-8">
                <q-input v-model="newUser.password" label="Hasło (puste = auto)" outlined dense type="password"
                  hint="Min. 8 znaków. Puste = automatyczne." />
              </div>
              <div class="col-12 col-sm-4">
                <q-input v-model.number="newUser.premium" label="Punkty startowe" outlined dense type="number" min="0" suffix="pkt" />
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Utwórz użytkownika" color="primary" unelevated type="submit" :loading="createLoading" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG EDYCJI UŻYTKOWNIKA ===================== -->
    <q-dialog v-model="editUserDialog" persistent>
      <q-card style="min-width:500px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div>
            <div class="text-h6 text-weight-bold">Edytuj użytkownika</div>
            <div class="text-caption" style="opacity:.8">{{ editUser?.email }}</div>
          </div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md" v-if="editUser">
          <q-form @submit="submitEditUser">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6">
                <q-input v-model="editUser.first_name" label="Imię" outlined dense />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="editUser.last_name" label="Nazwisko" outlined dense />
              </div>
              <div class="col-12">
                <q-toggle v-model="editUser.is_company" label="Konto firmowe" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="editUser.company_name" label="Nazwa firmy" outlined dense />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model="editUser.nip" label="NIP" outlined dense />
              </div>
              <div class="col-12">
                <q-input v-model="editUser.address_line" label="Adres" outlined dense />
              </div>
              <div class="col-6 col-sm-4">
                <q-input v-model="editUser.postal_code" label="Kod pocztowy" outlined dense />
              </div>
              <div class="col-6 col-sm-8">
                <q-input v-model="editUser.city" label="Miasto" outlined dense />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="editUser.premium" label="Punkty Premium" outlined dense type="number" min="0" suffix="pkt" />
              </div>
              <div class="col-12 col-sm-6">
                <q-input v-model.number="editUser.discount_percent" label="Zniżka procentowa (%)" outlined dense type="number" min="0" max="100" suffix="%" />
              </div>
              <div class="col-12 col-sm-6 self-center q-gutter-x-md">
                <q-toggle v-model="editUser.is_active" label="Konto aktywne" />
              </div>
              <div class="col-12">
                <q-separator class="q-my-sm" />
                <div class="text-subtitle2 text-weight-bold q-mb-xs">Ustawienia PDF</div>
                <div class="row q-col-gutter-sm">
                  <div class="col-6">
                    <q-toggle v-model="editUser.show_logo_on_pdf" label="Pokazuj logo" dense />
                  </div>
                  <div class="col-6">
                    <q-toggle v-model="editUser.show_signature_on_pdf" label="Pokazuj podpis" dense />
                  </div>
                </div>
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Zapisz zmiany" color="primary" unelevated type="submit" :loading="editLoading" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG: PRZEKAŻ MOJE OBLICZENIE ===================== -->
    <q-dialog v-model="pickMyResultDialog" persistent style="max-width:800px">
      <q-card style="width:760px;max-width:95vw" class="rounded-borders">
        <q-card-section class="bg-secondary text-white row items-center q-pb-none">
          <q-icon name="upload" size="1.3rem" class="q-mr-sm" />
          <div>
            <div class="text-h6 text-weight-bold">Przekaż moje obliczenie</div>
            <div class="text-caption" style="opacity:.85">Do: {{ selectedUser?.display_name }}</div>
          </div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md q-pb-none">
          <q-input v-model="myResultSearch" outlined dense clearable placeholder="Szukaj: kalkulator, nr fabryczny…">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
        </q-card-section>

        <q-card-section style="max-height:55vh;overflow-y:auto" class="q-pt-sm">
          <div v-if="myResultsLoading" class="text-center q-pa-lg">
            <q-spinner color="secondary" size="2rem" />
          </div>
          <div v-else-if="filteredMyResults.length === 0" class="text-center text-grey-6 q-pa-lg">
            <q-icon name="inbox" size="2rem" /><div class="q-mt-xs">Brak własnych obliczeń</div>
          </div>
          <q-list v-else separator bordered class="rounded-borders">
            <q-item
              v-for="r in filteredMyResults" :key="r.id"
              clickable
              :active="selectedMyResult?.id === r.id"
              active-class="bg-blue-1 text-primary"
              @click="selectedMyResult = r"
            >
              <q-item-section avatar>
                <q-icon name="calculate" :color="selectedMyResult?.id === r.id ? 'primary' : 'grey-5'" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">
                  {{ r.calculator_definition?.name || r.calculator_name }}
                </q-item-label>
                <q-item-label caption>
                  <span v-if="getField(r, 'nr_fabryczny')">Nr fab: <b>{{ getField(r, 'nr_fabryczny') }}</b> &bull; </span>
                  {{ formatDate(r.created_at) }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-chip :color="r.is_locked ? 'negative' : 'positive'" text-color="white" size="xs" dense>
                  {{ r.is_locked ? 'Zablok.' : 'OK' }}
                </q-chip>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-section class="q-pt-sm">
          <div class="row justify-end q-gutter-sm items-center">
            <span v-if="selectedMyResult" class="text-caption text-grey-7 q-mr-auto">
              Wybrano: <b>{{ selectedMyResult.calculator_definition?.name || selectedMyResult.calculator_name }}</b>
            </span>
            <q-btn flat label="Anuluj" v-close-popup />
            <q-btn
              icon="save" label="Zapisz do użytkownika" color="secondary" unelevated
              :disable="!selectedMyResult" :loading="pickLoading"
              @click="confirmPickMyResult"
            />
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG DODAWANIA LOGA PRZEZ ADMINA ===================== -->
    <q-dialog v-model="adminLogoDialog" persistent>
      <q-card style="min-width:400px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Dodaj logo użytkownikowi</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md" v-if="selectedUser">
          <div class="q-mb-md bg-blue-1 q-pa-sm rounded-borders text-primary row items-center">
            <q-icon name="person" class="q-mr-sm" />
            Dla: <b>{{ selectedUser.display_name }}</b>
          </div>

          <q-form @submit="handleAdminLogoSubmit">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="adminLogoForm.name" label="Nazwa własna loga" outlined dense />
              </div>
              <div class="col-12">
                <q-file v-model="adminLogoForm.imageFile" label="Plik loga (PNG/JPG)" outlined dense accept=".jpg,.jpeg,.png" :rules="[v => !!v || 'Wymagane']">
                  <template #prepend><q-icon name="attach_file" /></template>
                </q-file>
              </div>
              <div class="col-6">
                <q-input v-model.number="adminLogoForm.width" label="Szerokość (mm)" type="number" outlined dense />
              </div>
              <div class="col-6">
                <q-input v-model.number="adminLogoForm.height" label="Wysokość (mm)" type="number" outlined dense />
              </div>
              <div class="col-12">
                <q-select v-model="adminLogoForm.position" label="Pozycja" outlined dense emit-value map-options
                  :options="[ {label:'Lewo', value:'left'}, {label:'Góra', value:'top_center'}, {label:'Prawo', value:'right'} ]" />
              </div>
              <div class="col-12">
                <q-input v-model="adminLogoForm.theme_color" label="Kolor motywu" outlined dense readonly class="cursor-pointer">
                  <template v-slot:append>
                    <q-icon name="colorize" class="cursor-pointer" color="primary">
                      <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                        <q-color v-model="adminLogoForm.theme_color" no-header-footer />
                      </q-popup-proxy>
                    </q-icon>
                  </template>
                </q-input>
              </div>
              <div class="col-12">
                <q-checkbox v-model="adminLogoForm.is_default" label="Ustaw jako domyślne" />
              </div>
              <div class="col-12">
                <q-banner dense class="bg-blue-1 text-primary rounded-borders">
                  Dodanie loga przez admina <b>nie pobiera punktów</b> z konta użytkownika.
                </q-banner>
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Dodaj logo" color="primary" unelevated type="submit" :loading="adminLogoLoading" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG EDYCJI LOGA PRZEZ ADMINA ===================== -->
    <q-dialog v-model="editLogoDialog" persistent>
      <q-card style="min-width:380px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Edytuj logo</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md">
          <q-form @submit="handleEditLogoSubmit">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="editLogoForm.name" label="Nazwa własna loga" outlined dense />
              </div>
              <div class="col-6">
                <q-input v-model.number="editLogoForm.width" label="Szerokość (mm)" type="number" outlined dense />
              </div>
              <div class="col-6">
                <q-input v-model.number="editLogoForm.height" label="Wysokość (mm)" type="number" outlined dense />
              </div>
              <div class="col-12">
                <q-select v-model="editLogoForm.position" label="Pozycja" outlined dense emit-value map-options
                  :options="[ {label:'Lewo', value:'left'}, {label:'Góra', value:'top_center'}, {label:'Prawo', value:'right'} ]" />
              </div>
              <div class="col-12">
                <q-input v-model="editLogoForm.theme_color" label="Kolor motywu" outlined dense readonly class="cursor-pointer">
                  <template v-slot:append>
                    <q-icon name="colorize" class="cursor-pointer" color="primary">
                      <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                        <q-color v-model="editLogoForm.theme_color" no-header-footer />
                      </q-popup-proxy>
                    </q-icon>
                  </template>
                </q-input>
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Zapisz zmiany" color="primary" unelevated type="submit" :loading="editLogoLoading" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ===================== DIALOG DODAWANIA PODPISU PRZEZ ADMINA ===================== -->
    <q-dialog v-model="adminSignatureDialog" persistent>
      <q-card style="min-width:400px" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Dodaj podpis użytkownikowi</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md" v-if="selectedUser">
          <div class="q-mb-md bg-blue-1 q-pa-sm rounded-borders text-primary row items-center">
            <q-icon name="person" class="q-mr-sm" />
            Dla: <b>{{ selectedUser.display_name }}</b>
          </div>

          <q-form @submit="handleAdminSignatureSubmit">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="adminSignatureForm.name" label="Opis podpisu (np. Jan Kowalski)" outlined dense />
              </div>
              <div class="col-12">
                <q-file v-model="adminSignatureForm.imageFile" label="Plik podpisu/pieczątki" outlined dense accept=".jpg,.jpeg,.png" :rules="[v => !!v || 'Wymagane']">
                  <template #prepend><q-icon name="draw" /></template>
                </q-file>
              </div>
              <div class="col-6">
                <q-input v-model.number="adminSignatureForm.width" label="Szerokość (mm)" type="number" outlined dense />
              </div>
              <div class="col-6">
                <q-input v-model.number="adminSignatureForm.height" label="Wysokość (mm)" type="number" outlined dense />
              </div>
              <div class="col-12">
                <q-select v-model="adminSignatureForm.position" label="Pozycja (na dole)" outlined dense emit-value map-options
                  :options="[ {label:'Lewo', value:'bottom_left'}, {label:'Środek', value:'bottom_center'}, {label:'Prawo', value:'bottom_right'} ]" />
              </div>
              <div class="col-12">
                <q-checkbox v-model="adminSignatureForm.is_default" label="Ustaw jako domyślne" />
              </div>
              <div class="col-12">
                <div class="row justify-end q-gutter-sm">
                  <q-btn flat label="Anuluj" v-close-popup />
                  <q-btn label="Dodaj podpis" color="primary" unelevated type="submit" :loading="adminSignatureLoading" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { downloadBlob } from 'src/utils/download'
import VueApexCharts from 'vue3-apexcharts'
import CalculationResultReport from 'components/CalculationResultReport.vue'

const $q = useQuasar()
const ksefSandbox = ref(true)

// ---- Zakładki ----
const mainTab = ref('users')
const detailTab = ref('obliczenia')

// ---- Statystyki ----
const stats = ref(null)
const statsLoading = ref(false)

const statsCards = computed(() => {
  if (!stats.value) return []
  return [
    { icon: 'group', color: 'primary', value: stats.value.total_users, label: 'Wszystkich użytkowników' },
    { icon: 'person_check', color: 'secondary', value: stats.value.active_this_month, label: 'Aktywnych w tym miesiącu' },
    { icon: 'person_add', color: 'positive', value: stats.value.new_this_month, label: 'Nowych w tym miesiącu' },
    { icon: 'swap_horiz', color: 'info', value: stats.value.total_transactions, label: 'Wszystkich obliczeń' },
    { icon: 'calculate', color: 'orange', value: stats.value.transactions_this_month, label: 'Obliczeń w tym miesiącu' },
    { icon: 'payments', color: 'positive', value: formatAmount(stats.value.total_revenue) + ' zł', label: 'Łączny przychód brutto' },
    { icon: 'trending_up', color: 'teal', value: formatAmount(stats.value.revenue_this_month) + ' zł', label: 'Przychód w tym miesiącu' },
  ]
})

// Logika wykresów trendów
const activitySeries = computed(() => {
  if (!stats.value?.monthly_trends) return []
  return [
    { name: 'Nowi użytkownicy', data: stats.value.monthly_trends.map(t => t.users) },
    { name: 'Obliczenia', data: stats.value.monthly_trends.map(t => t.transactions) }
  ]
})

const revenueSeries = computed(() => {
  if (!stats.value?.monthly_trends) return []
  return [
    { name: 'Przychód (PLN)', data: stats.value.monthly_trends.map(t => t.revenue) }
  ]
})

const trendChartOptions = computed(() => ({
  chart: { 
    toolbar: { show: false }, 
    zoom: { enabled: false },
    foreColor: $q.dark.isActive ? '#9e9e9e' : '#616161'
  },
  stroke: { curve: 'smooth', width: 3 },
  xaxis: { 
    categories: stats.value?.monthly_trends?.map(t => t.label) || [],
    labels: { style: { colors: $q.dark.isActive ? '#9e9e9e' : '#616161' } }
  },
  yaxis: {
    labels: { style: { colors: $q.dark.isActive ? '#9e9e9e' : '#616161' } }
  },
  grid: { borderColor: $q.dark.isActive ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' },
  colors: ['#1565C0', '#F57C00'],
  markers: { size: 4 },
  legend: { labels: { colors: $q.dark.isActive ? '#e0e0e0' : '#424242' } },
  tooltip: { theme: $q.dark.isActive ? 'dark' : 'light' }
}))

const revenueChartOptions = computed(() => ({
  chart: { 
    toolbar: { show: false },
    foreColor: $q.dark.isActive ? '#9e9e9e' : '#616161'
  },
  stroke: { curve: 'area', width: 2 },
  fill: { type: 'solid', opacity: 1 },
  xaxis: { 
    categories: stats.value?.monthly_trends?.map(t => t.label) || [],
    labels: { style: { colors: $q.dark.isActive ? '#9e9e9e' : '#616161' } }
  },
  yaxis: { 
    labels: { 
      formatter: (v) => formatAmount(v) + ' zł',
      style: { colors: $q.dark.isActive ? '#9e9e9e' : '#616161' }
    } 
  },
  grid: { borderColor: $q.dark.isActive ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' },
  colors: ['#2E7D32'],
  tooltip: { theme: $q.dark.isActive ? 'dark' : 'light' }
}))

async function fetchStats() {
  statsLoading.value = true
  try {
    const { data } = await api.get('/auth/admin/users/stats/')
    stats.value = data
  } finally {
    statsLoading.value = false
  }
}

// ---- Użytkownicy ----
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const userFilterActive = ref(null)
const userFilterCompany = ref(null)

const activeOptions = [
  { label: 'Wszyscy', value: null },
  { label: 'Aktywni', value: 'true' },
  { label: 'Nieaktywni', value: 'false' },
]
const companyOptions = [
  { label: 'Wszyscy', value: null },
  { label: 'Firmy', value: 'true' },
  { label: 'Osoby', value: 'false' },
]

const userColumns = [
  { name: 'display_name', label: 'Nazwa / Email', field: 'display_name', align: 'left', sortable: true },
  { name: 'account_type', label: 'Typ', field: 'is_company', align: 'center' },
  { name: 'nip', label: 'NIP', field: 'nip', align: 'left' },
  { name: 'premium', label: 'Punkty', field: 'premium', align: 'center', sortable: true },
  { name: 'transaction_count', label: 'Obl.', field: 'transaction_count', align: 'center', sortable: true },
  { name: 'invoice_count', label: 'Fakt.', field: 'invoice_count', align: 'center', sortable: true },
  { name: 'last_login', label: 'Ost. logowanie', field: 'last_login', align: 'left', sortable: true },
  { name: 'is_active', label: 'Akt.', field: 'is_active', align: 'center' },
  { name: 'actions', label: 'Akcje', field: 'id', align: 'center' },
]

async function fetchUsers() {
  usersLoading.value = true
  try {
    const params = {}
    if (userSearch.value) params.search = userSearch.value
    if (userFilterActive.value !== null) params.is_active = userFilterActive.value
    if (userFilterCompany.value !== null) params.is_company = userFilterCompany.value
    const { data } = await api.get('/auth/admin/users/', { params })
    users.value = data
  } finally {
    usersLoading.value = false
  }
}

// ---- Szczegóły użytkownika ----
const userDetailOpen = ref(false)
const selectedUser = ref(null)

function openUserDetail(user) {
  selectedUser.value = user
  detailTab.value = 'obliczenia'
  userDetailOpen.value = true
  fetchUserTransactions()
  fetchUserInvoices()
  fetchUserLogos()
  fetchUserSignatures()
}

// ---- Transakcje użytkownika ----
const userTransactions = ref([])
const userTxLoading = ref(false)
const detailTxYear = ref(null)
const detailTxMonth = ref(null)
const detailTxSearch = ref('')

const userTxColumns = [
  { name: 'device', label: 'Urządzenie / identyfikacja', field: 'id', align: 'left' },
  { name: 'result', label: 'Wynik', field: 'id', align: 'left' },
  { name: 'is_locked', label: 'Status', field: 'is_locked', align: 'center' },
  { name: 'created_at', label: 'Data', field: 'created_at', align: 'left', sortable: true },
  { name: 'tx_actions', label: '', field: 'id', align: 'center' },
]

async function fetchUserTransactions() {
  if (!selectedUser.value) return
  userTxLoading.value = true
  try {
    const params = {}
    if (detailTxYear.value) params.year = detailTxYear.value
    if (detailTxMonth.value) params.month = detailTxMonth.value
    if (detailTxSearch.value) params.search = detailTxSearch.value
    const { data } = await api.get(`/auth/admin/users/${selectedUser.value.id}/transactions/`, { params })
    userTransactions.value = data
  } finally {
    userTxLoading.value = false
  }
}

// ---- Faktury użytkownika ----
const userInvoices = ref([])
const userInvLoading = ref(false)
const newInvoiceDialog = ref(false)
const invoiceLoading = ref(false)
const invoice = ref({
  net_amount: null,
  gross_amount: null,
  points_to_add: 100,
  is_proforma: false,
  service_name: 'Wyznaczenie resursu UTB GTU_12',
  use_custom_buyer: false,
  buyer_name: '',
  buyer_nip: '',
  buyer_address: '',
  recipient_name: '',
  recipient_address: '',
  payment_terms: null
})

function onNetUpdate(val) {
  if (val && val > 0) {
    const gross = Number((val * 1.23).toFixed(2))
    invoice.value.gross_amount = gross
    invoice.value.points_to_add = Math.round(gross)
  } else if (!val) {
    invoice.value.gross_amount = null
  }
}

function onGrossUpdate(val) {
  if (val && val > 0) {
    invoice.value.net_amount = Number((val / 1.23).toFixed(2))
    invoice.value.points_to_add = Math.round(val)
  } else if (!val) {
    invoice.value.net_amount = null
  }
}

function openNewInvoiceForUser() {
  const buyer = selectedUser.value
  const name = buyer.company_name || `${buyer.first_name || ''} ${buyer.last_name || ''}`.trim() || buyer.email
  const addr = [buyer.address_line, `${buyer.postal_code || ''} ${buyer.city || ''}`.trim()].filter(Boolean).join(', ')

  invoice.value = {
    net_amount: null,
    gross_amount: null,
    points_to_add: 100,
    is_proforma: false,
    service_name: 'Wyznaczenie resursu UTB GTU_12',
    use_custom_buyer: false,
    buyer_name: name,
    buyer_nip: buyer.nip || '',
    buyer_address: addr,
    recipient_name: '',
    recipient_address: '',
    payment_terms: null
  }
  newInvoiceDialog.value = true
}

async function submitInvoice() {
  if (!selectedUser.value) return
  invoiceLoading.value = true
  try {
    const payload = {
      user_id: selectedUser.value.id,
      net_amount: invoice.value.net_amount,
      gross_amount: invoice.value.gross_amount,
      points_to_add: invoice.value.points_to_add,
      is_proforma: invoice.value.is_proforma,
      service_name: invoice.value.service_name,
      buyer_name: invoice.value.buyer_name,
      buyer_nip: invoice.value.buyer_nip,
      buyer_address: invoice.value.buyer_address,
      recipient_name: invoice.value.recipient_name,
      recipient_address: invoice.value.recipient_address,
      payment_terms: invoice.value.payment_terms
    }
    await api.post('/billing/invoices/', payload, { timeout: 300000 })
    $q.notify({ type: 'positive', message: invoice.value.is_proforma ? 'Wystawiono proformę.' : 'Faktura wystawiona.', position: 'top' })
    newInvoiceDialog.value = false
    fetchUserInvoices()
    
    if (!invoice.value.is_proforma) {
      const { data } = await api.get(`/auth/admin/users/${selectedUser.value.id}/`)
      selectedUser.value = data
      const idx = users.value.findIndex(u => u.id === data.id)
      if (idx !== -1) users.value[idx] = data
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd wystawiania faktury.', position: 'top' })
  } finally {
    invoiceLoading.value = false
  }
}

async function approveProforma(inv) {
  $q.dialog({
    title: 'Zatwierdź proformę',
    message: `Czy na pewno chcesz przekształcić proformę <b>${inv.invoice_number}</b> w fakturę ostateczną i wysłać ją do KSeF?`,
    html: true,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.post(`/billing/invoices/${inv.id}/approve_proforma/`, {}, { timeout: 300000 })
      $q.notify({ type: 'positive', message: 'Faktura zatwierdzona i wysłana do KSeF.', position: 'top' })
      fetchUserInvoices()
      const { data } = await api.get(`/auth/admin/users/${selectedUser.value.id}/`)
      selectedUser.value = data
    } catch {
      $q.notify({ type: 'negative', message: 'Błąd podczas zatwierdzania faktury.', position: 'top' })
    }
  })
}

// ---- Faktura korygująca ----
const correctionDialog = ref(false)
const correctionInvoice = ref(null)
const correctionLoading = ref(false)
const correctionForm = ref({ net_amount: null, gross_amount: null, reason: '' })

function onNetUpdateCorrection(val) {
  if (val !== null && val >= 0) {
    correctionForm.value.gross_amount = Number((val * 1.23).toFixed(2))
  } else {
    correctionForm.value.gross_amount = null
  }
}

function onGrossUpdateCorrection(val) {
  if (val !== null && val >= 0) {
    correctionForm.value.net_amount = Number((val / 1.23).toFixed(2))
  } else {
    correctionForm.value.net_amount = null
  }
}

function startCorrection(inv) {
  $q.dialog({
    title: 'Faktura korygująca',
    message: `Czy chcesz wystawić fakturę korygującą do <b>${inv.invoice_number}</b>?`,
    html: true,
    cancel: true,
    persistent: true
  }).onOk(() => {
    correctionInvoice.value = inv
    correctionForm.value = { net_amount: null, gross_amount: null, reason: '' }
    correctionDialog.value = true
  })
}

async function submitCorrection() {
  $q.dialog({
    title: 'Potwierdź wysyłkę do KSeF',
    message: 'Czy na pewno wysłać fakturę korygującą do KSeF? Operacja jest nieodwracalna.',
    cancel: true,
    persistent: true,
    ok: { label: 'Wyślij do KSeF', color: 'warning', unelevated: true }
  }).onOk(async () => {
    correctionLoading.value = true
    try {
      await api.post(`/billing/invoices/${correctionInvoice.value.id}/issue_correction/`, {
        net_amount: correctionForm.value.net_amount,
        gross_amount: correctionForm.value.gross_amount,
        reason: correctionForm.value.reason
      }, { timeout: 300000 })
      $q.notify({ type: 'positive', message: 'Faktura korygująca wystawiona i wysłana do KSeF.', position: 'top' })
      correctionDialog.value = false
      fetchUserInvoices()
    } catch (e) {
      $q.notify({ type: 'negative', message: e.response?.data?.detail || 'Błąd wystawiania korekty.', position: 'top' })
    } finally {
      correctionLoading.value = false
    }
  })
}

const userInvColumns = [
  { name: 'invoice_number', label: 'Nr faktury', field: 'invoice_number', align: 'left', sortable: true },
  { name: 'issue_date', label: 'Data', field: 'issue_date', align: 'left', sortable: true },
  { name: 'gross_amount', label: 'Brutto', field: 'gross_amount', align: 'right', sortable: true },
  { name: 'points_added', label: 'Pkt', field: 'points_added', align: 'center' },
  { name: 'ksef_status', label: 'Status KSeF', field: 'ksef_status', align: 'center' },
  { name: 'inv_actions', label: '', field: 'id', align: 'center' },
]

async function fetchUserInvoices() {
  if (!selectedUser.value) return
  userInvLoading.value = true
  try {
    const { data } = await api.get('/billing/invoices/', { params: { user_id: selectedUser.value.id } })
    userInvoices.value = data
  } finally {
    userInvLoading.value = false
  }
}

// ---- Logotypy użytkownika (Zarządzanie przez admina) ----
const userLogos = ref([])
const userLogosLoading = ref(false)
const adminLogoDialog = ref(false)
const adminLogoLoading = ref(false)
const adminLogoForm = ref({
  name: '',
  imageFile: null,
  width: 45,
  height: 20,
  position: 'right',
  theme_color: '#1565C0',
  is_default: false
})

const userLogoColumns = [
  { name: 'image', label: 'Podgląd', field: 'image', align: 'center' },
  { name: 'name', label: 'Nazwa', field: 'name', align: 'left' },
  { name: 'settings', label: 'Ustawienia (mm/poz)', field: 'id', align: 'left' },
  { name: 'is_default', label: 'Domyślne', field: 'is_default', align: 'center' },
  { name: 'logo_actions', label: 'Akcje', field: 'id', align: 'center' },
]

async function fetchUserLogos() {
  if (!selectedUser.value) return
  userLogosLoading.value = true
  try {
    const { data } = await api.get(`/auth/admin/users/${selectedUser.value.id}/logos/`)
    userLogos.value = data
  } finally {
    userLogosLoading.value = false
  }
}

function openAdminAddLogo() {
  adminLogoForm.value = {
    name: '',
    imageFile: null,
    width: 45,
    height: 20,
    position: 'right',
    theme_color: '#1565C0',
    is_default: userLogos.value.length === 0
  }
  adminLogoDialog.value = true
}

async function handleAdminLogoSubmit() {
  if (!selectedUser.value) return
  adminLogoLoading.value = true
  const formData = new FormData()
  if (adminLogoForm.value.name) formData.append('name', adminLogoForm.value.name)
  formData.append('image', adminLogoForm.value.imageFile)
  formData.append('width', adminLogoForm.value.width)
  formData.append('height', adminLogoForm.value.height)
  formData.append('position', adminLogoForm.value.position)
  formData.append('theme_color', adminLogoForm.value.theme_color)
  formData.append('is_default', adminLogoForm.value.is_default)

  try {
    await api.post(`/auth/admin/users/${selectedUser.value.id}/logos/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    $q.notify({ type: 'positive', message: 'Logo dodane użytkownikowi.', position: 'top' })
    adminLogoDialog.value = false
    fetchUserLogos()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas dodawania loga.', position: 'top' })
  } finally {
    adminLogoLoading.value = false
  }
}

async function deleteUserLogo(logoId) {
  $q.dialog({
    title: 'Usuń logo',
    message: 'Czy na pewno chcesz usunąć to logo użytkownika?',
    cancel: true,
    persistent: true,
    ok: { color: 'negative', label: 'Usuń' }
  }).onOk(async () => {
    try {
      await api.delete(`/auth/logos/${logoId}/`)
      $q.notify({ type: 'positive', message: 'Logo usunięte.', position: 'top' })
      fetchUserLogos()
    } catch {
      $q.notify({ type: 'negative', message: 'Błąd podczas usuwania loga.', position: 'top' })
    }
  })
}

async function setAdminDefaultLogo(logoId) {
  try {
    await api.post(`/auth/logos/${logoId}/set_default/`)
    $q.notify({ type: 'positive', message: 'Logo ustawione jako domyślne.', position: 'top' })
    fetchUserLogos()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas ustawiania domyślnego loga.', position: 'top' })
  }
}

// ---- Edycja logo ----
const editLogoDialog = ref(false)
const editLogoLoading = ref(false)
const editLogoId = ref(null)
const editLogoForm = ref({ name: '', width: 45, height: 20, position: 'right', theme_color: '#1565C0' })

function openEditLogo(row) {
  editLogoId.value = row.id
  editLogoForm.value = { name: row.name || '', width: row.width, height: row.height, position: row.position, theme_color: row.theme_color }
  editLogoDialog.value = true
}

async function handleEditLogoSubmit() {
  editLogoLoading.value = true
  try {
    await api.patch(`/auth/logos/${editLogoId.value}/`, editLogoForm.value)
    $q.notify({ type: 'positive', message: 'Logo zaktualizowane.', position: 'top' })
    editLogoDialog.value = false
    fetchUserLogos()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas edycji loga.', position: 'top' })
  } finally {
    editLogoLoading.value = false
  }
}

// ---- Podgląd wydruku użytkownika ----
const pdfLoadingId = ref(null)

async function downloadUserResultPdf(result) {
  pdfLoadingId.value = result.id
  try {
    const res = await api.get(`/calculators/results/${result.id}/pdf/`, {
      params: { use_owner_logo: 'true' },
      responseType: 'blob'
    })
    const calcName = (result.calculator_definition?.name || result.calculator_name || 'obliczenie').replace(/[^a-zA-Z0-9_-]/g, '_')
    const rawNr = result.nr_fabryczny || result.input_data?.nr_fabryczny?.value || result.input_data?.nr_fabryczny || String(result.id)
    const nrFab = String(rawNr).replace(/[^a-zA-Z0-9_-]/g, '_')
    downloadBlob(res.data, `${calcName}_${nrFab}.pdf`)
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd pobierania PDF.', position: 'top' })
  } finally {
    pdfLoadingId.value = null
  }
}

// ---- Podpisy użytkownika (Zarządzanie przez admina) ----
const userSignatures = ref([])
const userSignaturesLoading = ref(false)
const adminSignatureDialog = ref(false)
const adminSignatureLoading = ref(false)
const adminSignatureForm = ref({
  name: '',
  imageFile: null,
  width: 60,
  height: 30,
  position: 'bottom_right',
  is_default: false
})

const userSignatureColumns = [
  { name: 'image', label: 'Podgląd', field: 'image', align: 'center' },
  { name: 'name', label: 'Nazwa/Opis', field: 'name', align: 'left' },
  { name: 'settings', label: 'Ustawienia (mm/poz)', field: 'id', align: 'left' },
  { name: 'is_default', label: 'Domyślne', field: 'is_default', align: 'center' },
  { name: 'sig_actions', label: 'Akcje', field: 'id', align: 'center' },
]

async function fetchUserSignatures() {
  if (!selectedUser.value) return
  userSignaturesLoading.value = true
  try {
    const { data } = await api.get(`/auth/admin/users/${selectedUser.value.id}/signatures/`)
    userSignatures.value = data
  } finally {
    userSignaturesLoading.value = false
  }
}

function openAdminAddSignature() {
  adminSignatureForm.value = {
    name: '',
    imageFile: null,
    width: 60,
    height: 30,
    position: 'bottom_right',
    is_default: userSignatures.value.length === 0
  }
  adminSignatureDialog.value = true
}

async function handleAdminSignatureSubmit() {
  if (!selectedUser.value) return
  adminSignatureLoading.value = true
  const formData = new FormData()
  if (adminSignatureForm.value.name) formData.append('name', adminSignatureForm.value.name)
  formData.append('image', adminSignatureForm.value.imageFile)
  formData.append('width', adminSignatureForm.value.width)
  formData.append('height', adminSignatureForm.value.height)
  formData.append('position', adminSignatureForm.value.position)
  formData.append('is_default', adminSignatureForm.value.is_default)

  try {
    await api.post(`/auth/admin/users/${selectedUser.value.id}/signatures/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    $q.notify({ type: 'positive', message: 'Podpis dodany użytkownikowi.', position: 'top' })
    adminSignatureDialog.value = false
    fetchUserSignatures()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas dodawania podpisu.', position: 'top' })
  } finally {
    adminSignatureLoading.value = false
  }
}

async function deleteUserSignature(sigId) {
  $q.dialog({
    title: 'Usuń podpis',
    message: 'Czy na pewno chcesz usunąć ten podpis użytkownika?',
    cancel: true,
    persistent: true,
    ok: { color: 'negative', label: 'Usuń' }
  }).onOk(async () => {
    try {
      await api.delete(`/auth/signatures/${sigId}/`)
      $q.notify({ type: 'positive', message: 'Podpis usunięty.', position: 'top' })
      fetchUserSignatures()
    } catch {
      $q.notify({ type: 'negative', message: 'Błąd podczas usuwania podpisu.', position: 'top' })
    }
  })
}

async function setAdminDefaultSignature(sigId) {
  try {
    await api.post(`/auth/signatures/${sigId}/set_default/`)
    $q.notify({ type: 'positive', message: 'Podpis ustawiony jako domyślny.', position: 'top' })
    fetchUserSignatures()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas ustawiania domyślnego podpisu.', position: 'top' })
  }
}

function getFullLogoUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const base = api.defaults.baseURL.replace(/\/api\/?$/, '')
  const path = url.startsWith('/') ? url : '/' + url
  return `${base}${path}`
}

// ---- Dialog szczegółów transakcji ----
const txDetailOpen = ref(false)
const selectedTx = ref(null)

function openTxDetail(tx) {
  selectedTx.value = tx
  txDetailOpen.value = true
}

const IDENT_KEYS = ['nr_fabryczny', 'typ', 'nr_udt', 'producent', 'marka', 'model', 'nazwa_urzadzenia']

const filteredIdentFields = computed(() => {
  if (!selectedTx.value) return []
  return IDENT_KEYS
    .map(key => ({ key, label: fieldLabel(key), value: getField(selectedTx.value, key) }))
    .filter(item => item.value !== '' && item.value !== null && item.value !== undefined)
})

const nonIdentInputData = computed(() => {
  if (!selectedTx.value?.input_data) return {}
  return Object.fromEntries(
    Object.entries(selectedTx.value.input_data).filter(([k]) => !IDENT_KEYS.includes(k))
  )
})

function getField(tx, key) {
  const d = tx.input_data || {}
  const val = d[key]
  if (val === null || val === undefined) return ''
  if (typeof val === 'object' && val !== null && 'value' in val) return String(val.value)
  return String(val)
}

function getResult(tx) {
  if (tx.is_locked) return null
  const out = tx.output_data || {}
  for (const k of ['resurs', 'T_WSK', 'U_WSK', 'resurs_pozostaly', 'resurs_zuzycie']) {
    if (out[k] !== undefined && out[k] !== null) {
      const v = out[k]
      return typeof v === 'object' ? JSON.stringify(v) : String(v)
    }
  }
  for (const [, v] of Object.entries(out)) {
    if (typeof v === 'number') return String(v)
  }
  return null
}

function isKeyResult(key) {
  return ['resurs', 'T_WSK', 'U_WSK', 'resurs_pozostaly', 'resurs_zuzycie', 'resurs_wykorzystanie'].includes(key)
}

function formatVal(val) {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'object' && 'value' in val) {
    return val.unit ? `${val.value} ${val.unit}` : String(val.value)
  }
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

const FIELD_LABELS = {
  nr_fabryczny: 'Nr fabryczny', typ: 'Typ/model', nr_udt: 'Nr UDT', producent: 'Producent',
  marka: 'Marka', model: 'Model', nazwa_urzadzenia: 'Nazwa urządzenia',
  q_max: 'Udźwig max (t)', masa_wlasna: 'Masa własna (t)', h_max: 'Wys. podnoszenia (m)',
  v_pod: 'Prędkość podnoszenia', v_jaz: 'Prędkość jazdy',
  ilosc_cykli: 'Liczba cykli', licznik_pracy: 'Licznik pracy (h)',
  ponowny_resurs: 'Ponowny resurs', data_resurs: 'Data poprzedniego resursu',
  ostatni_resurs: 'Poprzedni resurs', spec: 'Badanie specjalne',
  resurs: 'Resurs (cykle)', T_WSK: 'T_WSK', U_WSK: 'U_WSK (zdolność cyklowa)',
  resurs_pozostaly: 'Resurs pozostały', resurs_zuzycie: 'Zużycie resursu',
  resurs_wykorzystanie: 'Wykorzystanie resursu (%)',
  wsp_kdr: 'Wsp. widma obciążeń (Kd)', stan_obciazenia: 'Klasa obciążenia',
  F_X: 'Współczynnik F_X', kss: 'Wsp. badania specjalnego',
}

function fieldLabel(key) {
  return FIELD_LABELS[key] || key.replace(/_/g, ' ')
}

const txSummaryText = computed(() => {
  if (!selectedTx.value) return ''
  const tx = selectedTx.value
  const calName = tx.calculator_definition?.name || tx.calculator_name || '—'
  const lines = [
    '=== WYZNACZRESURS.COM — WYNIKI OBLICZEŃ ===',
    `Urządzenie: ${calName}`,
    `Data obliczeń: ${formatDate(tx.created_at)}`,
    '',
    '--- DANE URZĄDZENIA ---',
    ...filteredIdentFields.value.map(f => `${f.label}: ${f.value}`),
    '',
    '--- DANE WEJŚCIOWE ---',
    ...Object.entries(nonIdentInputData.value).map(([k, v]) => `${fieldLabel(k)}: ${formatVal(v)}`),
  ]
  if (!tx.is_locked) {
    lines.push('', '--- WYNIKI OBLICZEŃ ---')
    for (const [k, v] of Object.entries(tx.output_data || {})) {
      lines.push(`${fieldLabel(k)}: ${formatVal(v)}`)
    }
  } else {
    lines.push('', '[Wyniki zablokowane — brak punktów premium]')
  }
  lines.push('', 'wyznaczresurs.com')
  return lines.join('\n')
})

async function copyTxToClipboard() {
  await copyText(txSummaryText.value)
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    $q.notify({ type: 'positive', message: 'Skopiowano do schowka.', position: 'top', timeout: 1500 })
  } catch {
    $q.notify({ type: 'warning', message: 'Nie można skopiować automatycznie — zaznacz ręcznie.', position: 'top' })
  }
}

const copyLoading = ref(false)
const copyToUserLoading = ref(false)

async function copyResultToAdmin() {
  if (!selectedTx.value) return
  copyLoading.value = true
  try {
    await api.post(`/calculators/results/${selectedTx.value.id}/copy_to/`)
    $q.notify({ type: 'positive', message: 'Obliczenie skopiowane na Twoje konto.', position: 'top' })
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd kopiowania obliczenia.', position: 'top' })
  } finally {
    copyLoading.value = false
  }
}

async function copyResultToUser(userId) {
  if (!selectedTx.value) return
  copyToUserLoading.value = true
  try {
    await api.post(`/calculators/results/${selectedTx.value.id}/copy_to/`, { target_user_id: userId })
    const name = selectedUser.value?.display_name || 'użytkownika'
    $q.notify({ type: 'positive', message: `Obliczenie zapisane na konto: ${name}.`, position: 'top' })
    fetchUserTransactions()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd zapisywania obliczenia.', position: 'top' })
  } finally {
    copyToUserLoading.value = false
  }
}

const pickMyResultDialog = ref(false)
const myResults = ref([])
const myResultsLoading = ref(false)
const myResultSearch = ref('')
const selectedMyResult = ref(null)
const pickLoading = ref(false)

const filteredMyResults = computed(() => {
  const q = myResultSearch.value.toLowerCase()
  if (!q) return myResults.value
  return myResults.value.filter(r => {
    const name = (r.calculator_definition?.name || r.calculator_name || '').toLowerCase()
    const nr = getField(r, 'nr_fabryczny').toLowerCase()
    return name.includes(q) || nr.includes(q)
  })
})

async function fetchMyResults() {
  myResultsLoading.value = true
  try {
    const { data } = await api.get('/calculators/results/')
    myResults.value = data
  } finally {
    myResultsLoading.value = false
  }
}

function openPickMyResult() {
  selectedMyResult.value = null
  myResultSearch.value = ''
  pickMyResultDialog.value = true
  fetchMyResults()
}

async function confirmPickMyResult() {
  if (!selectedMyResult.value || !selectedUser.value) return
  pickLoading.value = true
  try {
    await api.post(`/calculators/results/${selectedMyResult.value.id}/copy_to/`, {
      target_user_id: selectedUser.value.id
    })
    const name = selectedUser.value.display_name
    $q.notify({ type: 'positive', message: `Obliczenie przekazane do: ${name}.`, position: 'top' })
    pickMyResultDialog.value = false
    fetchUserTransactions()
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd przekazywania obliczenia.', position: 'top' })
  } finally {
    pickLoading.value = false
  }
}

const createUserDialog = ref(false)
const createLoading = ref(false)
const newUser = ref(emptyNewUser())

function emptyNewUser() {
  return { email: '', first_name: '', last_name: '', is_company: false, company_name: '', nip: '', address_line: '', postal_code: '', city: '', password: '', premium: 0 }
}

function openCreateUserDialog() {
  newUser.value = emptyNewUser()
  createUserDialog.value = true
}

async function submitCreateUser() {
  createLoading.value = true
  try {
    const payload = { ...newUser.value }
    if (!payload.password) delete payload.password
    await api.post('/auth/admin/users/', payload)
    $q.notify({ type: 'positive', message: 'Użytkownik utworzony.', position: 'top' })
    createUserDialog.value = false
    fetchUsers()
  } finally {
    createLoading.value = false
  }
}

const editUserDialog = ref(false)
const editLoading = ref(false)
const editUser = ref(null)

function openEditUserDialog(user) {
  editUser.value = { ...user }
  editUserDialog.value = true
}

async function submitEditUser() {
  editLoading.value = true
  try {
    const { data } = await api.patch(`/auth/admin/users/${editUser.value.id}/`, {
      first_name: editUser.value.first_name,
      last_name: editUser.value.last_name,
      is_company: editUser.value.is_company,
      company_name: editUser.value.company_name,
      nip: editUser.value.nip,
      address_line: editUser.value.address_line,
      postal_code: editUser.value.postal_code,
      city: editUser.value.city,
      premium: editUser.value.premium,
      discount_percent: editUser.value.discount_percent,
      is_active: editUser.value.is_active,
    })
    $q.notify({ type: 'positive', message: 'Zaktualizowano.', position: 'top' })
    editUserDialog.value = false
    const idx = users.value.findIndex(u => u.id === data.id)
    if (idx !== -1) users.value[idx] = data
    if (selectedUser.value?.id === data.id) selectedUser.value = data
  } finally {
    editLoading.value = false
  }
}

async function updateUserAdminSettings() {
  if (!selectedUser.value) return
  try {
    const { data } = await api.patch(`/auth/admin/users/${selectedUser.value.id}/`, {
      show_logo_on_pdf: selectedUser.value.show_logo_on_pdf,
      show_signature_on_pdf: selectedUser.value.show_signature_on_pdf,
      discount_percent: selectedUser.value.discount_percent
    })
    $q.notify({ type: 'positive', message: 'Zaktualizowano ustawienia użytkownika.', position: 'top', timeout: 1000 })
    // Aktualizacja w głównej liście
    const idx = users.value.findIndex(u => u.id === data.id)
    if (idx !== -1) users.value[idx] = data
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas aktualizacji ustawień.', position: 'top' })
  }
}

function confirmDeleteUser(user) {
  $q.dialog({
    title: 'Usuń użytkownika',
    message: `Czy na pewno chcesz usunąć konto <b>${user.email}</b>? Operacja jest nieodwracalna.`,
    html: true,
    cancel: { label: 'Anuluj', flat: true },
    ok: { label: 'Usuń', color: 'negative', unelevated: true },
    persistent: true,
  }).onOk(async () => {
    try {
      await api.delete(`/auth/admin/users/${user.id}/`)
      $q.notify({ type: 'positive', message: 'Użytkownik usunięty.', position: 'top' })
      users.value = users.value.filter(u => u.id !== user.id)
      if (userDetailOpen.value && selectedUser.value?.id === user.id) userDetailOpen.value = false
    } catch {
      // Błąd jest obsługiwany przez interceptor axios
    }
  })
}

const allTransactions = ref([])
const txLoading = ref(false)
const txSearch = ref('')
const txYear = ref(null)
const txMonth = ref(null)

const txColumns = [
  { name: 'calculator_name', label: 'Kalkulator', field: 'calculator_name', align: 'left', sortable: true },
  { name: 'device_info', label: 'Nr fab / Typ', align: 'left', field: row => `${row.nr_fabryczny || '—'} / ${row.typ || '—'}` },
  { name: 'user_display', label: 'Użytkownik', field: 'user_display', align: 'left' },
  { name: 'is_locked', label: 'Status', field: 'is_locked', align: 'center' },
  { name: 'created_at', label: 'Data', field: 'created_at', align: 'left', sortable: true },
  { name: 'tx_pdf', label: 'PDF', field: 'id', align: 'center' },
]

const txAnalysisColumns = [
  { name: 'calculator_name', label: 'Kalkulator', field: 'calculator_name', align: 'left', sortable: true },
  { name: 'count', label: 'Liczba obliczeń', field: 'count', align: 'center', sortable: true },
]

const txAnalysis = computed(() => {
  const map = {}
  allTransactions.value.forEach(t => {
    if (!map[t.calculator_name]) map[t.calculator_name] = { calculator_name: t.calculator_name, count: 0 }
    map[t.calculator_name].count++
  })
  return Object.values(map).sort((a, b) => b.count - a.count)
})

async function fetchAllTransactions() {
  txLoading.value = true
  try {
    const params = {}
    if (txSearch.value) params.search = txSearch.value
    if (txYear.value) params.year = txYear.value
    if (txMonth.value) params.month = txMonth.value
    const { data } = await api.get('/auth/admin/transactions/', { params })
    allTransactions.value = data
  } finally {
    txLoading.value = false
  }
}

const invoiceReport = ref(null)
const invLoading = ref(false)
const invYear = ref(null)
const invMonth = ref(null)
const invStatus = ref(null)

const ksefStatusOptions = [
  { label: 'Wszystkie', value: null },
  { label: 'Oczekująca', value: 'pending' },
  { label: 'Wysłana', value: 'sent' },
  { label: 'Zaakceptowana', value: 'accepted' },
  { label: 'Odrzucona', value: 'rejected' },
  { label: 'Anulowana', value: 'cancelled' },
]

const invColumns = [
  { name: 'invoice_number', label: 'Numer', field: 'invoice_number', align: 'left', sortable: true },
  { name: 'buyer_name', label: 'Nabywca', field: 'buyer_name', align: 'left' },
  { name: 'buyer_nip', label: 'NIP', field: 'buyer_nip', align: 'left' },
  { name: 'issue_date', label: 'Data', field: 'issue_date', align: 'left', sortable: true },
  { name: 'net_amount', label: 'Netto', field: r => formatAmount(r.net_amount) + ' PLN', align: 'right' },
  { name: 'gross_amount', label: 'Brutto', field: 'gross_amount', align: 'right', sortable: true },
  { name: 'points_added', label: 'Pkt', field: 'points_added', align: 'center' },
  { name: 'ksef_status', label: 'Status', field: 'ksef_status', align: 'center' },
  { name: 'actions', label: '', field: 'id', align: 'center' },
]

async function fetchInvoiceReport() {
  invLoading.value = true
  try {
    const params = {}
    if (invYear.value) params.year = invYear.value
    if (invMonth.value) params.month = invMonth.value
    if (invStatus.value) params.ksef_status = invStatus.value
    const { data } = await api.get('/billing/admin/report/', { params })
    invoiceReport.value = data
  } finally {
    invLoading.value = false
  }
}

async function downloadInvoicePdf(inv) {
  try {
    const response = await api.get(`/billing/invoices/${inv.id}/download_pdf/`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `Faktura_${inv.invoice_number.replace(/\//g, '_')}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd pobierania PDF.', position: 'top' })
  }
}

async function refreshInvoiceQr(inv) {
  try {
    invLoading.value = true
    const { data } = await api.post(`/billing/invoices/${inv.id}/refresh_qr/`)
    $q.notify({ type: 'positive', message: data.detail || 'Zaktualizowano QR', position: 'top' })
    fetchInvoiceReport()
    fetchUserInvoices()
  } catch (err) {
    $q.notify({ type: 'negative', message: err.response?.data?.detail || 'Błąd odświeżania QR.', position: 'top' })
  } finally {
    invLoading.value = false
  }
}

function printInvoiceReport() {
  if (!invoiceReport.value) return
  const { summary, invoices, filters } = invoiceReport.value
  const periodLabel = [
    filters.year ? `Rok: ${filters.year}` : '',
    filters.month ? `Miesiąc: ${filters.month}` : '',
  ].filter(Boolean).join(', ') || 'Wszystkie okresy'

  const rows = invoices.map(inv => `
    <tr>
      <td>${inv.invoice_number}</td><td>${inv.buyer_name}</td><td>${inv.buyer_nip || '—'}</td>
      <td>${inv.issue_date}</td><td style="text-align:right">${formatAmount(inv.net_amount)} PLN</td>
      <td style="text-align:right">${formatAmount(inv.vat_amount)} PLN</td>
      <td style="text-align:right"><b>${formatAmount(inv.gross_amount)} PLN</b></td>
      <td style="text-align:center">${inv.points_added}</td><td>${ksefLabel(inv.ksef_status)}</td>
    </tr>`).join('')

  const win = window.open('', '_blank')
  win.document.write(`<html><head><title>Zestawienie faktur</title>
    <style>body{font-family:Arial,sans-serif;font-size:12px}h2{color:#1565C0}
    table{width:100%;border-collapse:collapse;margin-top:12px}
    th{background:#1565C0;color:#fff;padding:6px 8px;text-align:left}
    td{padding:5px 8px;border-bottom:1px solid #eee}
    tr:nth-child(even) td{background:#f5f7ff}
    .sum{margin-top:16px;font-weight:700;background:#e3f2fd;padding:10px;border-radius:4px}</style></head>
    <body><h2>wyznaczresurs.com — Zestawienie faktur</h2><p><b>Okres:</b> ${periodLabel}</p>
    <table><thead><tr><th>Nr faktury</th><th>Nabywca</th><th>NIP</th><th>Data</th>
    <th>Netto</th><th>VAT</th><th>Brutto</th><th>Pkt</th><th>Status</th></tr></thead>
    <tbody>${rows}</tbody></table>
    <div class="sum">Razem: ${summary.count} faktur | Netto: ${formatAmount(summary.total_net)} PLN |
    VAT: ${formatAmount(summary.total_vat)} PLN | Brutto: ${formatAmount(summary.total_gross)} PLN |
    Punkty: ${summary.total_points}</div></body></html>`)
  win.document.close()
  setTimeout(() => win.print(), 400)
}

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 6 }, (_, i) => ({ label: String(currentYear - i), value: String(currentYear - i) }))
const monthOptions = [
  { label: 'Styczeń', value: '1' }, { label: 'Luty', value: '2' }, { label: 'Marzec', value: '3' },
  { label: 'Kwiecień', value: '4' }, { label: 'Maj', value: '5' }, { label: 'Czerwiec', value: '6' },
  { label: 'Lipiec', value: '7' }, { label: 'Sierpień', value: '8' }, { label: 'Wrzesień', value: '9' },
  { label: 'Październik', value: '10' }, { label: 'Listopad', value: '11' }, { label: 'Grudzień', value: '12' },
]

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatAmount(val) {
  return Number(val || 0).toFixed(2)
}

function ksefColor(s) {
  return { accepted: 'positive', pending: 'warning', sent: 'info', rejected: 'negative', cancelled: 'grey-6' }[s] || 'grey'
}

function ksefLabel(s) {
  return { accepted: 'Zaakceptowana', pending: 'Oczekująca', sent: 'Wysłana', rejected: 'Odrzucona', cancelled: 'Anulowana' }[s] || s
}

// ---- Cennik Globalny ----
const allCalculators = ref([])
const pricingLoading = ref(false)
const pricingColumns = [
  { name: 'name', label: 'Kalkulator', field: 'name', align: 'left', sortable: true },
  { name: 'premium_cost', label: 'Cena: Nowy resurs', field: 'premium_cost', align: 'center' },
  { name: 'premium_cost_recurring', label: 'Cena: Ponowny resurs', field: 'premium_cost_recurring', align: 'center' },
]

async function fetchPricing() {
  pricingLoading.value = true
  try {
    const { data } = await api.get('/calculators/definitions/')
    allCalculators.value = data
  } finally {
    pricingLoading.value = false
  }
}

async function saveAllPrices() {
  pricingLoading.value = true
  try {
    const pricesPayload = allCalculators.value.map(c => ({
      id: c.id,
      premium_cost: c.premium_cost,
      premium_cost_recurring: c.premium_cost_recurring
    }))
    await api.post('/calculators/definitions/update_prices/', { prices: pricesPayload })
    $q.notify({ type: 'positive', message: 'Cennik zaktualizowany.', position: 'top' })
  } catch {
    $q.notify({ type: 'negative', message: 'Błąd podczas aktualizacji cennika.', position: 'top' })
  } finally {
    pricingLoading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/billing/public-config/')
    ksefSandbox.value = res.data.ksef_sandbox
  } catch (e) {
    console.error('Błąd pobierania konfiguracji public-config:', e)
  }
  fetchUsers()
  fetchStats()
  fetchAllTransactions()
  fetchInvoiceReport()
})

watch(mainTab, tab => {
  if (tab === 'stats' && !stats.value) fetchStats()
  if (tab === 'pricing' && !allCalculators.value.length) fetchPricing()
})
</script>

<style scoped>
.ident-chip {
  background: rgba(21, 101, 192, 0.06);
  border: 1px solid rgba(21, 101, 192, 0.15);
  border-radius: 6px;
  padding: 6px 10px;
  height: 100%;
}
.data-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 4px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  font-size: 13px;
  gap: 8px;
}
.data-row:last-child { border-bottom: none; }
.data-key {
  flex-shrink: 0;
  max-width: 70%;
  opacity: 0.8;
}
.data-val {
  text-align: right;
  word-break: break-word;
}
.data-row--highlight {
  background: rgba(21, 101, 192, 0.07);
}
.font-mono :deep(textarea) {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
}
</style>
