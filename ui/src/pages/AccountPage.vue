<template>
  <q-page padding class="container">
    <div class="calc-page-header q-mb-xl">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Moje konto</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">Zarządzaj swoimi danymi i ustawieniami profilu</p>
    </div>

    <div class="row q-col-gutter-lg">
      <!-- Dane profilu -->
      <div class="col-12 col-md-7">
        <div class="section-label">Dane profilowe</div>
        <q-card flat bordered class="shadow-1 q-pa-md">
          <q-form @submit.prevent="saveProfile" class="q-gutter-md">
            <q-input :model-value="userStore.user?.email" label="Adres e-mail" disable outlined />

            <template v-if="userStore.isCompany">
              <q-input v-model="form.company_name" label="Nazwa firmy" outlined :rules="[v => !!v || 'Nazwa firmy jest wymagana']" />
              <q-input v-model="form.nip" label="NIP" outlined :rules="[v => !!v || 'NIP jest wymagany']" />
            </template>
            <template v-else>
              <div class="row q-col-gutter-md">
                <q-input v-model="form.first_name" label="Imię" outlined class="col-12 col-sm-6" />
                <q-input v-model="form.last_name" label="Nazwisko" outlined class="col-12 col-sm-6" />
              </div>
            </template>

            <q-input v-model="form.address_line" label="Adres (ulica, nr domu/lokalu)" outlined />

            <div class="row q-col-gutter-md">
              <q-input v-model="form.postal_code" label="Kod pocztowy" outlined class="col-4" />
              <q-input v-model="form.city" label="Miasto" outlined class="col-8" />
            </div>

            <div class="q-mt-lg text-right">
              <q-btn type="submit" label="Zapisz zmiany" color="primary" icon="save" unelevated :loading="saving" class="q-px-xl" />
            </div>
          </q-form>
        </q-card>
      </div>

      <!-- Podsumowanie konta -->
      <div class="col-12 col-md-5">
        <div class="section-label">Status konta</div>
        <q-card flat bordered class="shadow-1 q-mb-lg">
          <q-list separator>
            <q-item class="q-py-md">
              <q-item-section>
                <q-item-label caption>Typ konta</q-item-label>
                <q-item-label class="text-h6 text-weight-bold">
                  {{ userStore.isCompany ? 'Firma' : 'Osoba prywatna' }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-icon :name="userStore.isCompany ? 'business' : 'person'" color="primary" size="md" />
              </q-item-section>
            </q-item>
            
            <q-item class="q-py-md">
              <q-item-section>
                <q-item-label caption>Punkty premium</q-item-label>
                <q-item-label class="text-h4 text-weight-bolder text-primary">
                  {{ userStore.user?.premium ?? 0 }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-btn unelevated color="secondary" text-color="primary" label="Doładuj" to="/pricing" no-caps class="text-weight-bold" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>

        <div class="section-label">Bezpieczeństwo</div>
        <q-card flat bordered class="shadow-1 hover-primary">
          <q-list>
            <q-item clickable to="/change-password" class="q-py-md">
              <q-item-section avatar><q-icon name="lock" color="primary" /></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">Zmień hasło dostępu</q-item-label>
                <q-item-label caption>Regularna zmiana hasła zwiększa bezpieczeństwo konta</q-item-label>
              </q-item-section>
              <q-item-section side><q-icon name="chevron_right" /></q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useUserStore } from 'stores/user-store'
import { api } from 'boot/axios'
import { Notify } from 'quasar'

const userStore = useUserStore()
const saving = ref(false)

const form = reactive({
  first_name: '',
  last_name: '',
  company_name: '',
  nip: '',
  address_line: '',
  postal_code: '',
  city: '',
})

watch(() => userStore.user, (u) => {
  if (!u) return
  Object.keys(form).forEach(k => { form[k] = u[k] || '' })
}, { immediate: true })

async function saveProfile () {
  saving.value = true
  try {
    const response = await api.patch('/auth/user/', form)
    userStore.user = response.data
    Notify.create({ type: 'positive', message: 'Dane zostały pomyślnie zaktualizowane.', position: 'top' })
  } catch {
    Notify.create({ type: 'negative', message: 'Nie udało się zapisać zmian.', position: 'top' })
  } finally {
    saving.value = false
  }
}
</script>
