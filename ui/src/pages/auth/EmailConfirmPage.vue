<template>
  <div class="confirm-wrapper">
    <div class="confirm-card">

      <div class="confirm-logo">wyznacz<span>resurs</span>.pl</div>

      <!-- Ładowanie -->
      <template v-if="status === 'loading'">
        <q-spinner color="primary" size="3em" class="q-mb-md" />
        <div class="confirm-title">Weryfikacja adresu e-mail...</div>
      </template>

      <!-- Sukces -->
      <template v-else-if="status === 'success'">
        <q-icon name="check_circle" color="positive" size="4em" class="q-mb-md" />
        <div class="confirm-title">Konto aktywowane!</div>
        <p class="confirm-sub">Twój adres e-mail został potwierdzony. Możesz się teraz zalogować.</p>
        <q-btn unelevated color="primary" label="Przejdź do logowania" to="/login" class="q-mt-md full-width" no-caps size="lg" />
      </template>

      <!-- Błąd -->
      <template v-else-if="status === 'error'">
        <q-icon name="error_outline" color="negative" size="4em" class="q-mb-md" />
        <div class="confirm-title">Link nieważny lub wygasły</div>
        <p class="confirm-sub">{{ errorMessage }}</p>
        <q-btn unelevated color="primary" label="Zaloguj się" to="/login" class="q-mt-md full-width" no-caps />
        <q-btn flat color="primary" label="Zarejestruj się ponownie" to="/register" class="q-mt-sm full-width" no-caps />
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'

const route = useRoute()
const status = ref('loading')
const errorMessage = ref('')

onMounted(async () => {
  const key = route.params.key
  if (!key) {
    status.value = 'error'
    errorMessage.value = 'Brak klucza weryfikacyjnego w adresie URL.'
    return
  }
  try {
    await api.post('/auth/registration/verify-email/', { key })
    status.value = 'success'
  } catch (e) {
    status.value = 'error'
    errorMessage.value = e.response?.data?.detail || 'Link weryfikacyjny jest nieważny lub wygasł. Zarejestruj się ponownie.'
  }
})
</script>

<style scoped>
.confirm-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f7fa;
  padding: 24px;
}

.confirm-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(10, 25, 41, 0.12);
  padding: 48px 40px;
  max-width: 440px;
  width: 100%;
  text-align: center;
}

.confirm-logo {
  font-size: 24px;
  font-weight: 900;
  color: #1565c0;
  letter-spacing: -0.5px;
  margin-bottom: 32px;
}

.confirm-logo span {
  color: #90caf9;
}

.confirm-title {
  font-size: 22px;
  font-weight: 800;
  color: #0a1929;
  margin-bottom: 12px;
}

.confirm-sub {
  font-size: 15px;
  color: #64748b;
  line-height: 1.6;
  margin: 0;
}
</style>
