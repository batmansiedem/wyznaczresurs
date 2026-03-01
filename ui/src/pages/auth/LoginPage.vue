<template>
  <q-page class="auth-page">
    <div class="auth-grid">

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
            <g transform="translate(60, 680)" stroke="white" fill="none" stroke-opacity="0.15">
              <path d="M0 -200 L0 0 L200 0" stroke-width="1.2"/>
              <line x1="-7" y1="-50" x2="7" y2="-50" stroke-width="1"/>
              <line x1="-7" y1="-100" x2="7" y2="-100" stroke-width="1"/>
              <line x1="-7" y1="-150" x2="7" y2="-150" stroke-width="1"/>
            </g>
          </svg>
        </div>
        <div class="auth-left-content">
          <div class="auth-brand">wyznacz<span style="opacity:0.6">resurs</span>.com</div>
          <h2 class="auth-left-h2">Kalkulator resursu<br>UTB dla inżynierów</h2>
          <ul class="auth-features">
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />22 typy urządzeń transportu bliskiego</li>
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />Metodologia FEM 9.511 / ISO 4301</li>
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />Orzeczenie PDF akceptowane przez UDT</li>
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />Archiwizacja i aktualizacja wyników</li>
          </ul>
          <div class="auth-norm-row">
            <span class="auth-norm">FEM 9.511</span>
            <span class="auth-norm">ISO 4301</span>
            <span class="auth-norm">Rozp. MPiT 2018</span>
          </div>
        </div>
      </div>

      <div class="auth-right">
        <div class="auth-form-wrap">
          <h1 class="auth-form-title">Zaloguj się</h1>
          <p class="auth-form-sub">
            Nie masz konta?
            <q-btn flat no-caps dense label="Zarejestruj się" color="primary" to="/register" class="q-pa-none" />
          </p>
          <q-form @submit="onSubmit" class="q-gutter-md">
            <q-input v-model="email" label="Adres email" type="email" outlined
              :rules="[val => !!val || 'Wymagane']" />
            <q-input v-model="password" label="Hasło" type="password" outlined
              :rules="[val => !!val || 'Wymagane']" />
            <div class="row justify-end">
              <q-btn flat no-caps label="Zapomniałem hasła" size="sm" color="primary" to="/forgot-password" />
            </div>
            <q-btn label="Zaloguj się" type="submit" color="primary"
              class="full-width auth-submit" :loading="loading" unelevated size="lg" />
          </q-form>

          <!-- Linki prawne -->
          <div class="auth-legal-links">
            <router-link to="/regulamin" class="auth-legal-link">Regulamin</router-link>
            <span class="auth-legal-sep">·</span>
            <router-link to="/rodo" class="auth-legal-link">Polityka prywatności</router-link>
            <span class="auth-legal-sep">·</span>
            <router-link to="/cookies" class="auth-legal-link">Cookies</router-link>
          </div>
        </div>
      </div>

    </div>
  </q-page>

  <!-- MODAL AKCEPTACJI REGULAMINU (pojawia się raz — przy pierwszym logowaniu) -->
  <q-dialog v-model="termsModal" persistent>
    <q-card style="max-width:620px;width:100%">
      <q-card-section class="row items-center">
        <q-icon name="gavel" size="1.5rem" color="primary" class="q-mr-sm" />
        <div class="text-h6">Regulamin i polityka prywatności</div>
      </q-card-section>
      <q-separator />
      <q-card-section class="terms-modal-scroll">
        <p class="q-mb-md text-grey-8">
          Aby korzystać z serwisu <strong>wyznaczresurs.com</strong>, zapoznaj się z poniższymi dokumentami
          i zaakceptuj ich warunki.
        </p>

        <q-list bordered separator class="rounded-borders q-mb-md">
          <q-item clickable @click="openDoc('/regulamin')" v-ripple>
            <q-item-section avatar><q-icon name="gavel" color="primary" /></q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">Regulamin serwisu</q-item-label>
              <q-item-label caption>Zasady korzystania, odpowiedzialność, płatności</q-item-label>
            </q-item-section>
            <q-item-section side><q-icon name="open_in_new" color="grey-5" size="sm" /></q-item-section>
          </q-item>
          <q-item clickable @click="openDoc('/rodo')" v-ripple>
            <q-item-section avatar><q-icon name="privacy_tip" color="primary" /></q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">Polityka Prywatności (RODO)</q-item-label>
              <q-item-label caption>Jak przetwarzamy Twoje dane osobowe</q-item-label>
            </q-item-section>
            <q-item-section side><q-icon name="open_in_new" color="grey-5" size="sm" /></q-item-section>
          </q-item>
          <q-item clickable @click="openDoc('/cookies')" v-ripple>
            <q-item-section avatar><q-icon name="cookie" color="primary" /></q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">Polityka cookies</q-item-label>
              <q-item-label caption>Jakich plików cookies używamy</q-item-label>
            </q-item-section>
            <q-item-section side><q-icon name="open_in_new" color="grey-5" size="sm" /></q-item-section>
          </q-item>
        </q-list>

        <q-checkbox v-model="termsAccepted" class="q-mb-sm"
          label="Zapoznałem/am się z Regulaminem serwisu i akceptuję jego warunki." />
        <q-checkbox v-model="rodoAccepted"
          label="Zapoznałem/am się z Polityką Prywatności i wyrażam zgodę na przetwarzanie moich danych osobowych w celu świadczenia usług serwisu." />
      </q-card-section>
      <q-separator />
      <q-card-actions align="right" class="q-pa-md">
        <q-btn flat label="Odmawiam" color="grey-7" @click="rejectTerms" />
        <q-btn label="Akceptuję i wchodzę do serwisu" color="primary" unelevated
          :disable="!termsAccepted || !rodoAccepted"
          @click="acceptTerms" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from 'stores/user-store'
import { useRouter, useRoute } from 'vue-router'

const TERMS_KEY = 'terms_accepted_v1'

const email = ref('')
const password = ref('')
const loading = ref(false)
const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

// Modal zgody
const termsModal = ref(false)
const termsAccepted = ref(false)
const rodoAccepted = ref(false)
let pendingRedirect = '/dashboard'

const onSubmit = async () => {
  loading.value = true
  try {
    await userStore.login({ email: email.value, password: password.value })
    const next = route.query.next || '/dashboard'
    // Sprawdź czy użytkownik już zaakceptował regulamin
    if (!localStorage.getItem(TERMS_KEY)) {
      pendingRedirect = next
      termsModal.value = true
    } else {
      router.push(next)
    }
  } catch {
    // Błąd obsłużony przez Axios Interceptor
  } finally {
    loading.value = false
  }
}

function acceptTerms() {
  localStorage.setItem(TERMS_KEY, '1')
  termsModal.value = false
  router.push(pendingRedirect)
}

async function rejectTerms() {
  termsModal.value = false
  await userStore.logout()
}

function openDoc(path) {
  window.open(path, '_blank')
}

onMounted(() => {
  // Jeśli już zalogowany, nie pokazuj strony logowania
})
</script>

<style scoped>
.auth-legal-links {
  margin-top: 24px;
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
.terms-modal-scroll {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
