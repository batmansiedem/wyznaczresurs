<template>
  <q-page padding>
    <!-- Nagłówek z przełącznikiem -->
    <div class="row items-center justify-between q-mb-lg">
      <div class="col-12 col-sm-auto">
        <div class="calc-page-header">
          <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Kalkulatory resursu</h1>
          <p class="text-subtitle1 text-grey-7 q-mb-none">Wybierz urządzenie, aby rozpocząć obliczenia</p>
        </div>
      </div>
      
      <div class="col-12 col-sm-auto q-mt-md q-sm-mt-none">
        <q-btn-toggle
          v-model="viewType"
          toggle-color="primary"
          flat dense unelevated
          class="border-primary"
          :options="[
            { icon: 'grid_view', value: 'grid' },
            { icon: 'list', value: 'list' }
          ]"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center q-pa-xl">
      <q-spinner-cube color="primary" size="4em" />
    </div>

    <template v-else>
      <div class="section-label">Urządzenia Transportu Bliskiego</div>
      
      <!-- WIDOK SIATKI -->
      <div v-if="viewType === 'grid'" class="row q-col-gutter-lg q-mb-xl">
        <div v-for="calc in deviceCalcs" :key="calc.slug" class="col-12 col-sm-6 col-lg-4">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col q-pa-md">
              <div class="row no-wrap items-start">
                <div class="col q-pr-md">
                  <div class="text-h6 text-weight-bold">{{ calc.name }}</div>
                  <div class="text-caption text-grey-7 description-text">
                    {{ getDeviceDescription(calc.slug) }}
                  </div>
                </div>
                <div class="col-auto">
                  <div class="icon-bg">
                    <DeviceIcon :slug="calc.slug" :size="64" class="text-primary" />
                  </div>
                </div>
              </div>

              <!-- Mechanizmy w widoku siatki -->
              <div v-if="getDeviceMechanisms(calc.slug).length" class="q-mt-md">
                <div class="text-overline text-grey-6 q-mb-xs">Mechanizmy:</div>
                <div class="row q-gutter-xs">
                  <q-btn
                    v-for="mech in getDeviceMechanisms(calc.slug)"
                    :key="mech.slug"
                    :label="mech.name"
                    :to="`/calculators/${mech.slug}`"
                    outline no-caps dense size="sm"
                    color="primary"
                    class="q-px-sm"
                  />
                </div>
              </div>
            </q-card-section>

            <q-separator inset opacity="0.1" />

            <q-card-actions class="q-pa-md">
              <q-btn unelevated color="primary" no-caps label="Otwórz kalkulator"
                :to="`/calculators/${calc.slug}`" icon="calculate" class="full-width" />
            </q-card-actions>
          </q-card>
        </div>
      </div>

      <!-- WIDOK LISTY -->
      <q-list v-else bordered separator class="rounded-borders q-mb-xl">
        <q-item v-for="calc in deviceCalcs" :key="calc.slug" class="q-py-md">
          <q-item-section avatar>
            <DeviceIcon :slug="calc.slug" :size="48" class="text-primary" />
          </q-item-section>

          <q-item-section>
            <q-item-label class="text-weight-bold text-subtitle1">{{ calc.name }}</q-item-label>
            <q-item-label caption lines="1">{{ getDeviceDescription(calc.slug) }}</q-item-label>
            
            <!-- Mechanizmy w widoku listy -->
            <div v-if="getDeviceMechanisms(calc.slug).length" class="row q-gutter-xs q-mt-sm">
              <q-btn
                v-for="mech in getDeviceMechanisms(calc.slug)"
                :key="mech.slug"
                :label="mech.name"
                :to="`/calculators/${mech.slug}`"
                outline no-caps dense size="xs"
                color="primary"
                class="q-px-sm"
              />
            </div>
          </q-item-section>

          <q-item-section side>
            <q-btn flat round color="primary" icon="chevron_right" :to="`/calculators/${calc.slug}`" />
          </q-item-section>
        </q-item>
      </q-list>
    </template>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from 'boot/axios'
import DeviceIcon from 'components/DeviceIcon.vue'

const calculators = ref([])
const loading = ref(true)
const viewType = ref('grid')

const DEVICE_DESCRIPTIONS = {
  suwnica: 'Urządzenie dźwignicowe poruszające się po torowisku.',
  zuraw: 'Dźwignica z wysięgnikiem do podnoszenia ładunków.',
  wciagarka: 'Urządzenie do pionowego podnoszenia za pomocą liny.',
  wciagnik: 'Kompaktowe urządzenie podnoszące na belce.',
  wozek_jezdniowy: 'Pojazd do podnoszenia i przewozu ładunków na widłach.',
  podest_ruchomy: 'Urządzenie do prac na wysokościach.',
  ukladnica_magazynowa: 'Dźwignica do obsługi regałów wysokiego składowania.',
  zuraw_przeladunkowy: 'Żuraw na pojeździe (HDS) do załadunku towarów.',
  dzwig: 'Winda osobowa lub towarowa w pionowym szybie.',
  dzwignik: 'Urządzenie o ograniczonej wysokości podnoszenia.',
  hakowiec: 'Pojazd do transportu kontenerów mechanizmem hakowym.',
  podnosnik_samochodowy: 'Dźwignik warsztatowy do podnoszenia pojazdów.',
  autotransporter: 'Zabudowa do transportu pojazdów na dwóch poziomach.',
  podest_zaladowczy: 'Platforma z tyłu pojazdu do załadunku towarów.',
  wozek_specjalizowany: 'Wózek o unikalnej konstrukcji do zadań specjalnych.',
  winda_dekarska: 'Winda pochyła do transportu materiałów na dachy.',
}

function getDeviceDescription(slug) {
  return DEVICE_DESCRIPTIONS[slug] || 'Obliczanie stopnia wykorzystania resursu.'
}

const DEVICE_MECHANISMS = {
  suwnica:   ['mech_podnoszenia', 'mech_jazdy_suwnicy'],
  wciagarka: ['mech_podnoszenia', 'mech_jazdy_wciagarki'],
  wciagnik:  ['mech_podnoszenia'],
  zuraw:     ['mech_podnoszenia', 'mech_jazdy_zurawia', 'mech_zmiany_wysiegu', 'mech_zmiany_obrotu'],
}

const ALL_MECH_SLUGS = new Set(Object.values(DEVICE_MECHANISMS).flat())
const deviceCalcs = computed(() => calculators.value.filter(c => !ALL_MECH_SLUGS.has(c.slug)))
const calcBySlug = computed(() => Object.fromEntries(calculators.value.map(c => [c.slug, c])))

function getDeviceMechanisms(deviceSlug) {
  return (DEVICE_MECHANISMS[deviceSlug] || []).map(s => calcBySlug.value[s]).filter(Boolean)
}

async function fetchCalculators() {
  loading.value = true
  try {
    const response = await api.get('/calculators/definitions/')
    calculators.value = response.data
  } finally {
    loading.value = false
  }
}

onMounted(fetchCalculators)
</script>

<style scoped lang="scss">
.border-primary {
  border: 1px solid var(--q-primary);
}
</style>
