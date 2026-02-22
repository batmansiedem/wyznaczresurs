<template>
  <q-page class="flex flex-center q-pa-lg">
    <q-card style="width: 350px" class="shadow-10">
      <q-card-section><div class="text-h6">Nowe hasło</div></q-card-section>
      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
           <q-input v-model="pass1" label="Nowe hasło" type="password" filled :rules="[val => !!val || 'Wymagane']" />
           <q-input v-model="pass2" label="Powtórz" type="password" filled :rules="[val => val === pass1 || 'Różne hasła']" />
           <q-btn label="Zapisz" type="submit" color="primary" class="full-width" :loading="loading" />
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

const props = defineProps(['uid', 'token'])
const pass1 = ref('')
const pass2 = ref('')
const loading = ref(false)
const $q = useQuasar()
const router = useRouter()

const onSubmit = async () => {
  loading.value = true
  try {
    await api.post('/auth/password/reset/confirm/', {
      uid: props.uid,
      token: props.token,
      new_password1: pass1.value,
      new_password2: pass2.value
    })
    $q.notify({ type: 'positive', message: 'Zaloguj się nowym hasłem.' })
    router.push('/login')
  } catch { // <--- ZMIANA: Usunięto (e)
    // Tu możemy zostawić customowy komunikat, jeśli Axios nie pokrywa tego przypadku idealnie
    // ale zazwyczaj axios to obsłuży. Jeśli chcemy "nadpisać" komunikat:
    // $q.notify({ type: 'negative', message: 'Link wygasł lub jest nieprawidłowy' })
  } finally {
    loading.value = false
  }
}
</script>