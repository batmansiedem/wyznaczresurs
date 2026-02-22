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
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col text-center q-pa-lg">
              <div class="text-overline text-grey-6">Punkty premium</div>
              <div class="text-h3 text-weight-bolder text-primary q-my-sm">{{ userStore.user.premium }}</div>
              <q-btn flat dense color="primary" label="Doładuj konto" to="/pricing" no-caps />
            </q-card-section>
          </q-card>
        </div>

        <!-- Ilość wyników -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col text-center q-pa-lg">
              <div class="text-overline text-grey-6">Zapisane wyniki</div>
              <div class="text-h3 text-weight-bolder text-primary q-my-sm">{{ resultsCount }}</div>
              <q-btn flat dense color="primary" label="Zobacz wszystkie" to="/saved-results" no-caps />
            </q-card-section>
          </q-card>
        </div>

        <!-- Typ konta -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered class="column full-height hover-primary">
            <q-card-section class="col text-center q-pa-lg">
              <div class="text-overline text-grey-6">Typ konta</div>
              <div class="text-h4 text-weight-bold q-my-sm">
                {{ userStore.isCompany ? 'Firma' : 'Prywatne' }}
              </div>
              <q-btn flat dense color="grey-7" label="Edytuj profil" to="/account" no-caps />
            </q-card-section>
          </q-card>
        </div>

        <!-- Szybkie akcje -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered class="column full-height">
            <q-list separator>
              <q-item clickable to="/calculators" class="q-py-md">
                <q-item-section avatar><q-icon name="calculate" color="primary" /></q-item-section>
                <q-item-section class="text-weight-bold">Nowe obliczenie</q-item-section>
              </q-item>
              <q-item clickable to="/specialists" class="q-py-md">
                <q-item-section avatar><q-icon name="group" color="primary" /></q-item-section>
                <q-item-section class="text-weight-bold">Baza specjalistów</q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </div>

      <!-- Ostatnie wyniki -->
      <template v-if="recentResults.length">
        <div class="section-label">Ostatnie obliczenia</div>
        <q-card flat bordered class="shadow-1">
          <q-list separator>
            <q-item v-for="r in recentResults" :key="r.id" clickable to="/saved-results" class="q-py-md">
              <q-item-section avatar>
                <DeviceIcon :slug="r.calculator_slug || 'wciagnik'" :size="40" class="text-primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold text-primary">{{ r.calculator_name }}</q-item-label>
                <q-item-label caption>{{ new Date(r.created_at).toLocaleString() }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge v-if="r.is_locked" color="warning" outline>
                  <q-icon name="lock" size="12px" />
                </q-badge>
                <q-badge v-else color="primary" outline :label="`${r.output_data?.resurs_wykorzystanie || 0}%`" />
              </q-item-section>
              <q-item-section side>
                <q-icon name="chevron_right" color="primary" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </template>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from 'stores/user-store'
import { api } from 'boot/axios'
import DeviceIcon from 'components/DeviceIcon.vue'

const userStore = useUserStore()
const recentResults = ref([])
const resultsCount = ref(0)

onMounted(async () => {
  try {
    const response = await api.get('/calculators/results/')
    const all = response.data
    resultsCount.value = all.length
    recentResults.value = all.slice(0, 5)
  } catch {
    // Silent
  }
})
</script>
