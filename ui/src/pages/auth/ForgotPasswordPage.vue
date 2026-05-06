<template>
  <q-page class="auth-page">
    <div class="auth-grid">
      <!-- Lewa sekcja (identyczna jak w login) -->
      <div class="auth-left">
        <div class="auth-left-bg" aria-hidden="true">
          <svg viewBox="0 0 600 800" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="al-m" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M20 0L0 0 0 20" fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.12"/>
              </pattern>
              <pattern id="al-M" width="100" height="100" patternUnits="userSpaceOnUse">
                <rect width="100" height="100" fill="url(#al-m)"/>
                <path d="M100 0L0 0 0 100" fill="none" stroke="white" stroke-width="0.6" stroke-opacity="0.18"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#al-M)"/>
            <g transform="translate(500, 160)" stroke="white" fill="none" stroke-opacity="0.15">
              <circle r="220" stroke-width="0.5"/><circle r="170" stroke-width="0.7"/>
              <circle r="120" stroke-width="0.5"/><circle r="70" stroke-width="0.9"/>
              <line x1="-240" x2="240" y1="0" y2="0" stroke-width="0.5"/>
              <line x1="0" x2="0" y1="-240" y2="240" stroke-width="0.5"/>
              <circle r="4" fill="white" stroke="none" fill-opacity="0.2"/>
            </g>
          </svg>
        </div>
        <div class="auth-left-content">
          <div class="auth-brand">wyznacz<span style="opacity:0.6">resurs</span>.com</div>
          <h2 class="auth-left-h2">Przywracanie dostępu</h2>
          <p class="text-white opacity-70">Wprowadź swój adres email, aby otrzymać link do zresetowania hasła.</p>
        </div>
      </div>

      <!-- Prawa sekcja (formularz) -->
      <div class="auth-right">
        <div class="auth-form-wrap">
          <h1 class="auth-form-title">Zresetuj hasło</h1>
          <p class="auth-form-sub">
            Pamiętasz hasło?
            <q-btn flat no-caps dense label="Zaloguj się" color="primary" to="/login" class="q-pa-none" />
          </p>

          <q-form @submit="onSubmit">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="email" label="Adres email" type="email" outlined
                  :rules="[val => !!val || 'Wymagane']" />
              </div>
              <div class="col-12 q-mt-md">
                <q-btn label="Wyślij link do resetu" type="submit" color="primary"
                  class="full-width auth-submit" :loading="loading" unelevated size="lg" />
              </div>
            </div>
          </q-form>

          <!-- Linki prawne -->
          <div class="auth-legal-links">
            <router-link to="/regulamin" class="auth-legal-link">Regulamin</router-link>
            <span class="auth-legal-sep">·</span>
            <router-link to="/rodo" class="auth-legal-link">Polityka prywatności</router-link>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { api } from 'boot/axios'
import { Notify, useMeta } from 'quasar'

useMeta({
  title: 'Reset hasła | wyznaczresurs.com'
})

const email = ref('')
const loading = ref(false)

const onSubmit = async () => {
  loading.value = true
  try {
    await api.post('/auth/password/reset/', { email: email.value })
    Notify.create({ 
      type: 'positive', 
      message: 'Link do resetu hasła został wysłany. Sprawdź swoją skrzynkę (również folder SPAM).', 
      position: 'top',
      timeout: 10000 
    })
  } catch {
     // Błąd obsłużony przez Axios
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-legal-links {
  margin-top: 48px;
  text-align: center;
  font-size: 12px;
}
.auth-legal-link {
  color: #666;
  text-decoration: none;
}
.auth-legal-link:hover {
  color: #1565C0;
  text-decoration: underline;
}
.auth-legal-sep {
  margin: 0 6px;
  color: #ccc;
}
</style>
