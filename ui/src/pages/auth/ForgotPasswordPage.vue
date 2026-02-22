<template>
  <q-page class="flex flex-center q-pa-lg">
    <q-card style="width: 350px" class="shadow-10">
      <q-card-section><div class="text-h6">Reset Hasła</div></q-card-section>
      <q-card-section>
        <q-form @submit="onSubmit">
           <q-input v-model="email" label="Email" type="email" filled :rules="[val => !!val || 'Wymagane']" />
           <q-btn label="Wyślij link" type="submit" color="primary" class="full-width q-mt-md" :loading="loading" />
        </q-form>
      </q-card-section>
      <q-card-section class="text-center"><q-btn flat label="Wróć" to="/login" /></q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const email = ref('')
const loading = ref(false)
const $q = useQuasar()

const onSubmit = async () => {
  loading.value = true
  try {
    await api.post('/auth/password/reset/', { email: email.value })
    $q.notify({ type: 'positive', message: 'Sprawdź email' })
  } catch { // <--- ZMIANA: Usunięto (e)
     // Błąd obsłużony przez Axios
  } finally {
    loading.value = false
  }
}
</script>