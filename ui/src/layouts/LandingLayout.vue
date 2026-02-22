<template>
  <q-layout view="lHh Lpr lFf">
    <q-header bordered :class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-white text-primary'">
      <q-toolbar class="container q-mx-auto q-py-sm">
        <q-btn flat no-caps no-wrap size="lg" to="/" class="q-px-none">
          <q-toolbar-title class="text-weight-bolder text-h5">
            wyznacz<span class="text-secondary">resurs</span>.com
          </q-toolbar-title>
        </q-btn>

        <q-space />

        <div class="gt-sm q-gutter-md">
          <q-btn flat no-caps label="Cennik" to="/pricing" class="text-weight-bold" />
          <q-btn flat no-caps label="Pomoc" to="/help" class="text-weight-bold" />
          <q-btn flat no-caps label="Kontakt" to="/contact" class="text-weight-bold" />
        </div>

        <q-separator vertical inset class="q-mx-lg gt-sm" />

        <div class="q-gutter-sm row no-wrap items-center">
          <q-btn
            flat
            round
            dense
            :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'"
            @click="toggleDarkMode"
            class="q-mr-sm"
            :title="$q.dark.isActive ? 'Przełącz na tryb jasny' : 'Przełącz na tryb ciemny'"
          />

          <template v-if="userStore.isLoggedIn">
            <q-btn unelevated no-caps label="Mój Pulpit" to="/dashboard" color="primary" class="rounded-borders q-px-md" />
          </template>
          <template v-else>
            <q-btn flat no-caps label="Zaloguj" to="/login" color="primary" class="text-weight-bold" />
            <q-btn unelevated no-caps label="Zarejestruj się" to="/register" color="primary" class="rounded-borders q-px-md shadow-2" />
          </template>
          
          <q-btn flat round dense icon="menu" class="lt-md" color="primary">
            <q-menu auto-close>
              <q-list style="min-width: 200px">
                <q-item clickable to="/pricing"><q-item-section>Cennik</q-item-section></q-item>
                <q-item clickable to="/help"><q-item-section>Pomoc / FAQ</q-item-section></q-item>
                <q-item clickable to="/contact"><q-item-section>Kontakt</q-item-section></q-item>
                <q-separator />
                <q-item v-if="!userStore.isLoggedIn" clickable to="/login"><q-item-section>Zaloguj się</q-item-section></q-item>
                <q-item v-else clickable to="/dashboard"><q-item-section>Przejdź do pulpitu</q-item-section></q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

    <footer class="bg-grey-10 text-white q-pa-xl">
      <div class="row q-col-gutter-xl justify-center container q-mx-auto">
        <div class="col-12 col-md-4">
          <div class="text-h5 text-weight-bolder q-mb-md">
            wyznacz<span class="text-secondary">resurs</span>.com
          </div>
          <p class="text-grey-5 text-subtitle2" style="line-height: 1.6">
            Profesjonalne narzędzia do wyznaczania resursu urządzeń transportu bliskiego. 
            Zgodnie z Rozporządzeniem Ministra Przedsiębiorczości i Technologii oraz dobrą praktyką inżynierską.
          </p>
          <div class="row q-gutter-sm q-mt-md">
            <q-btn flat round dense icon="facebook" color="grey-5" size="md" href="https://www.facebook.com/Wyznacz-resurs-107911734048291/" target="_blank" />
            <q-btn flat round dense icon="smart_display" color="grey-5" size="md" href="https://www.youtube.com/channel/UC-fqGlD3TSgE" target="_blank" />
          </div>
        </div>
        <div class="col-6 col-md-2">
          <div class="text-subtitle1 text-weight-bold q-mb-md">Usługi</div>
          <q-list dense dark>
            <q-item clickable to="/calculators"><q-item-section class="text-grey-5">Kalkulatory</q-item-section></q-item>
            <q-item clickable to="/pricing"><q-item-section class="text-grey-5">Cennik</q-item-section></q-item>
            <q-item clickable to="/specialists"><q-item-section class="text-grey-5">Specjaliści</q-item-section></q-item>
          </q-list>
        </div>
        <div class="col-6 col-md-2">
          <div class="text-subtitle1 text-weight-bold q-mb-md">Pomoc</div>
          <q-list dense dark>
            <q-item clickable to="/help"><q-item-section class="text-grey-5">Instrukcje</q-item-section></q-item>
            <q-item clickable to="/contact"><q-item-section class="text-grey-5">Kontakt</q-item-section></q-item>
            <q-item clickable><q-item-section class="text-grey-5">Regulamin</q-item-section></q-item>
          </q-list>
        </div>
        <div class="col-12 col-md-4">
          <div class="text-subtitle1 text-weight-bold q-mb-md">Kontakt</div>
          <div class="text-grey-5 q-gutter-y-sm">
            <div class="row items-center"><q-icon name="phone" class="q-mr-sm" color="grey-5" /> +48 666 625 752</div>
            <div class="row items-center"><q-icon name="email" class="q-mr-sm" color="grey-5" /> info@wyznaczresurs.com</div>
            <div class="row items-center"><q-icon name="schedule" class="q-mr-sm" color="grey-5" /> Pon - Pt: 8:00 - 17:00</div>
          </div>
        </div>
      </div>
      <q-separator dark class="q-my-xl" style="opacity: 0.2" />
      <div class="text-center text-grey-7 text-caption">
        wyznaczresurs.com &copy; {{ new Date().getFullYear() }} &bull; Profesjonalne Kalkulatory Resursu UTB
      </div>
    </footer>
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { useUserStore } from 'stores/user-store'

const $q = useQuasar()
const userStore = useUserStore()

const toggleDarkMode = () => {
  $q.dark.toggle()
  // Można tu dodać zapisywanie do ciasteczek/localStorage jeśli Quasar sam tego nie robi (zależy od configu)
}
</script>

<style scoped lang="scss">
.container {
  max-width: 1200px;
}
</style>
