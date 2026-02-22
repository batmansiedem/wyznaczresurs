<template>
  <q-page class="auth-page">
    <div class="auth-grid">

      <div class="auth-left">
        <div class="auth-left-bg" aria-hidden="true">
          <svg viewBox="0 0 600 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="ar-m" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M20 0L0 0 0 20" fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.12"/>
              </pattern>
              <pattern id="ar-M" width="100" height="100" patternUnits="userSpaceOnUse">
                <rect width="100" height="100" fill="url(#ar-m)"/>
                <path d="M100 0L0 0 0 100" fill="none" stroke="white" stroke-width="0.6" stroke-opacity="0.18"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#ar-M)"/>
            <g transform="translate(520, 200)" stroke="white" fill="none" stroke-opacity="0.15">
              <circle r="260" stroke-width="0.5"/><circle r="200" stroke-width="0.7"/>
              <circle r="140" stroke-width="0.5"/><circle r="80" stroke-width="0.9"/>
              <line x1="-280" x2="280" y1="0" y2="0" stroke-width="0.5"/>
              <line x1="0" x2="0" y1="-280" y2="280" stroke-width="0.5"/>
              <line x1="-183" y1="-183" x2="183" y2="183" stroke-width="0.3" stroke-dasharray="5 9"/>
              <circle r="4" fill="white" stroke="none" fill-opacity="0.2"/>
            </g>
            <g transform="translate(60, 800)" stroke="white" fill="none" stroke-opacity="0.15">
              <path d="M0 -260 L0 0 L240 0" stroke-width="1.2"/>
              <line x1="-7" y1="-65"  x2="7" y2="-65"  stroke-width="1"/>
              <line x1="-7" y1="-130" x2="7" y2="-130" stroke-width="1"/>
              <line x1="-7" y1="-195" x2="7" y2="-195" stroke-width="1"/>
            </g>
          </svg>
        </div>
        <div class="auth-left-content">
          <div class="auth-brand">wyznacz<span style="opacity:0.6">resurs</span>.com</div>
          <h2 class="auth-left-h2">Profesjonalne<br>obliczenia resursu UTB</h2>
          <ul class="auth-features">
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />Rejestracja bezpłatna — bez karty</li>
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />22 typy urządzeń transportu bliskiego</li>
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />Metodologia FEM 9.511 / ISO 4301</li>
            <li><q-icon name="check_circle" size="18px" color="white" style="opacity:0.7" />Orzeczenie PDF akceptowane przez UDT</li>
          </ul>
          <div class="auth-norm-row">
            <span class="auth-norm">FEM 9.511</span>
            <span class="auth-norm">ISO 4301</span>
            <span class="auth-norm">UDT 2018</span>
          </div>
        </div>
      </div>

      <div class="auth-right">
        <div class="auth-form-wrap">
          <h1 class="auth-form-title">Utwórz konto</h1>
          <p class="auth-form-sub">
            Masz już konto?
            <q-btn flat no-caps dense label="Zaloguj się" color="primary" to="/login" class="q-pa-none" />
          </p>
          <q-form @submit="onSubmit" class="q-gutter-md">
            <div class="account-type-toggle">
              <q-toggle v-model="form.is_company" label="Konto firmowe" color="primary" />
            </div>

            <q-input v-model="form.email" label="Adres email" outlined
              :rules="[val => !!val || 'Wymagane']" />

            <template v-if="form.is_company">
              <q-input v-model="form.company_name" label="Nazwa firmy" outlined
                :rules="[val => !!val || 'Wymagane']" />
              <q-input v-model="form.nip" label="NIP" outlined mask="##########"
                :rules="[val => !!val || 'Wymagane', val => val.length === 10 || '10 cyfr']" />
            </template>
            <template v-else>
              <div class="row q-col-gutter-sm">
                <div class="col-6"><q-input v-model="form.first_name" label="Imię" outlined /></div>
                <div class="col-6"><q-input v-model="form.last_name" label="Nazwisko" outlined /></div>
              </div>
            </template>

            <q-input v-model="form.password" label="Hasło" type="password" outlined
              :rules="[val => !!val || 'Wymagane', val => val.length >= 8 || 'Min 8 znaków']" />
            <q-input v-model="form.passwordConfirm" label="Powtórz hasło" type="password" outlined
              :rules="[val => val === form.password || 'Hasła muszą być identyczne']" />

            <q-btn label="Załóż konto" type="submit" color="primary"
              class="full-width auth-submit" :loading="loading" unelevated size="lg" />
          </q-form>
        </div>
      </div>

    </div>
  </q-page>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useUserStore } from 'stores/user-store'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'

const userStore = useUserStore()
const router = useRouter()
const $q = useQuasar()
const loading = ref(false)

const form = reactive({
  email: '', password: '', passwordConfirm: '',
  is_company: false, company_name: '', nip: '',
  first_name: '', last_name: ''
})

const onSubmit = async () => {
  loading.value = true
  try {
    await userStore.register({ ...form, re_password: form.passwordConfirm })
    $q.notify({ type: 'positive', message: 'Konto utworzone! Zaloguj się.' })
    router.push('/login')
  } catch {
    // Błąd obsłużony przez Axios
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.account-type-toggle {
  padding: 10px 14px;
  border: 1px solid rgba(black, 0.1);
  border-radius: 6px;
  .body--dark & { border-color: rgba(white, 0.1); }
}
</style>
