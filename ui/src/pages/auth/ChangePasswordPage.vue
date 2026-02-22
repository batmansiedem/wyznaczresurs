<template>
  <q-page class="q-pa-md">
    <q-card style="max-width: 500px; margin: 0 auto">
      <q-card-section><div class="text-h6">Zmiana hasła</div></q-card-section>
      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input v-model="oldPassword" label="Obecne hasło" type="password" filled :rules="[val => !!val || 'Wymagane']" />
          <q-input v-model="newPassword" label="Nowe hasło" type="password" filled :rules="[val => !!val || 'Wymagane']" />
          <q-input v-model="confirmPassword" label="Powtórz" type="password" filled :rules="[val => val === newPassword || 'Różne hasła']" />
          <q-btn label="Zmień" type="submit" color="primary" :loading="loading" />
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const $q = useQuasar()
const router = useRouter()

const onSubmit = async () => {
  loading.value = true
  try {
    await api.post('/auth/password/change/', {
      old_password: oldPassword.value,
      new_password1: newPassword.value,
      new_password2: confirmPassword.value
    })
    $q.notify({ type: 'positive', message: 'Hasło zmienione' })
    router.push('/')
  } catch { // <--- ZMIANA: Usunięto (e)
    // Błąd obsłużony przez Axios
  } finally {
    loading.value = false
  }
}
</script>