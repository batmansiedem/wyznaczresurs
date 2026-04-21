<template>
  <q-page padding class="container">
    <div v-if="userStore.user">
      <div class="calc-page-header">
        <h1 class="text-h4 text-weight-bolder text-primary q-my-none">
          Witaj, {{ userStore.isCompany ? userStore.user.company_name : userStore.user.first_name || 'Użytkowniku' }}!
        </h1>
        <p class="text-subtitle1 text-grey-7 q-mb-none">Przegląd Twojego konta i szybkie skróty</p>
      </div>

      <div class="row q-col-gutter-lg q-mb-xl q-mt-md">
        <!-- Punkty premium -->
        <div class="col-12 col-sm-4 col-md-2">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col text-center q-pa-md">
              <div class="text-overline text-grey-6 line-height-1">Punkty premium</div>
              <div class="text-h4 text-weight-bolder text-primary q-my-sm">{{ userStore.user.premium }}</div>
              <q-btn flat dense color="primary" label="Doładuj" to="/pricing" no-caps />
            </q-card-section>
          </q-card>
        </div>

        <!-- Ilość wyników -->
        <div class="col-12 col-sm-4 col-md-2">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col text-center q-pa-md">
              <div class="text-overline text-grey-6 line-height-1">Zapisane wyniki</div>
              <div class="text-h4 text-weight-bolder text-primary q-my-sm">{{ resultsCount }}</div>
              <q-btn flat dense color="primary" label="Zobacz" to="/saved-results" no-caps />
            </q-card-section>
          </q-card>
        </div>

        <!-- Typ konta -->
        <div class="col-12 col-sm-4 col-md-2">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col text-center q-pa-md">
              <div class="text-overline text-grey-6 line-height-1">Typ konta</div>
              <div class="text-h5 text-weight-bold q-my-sm">
                {{ userStore.isCompany ? 'Firma' : 'Osoba prywatna' }}
              </div>
              <q-btn flat dense color="grey-7" label="Edytuj" to="/account" no-caps />
            </q-card-section>
          </q-card>
        </div>

        <!-- Szybkie akcje -->
        <div class="col-12 col-md-6">
          <q-card flat bordered class="column full-height bg-primary text-white shadow-3 hover-primary cursor-pointer" @click="$router.push('/calculators')">
            <q-card-section class="col row items-center q-pa-lg">
              <q-icon name="calculate" size="3rem" class="q-mr-lg" />
              <div class="col">
                <div class="text-h5 text-weight-bolder">Nowe obliczenie</div>
                <div class="text-subtitle2 opacity-80">Rozpocznij wyznaczanie resursu dla nowego urządzenia</div>
              </div>
              <q-icon name="chevron_right" size="2rem" />
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Ostatnie wyniki -->
      <template v-if="allResults.length">
        <div class="row items-center q-mb-md">
          <div class="col section-label q-mb-none">Ostatnie obliczenia</div>
          <div class="col-12 col-sm-4">
            <q-input
              v-model="filter"
              placeholder="Szukaj (nazwa, nr fabr., nr UDT)..."
              outlined
              dense
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
        </div>

        <q-card flat bordered class="shadow-1">
          <q-list separator>
            <q-item
              v-for="r in filteredResults"
              :key="r.id"
              clickable
              :to="`/calculators/${r.calculator_slug}?result_id=${r.id}`"
              class="q-py-md"
            >
              <!-- Info o urządzeniu (LEWA) -->
              <q-item-section avatar>
                <DeviceIcon :slug="r.calculator_slug || 'wciagnik'" :size="40" class="text-primary" />
              </q-item-section>
              <q-item-section style="max-width: 250px">
                <q-item-label class="text-weight-bold text-primary">{{ r.calculator_name }}</q-item-label>
                <q-item-label caption class="row q-gutter-x-sm">
                  <span v-if="r.input_data?.nr_fabryczny">Nr: <strong>{{ r.input_data.nr_fabryczny }}</strong></span>
                </q-item-label>
                <q-item-label caption>{{ new Date(r.created_at).toLocaleDateString('pl-PL') }}</q-item-label>
              </q-item-section>

              <!-- TRZY WSKAŹNIKI (ŚRODEK) -->
              <q-item-section v-if="!r.is_locked" class="gt-sm col">
                <div class="row items-center justify-center q-gutter-x-massive full-width">
                  <!-- 1. Zużycie % (Kołowy) -->
                  <div class="text-center column items-center" style="width: 100px">
                    <q-circular-progress
                      show-value
                      font-size="12px"
                      :value="parseFloat(r.output_data?.resurs_wykorzystanie || 0)"
                      size="50px"
                      :thickness="0.22"
                      :color="getUtilColor(r.output_data?.resurs_wykorzystanie)"
                      track-color="grey-2"
                      class="text-weight-bold"
                    >
                      {{ Math.round(r.output_data?.resurs_wykorzystanie || 0) }}%
                    </q-circular-progress>
                    <div class="text-micro q-mt-xs text-grey-7">Zużycie</div>
                  </div>

                  <!-- 2. Praca (Obecne / Max) -->
                  <div class="text-center column items-center" style="min-width: 180px">
                    <div class="text-weight-bolder text-primary text-body2">
                      {{ getWorkData(r).label }}
                    </div>
                    <q-linear-progress 
                      :value="getWorkData(r).percent" 
                      color="primary" 
                      style="height: 6px; border-radius: 4px; width: 140px; margin: 6px 0" 
                    />
                    <div class="text-micro text-grey-7">Wykorzystane {{ getWorkData(r).unit }}</div>
                  </div>

                  <!-- 3. Prognoza zużycia (Data) -->
                  <div class="text-center column items-center" style="min-width: 120px">
                    <div class="row items-center q-gutter-x-xs text-primary">
                      <q-icon name="event" size="18px" />
                      <div class="text-weight-bolder text-body2">{{ getForecast(r) }}</div>
                    </div>
                    <div class="text-micro q-mt-xs text-grey-7">Prognoza 100%</div>
                  </div>
                </div>
              </q-item-section>

              <!-- Akcja (PRAWA) -->
              <q-item-section side>
                <q-badge v-if="r.is_locked" color="warning" outline>
                  <q-icon name="lock" size="12px" class="q-mr-xs" /> Zablokowany
                </q-badge>
                <div v-else class="row items-center q-gutter-x-sm">
                  <q-btn flat round dense icon="chevron_right" color="primary" />
                </div>
              </q-item-section>
            </q-item>
            <q-item v-if="filteredResults.length === 0" class="q-pa-lg text-center text-grey-6">
              <q-item-section>Nie znaleziono obliczeń spełniających kryteria.</q-item-section>
            </q-item>
          </q-list>
          <q-card-actions v-if="!filter && allResults.length > 5" align="center">
            <q-btn flat color="primary" label="Zobacz wszystkie zapisane wyniki" to="/saved-results" no-caps />
          </q-card-actions>
        </q-card>
      </template>

    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from 'stores/user-store'
import { api } from 'boot/axios'
import DeviceIcon from 'components/DeviceIcon.vue'

const userStore = useUserStore()
const allResults = ref([])
const filter = ref('')
const resultsCount = ref(0)

// Funkcje pomocnicze dla mini-wykresów w wierszach
function getUtilColor(val) {
  const v = parseFloat(val || 0)
  if (v >= 90) return 'negative'
  if (v >= 70) return 'warning'
  return 'primary'
}

function getWorkData(r) {
  const out = r.output_data || {}
  const inp = r.input_data || {}

  function pv(v) {
    if (v == null) return 0
    if (typeof v === 'object') return parseFloat(v?.value || 0)
    return parseFloat(v || 0)
  }

  // 1. BUMAR (podest_ruchomy) — typ = 'składany na pojeździe BUMAR'
  //    Wykrywaj po typie, nie wartości moto (może być 0 przy ponowny_resurs)
  const typVal = typeof inp.typ === 'object' ? inp.typ?.value : inp.typ
  if (typVal === 'składany na pojeździe BUMAR') {
    const current = pv(inp.moto_podest_ruchomy)
    const total = pv(out.T_WSK)
    return {
      current, total,
      percent: total
        ? Math.min(current / total, 1)
        : parseFloat(out.resurs_wykorzystanie || 0) / 100,
      unit: 'mth',
      label: total ? `${current.toLocaleString('pl-PL')} / ${total.toLocaleString('pl-PL')}` : `${current.toLocaleString('pl-PL')} mth`
    }
  }

  // 2. Kalkulatory mechanizmów — czas_uzytkowania_mech + T_WSK w output
  if (out.czas_uzytkowania_mech != null && out.T_WSK != null) {
    const current = parseFloat(out.czas_uzytkowania_mech || 0)
    const total = pv(out.T_WSK)
    return {
      current, total,
      percent: total ? Math.min(current / total, 1) : 0,
      unit: 'mth',
      label: `${Math.round(current).toLocaleString('pl-PL')} / ${total.toLocaleString('pl-PL')}`
    }
  }

  // 3. Dźwig (winda) — unikalny kalkulator oparty o wiek, nie cykle
  if (out.wiek_dzwigu != null) {
    const current = parseFloat(out.licznik_godzin || 0)
    return {
      current, total: 0,
      percent: parseFloat(out.resurs_wykorzystanie || 0) / 100,
      unit: 'mth',
      label: `${Math.round(current).toLocaleString('pl-PL')} mth`
    }
  }

  // 4. Cycle-based (domyślna) — ilosc_cykli vs U_WSK
  //    Dzwig/wozek z licznikiem: tylko gdy pyt_motogodzin === 'Tak'
  const usesHours = inp.pyt_motogodzin === 'Tak'
  const rawVal = usesHours ? (inp.licznik_pracy ?? 0) : (inp.ilosc_cykli ?? inp.licznik_pracy ?? 0)
  const current = pv(rawVal)
  const total = parseFloat(out.U_WSK || out.U_res || 0)
  const unit = usesHours ? 'mth' : 'cykli'
  return {
    current, total,
    percent: total
      ? Math.min(current / total, 1)
      : parseFloat(out.resurs_wykorzystanie || 0) / 100,
    unit,
    label: total
      ? `${current.toLocaleString('pl-PL')} / ${total.toLocaleString('pl-PL')}`
      : `${current.toLocaleString('pl-PL')} ${unit}`
  }
}

function getForecast(r) {
  const date = r.output_data?.data_prognoza
  if (!date) return 'brak danych'
  return new Date(date).toLocaleDateString('pl-PL')
}

const filteredResults = computed(() => {
  if (!filter.value) {
    return allResults.value.slice(0, 5)
  }
  const needle = filter.value.toLowerCase()
  return allResults.value.filter(r => {
    const name = (r.calculator_name || '').toLowerCase()
    const sn = (r.input_data?.nr_fabryczny || '').toLowerCase()
    const udt = (r.input_data?.nr_udt || '').toLowerCase()
    return name.includes(needle) || sn.includes(needle) || udt.includes(needle)
  })
})

onMounted(async () => {
  try {
    const response = await api.get('/calculators/results/')
    allResults.value = response.data
    resultsCount.value = allResults.value.length
  } catch (e) {
    if (e.response?.status !== 401) console.error('[Dashboard] Błąd pobierania wyników:', e)
  }
})
</script>

<style scoped>
.line-height-1 {
  line-height: 1.1;
}
.text-micro {
  font-size: 9px;
  text-transform: uppercase;
  font-weight: bold;
  letter-spacing: 0.5px;
}
.hover-primary {
  transition: all 0.3s ease;
}
.hover-primary:hover {
  border-color: var(--q-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
</style>
