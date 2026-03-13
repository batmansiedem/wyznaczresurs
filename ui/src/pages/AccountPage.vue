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
        <q-card flat bordered class="shadow-1 q-pa-lg">
          <q-form @submit.prevent="saveProfile">
            <div class="row q-col-gutter-md">
              <!-- Podstawowe dane -->
              <div class="col-12">
                <q-input :model-value="userStore.user?.email" label="Adres e-mail" disable outlined />
              </div>

              <!-- Firma -->
              <template v-if="userStore.isCompany">
                <div class="col-12">
                  <q-input v-model="form.company_name" label="Nazwa firmy" outlined :rules="[v => !!v || 'Nazwa firmy jest wymagana']" />
                </div>
                <div class="col-12">
                  <q-input v-model="form.nip" label="NIP" outlined :rules="[v => !!v || 'NIP jest wymagany']" />
                </div>
              </template>

              <!-- Osoba prywatna -->
              <template v-else>
                <div class="col-12 col-sm-6">
                  <q-input v-model="form.first_name" label="Imię" outlined />
                </div>
                <div class="col-12 col-sm-6">
                  <q-input v-model="form.last_name" label="Nazwisko" outlined />
                </div>
              </template>

              <!-- Adres -->
              <div class="col-12">
                <q-input v-model="form.address_line" label="Adres (ulica, nr domu/lokalu)" outlined />
              </div>
              <div class="col-12 col-sm-4">
                <q-input v-model="form.postal_code" label="Kod pocztowy" outlined />
              </div>
              <div class="col-12 col-sm-8">
                <q-input v-model="form.city" label="Miasto" outlined />
              </div>

              <!-- Akcja -->
              <div class="col-12 q-mt-md">
                <div class="row justify-end">
                  <q-btn type="submit" label="Zapisz zmiany" color="primary" icon="save" unelevated :loading="saving" class="q-px-xl" />
                </div>
              </div>
            </div>
          </q-form>
        </q-card>

        <!-- WŁASNE LOGO -->
        <div class="section-label q-mt-xl">Własne logo na orzeczeniach</div>
        <q-card flat bordered class="shadow-1 q-pa-lg">
          <div v-if="!userStore.user?.has_custom_logo">
            <div class="row items-center q-col-gutter-md">
              <div class="col-12 col-sm-8">
                <div class="text-subtitle1 text-weight-bold">Personalizacja orzeczeń PDF</div>
                <div class="text-body2 text-grey-7">
                  Możesz umieścić własne logo w nagłówku każdego wygenerowanego orzeczenia. 
                  Koszt aktywacji tej funkcji to jednorazowo <strong>200 punktów premium</strong>.
                </div>
              </div>
              <div class="col-12 col-sm-4 text-center">
                <q-btn 
                  label="Aktywuj za 200 pkt" 
                  color="secondary" 
                  text-color="primary" 
                  unelevated 
                  icon="stars"
                  class="text-weight-bold full-width"
                  :loading="activatingLogo"
                  @click="purchaseLogo"
                />
              </div>
            </div>
          </div>

          <div v-else>
            <div class="row q-col-gutter-lg items-center">
              <div class="col-12 col-sm-4 text-center">
                <div class="text-caption text-grey-6 q-mb-sm">Aktualne logo:</div>
                <div class="logo-preview-box border-grey rounded-borders overflow-hidden row items-center justify-center">
                  <img v-if="userStore.user?.custom_logo" :src="getFullLogoUrl(userStore.user.custom_logo)" class="responsive-img" />
                  <div v-else class="text-grey-4 column items-center">
                    <q-icon name="image" size="3rem" />
                    <span>Brak pliku</span>
                  </div>
                </div>
              </div>
              <div class="col-12 col-sm-8">
                <div class="text-subtitle1 text-weight-bold q-mb-sm">Wgraj plik logotypu</div>
                <q-file
                  v-model="logoFile"
                  label="Wybierz plik (PNG, JPG, max 2MB)"
                  outlined
                  dense
                  accept=".jpg, .jpeg, .png"
                  max-file-size="2097152"
                  @rejected="onFileRejected"
                >
                  <template v-slot:prepend>
                    <q-icon name="attach_file" />
                  </template>
                </q-file>
                <div class="q-mt-md row q-gutter-sm">
                  <q-btn 
                    label="Wyślij na serwer" 
                    color="primary" 
                    unelevated 
                    :loading="uploadingLogo" 
                    :disable="!logoFile"
                    @click="uploadLogo" 
                  />
                  <q-btn 
                    v-if="userStore.user?.custom_logo" 
                    label="Zobacz przykład (PDF)" 
                    color="secondary" 
                    text-color="primary"
                    unelevated 
                    icon="picture_as_pdf"
                    :loading="previewingLogo"
                    @click="previewLogoPdf" 
                  />
                  <q-btn 
                    v-if="userStore.user?.custom_logo" 
                    label="Usuń logo" 
                    color="negative" 
                    flat 
                    dense 
                    @click="removeLogo" 
                  />
                </div>
                <p class="text-caption text-grey-6 q-mt-sm">
                  Zalecany format: poziomy, przeźroczyste tło (PNG). Logo zostanie umieszczone zgodnie z Twoimi ustawieniami poniżej.
                </p>

                <q-separator class="q-my-lg" />

                <!-- USTAWIENIA WYDRUKU -->
                <div class="text-subtitle2 text-primary q-mb-md">Parametry wyświetlania na PDF</div>
                
                <div class="row q-col-gutter-xl">
                  <div class="col-12 col-sm-6">
                    <div class="q-mb-lg">
                      <div class="text-caption text-grey-7 q-mb-sm">Maksymalna szerokość: <strong>{{ form.logo_width }} mm</strong></div>
                      <q-slider
                        v-model="form.logo_width"
                        :min="20"
                        :max="120"
                        :step="5"
                        label
                        label-always
                        color="primary"
                      />
                    </div>

                    <div class="q-mb-md">
                      <div class="text-caption text-grey-7 q-mb-sm">Maksymalna wysokość: <strong>{{ form.logo_height }} mm</strong></div>
                      <q-slider
                        v-model="form.logo_height"
                        :min="10"
                        :max="60"
                        :step="5"
                        label
                        label-always
                        color="primary"
                      />
                    </div>
                  </div>
                  
                  <div class="col-12 col-sm-6">
                    <div class="text-caption text-grey-7 q-mb-sm">Wyrównanie / Pozycja:</div>
                    <q-btn-toggle
                      v-model="form.logo_position"
                      spread
                      no-caps
                      unelevated
                      toggle-color="primary"
                      color="grey-2"
                      text-color="grey-7"
                      :options="[
                        { label: 'Lewo', value: 'left' },
                        { label: 'Góra', value: 'top_center' },
                        { label: 'Prawo', value: 'right' }
                      ]"
                    />
                  </div>

                  <div class="col-12 col-sm-6">
                    <div class="text-caption text-grey-7 q-mb-sm">Kolor motywu dokumentu:</div>
                    <q-input
                      v-model="form.theme_color"
                      outlined
                      dense
                      class="cursor-pointer"
                      readonly
                    >
                      <template v-slot:append>
                        <q-icon name="colorize" class="cursor-pointer" color="primary">
                          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                            <q-color v-model="form.theme_color" no-header-footer />
                          </q-popup-proxy>
                        </q-icon>
                      </template>
                    </q-input>
                  </div>

                  <div class="col-12">
                    <div class="q-mt-md text-caption text-grey-6">
                      <q-icon name="info" size="xs" class="q-mr-xs" />
                      Wymiary są traktowane jako <strong>maksymalne ograniczenia</strong>. System zachowa oryginalne proporcje Twojego logotypu. Wybrany kolor motywu zostanie zastosowany do tabel i nagłówków na wydruku.
                    </div>
                  </div>
                </div>

                <div class="q-mt-md row justify-end">
                  <q-btn 
                    label="Zapisz ustawienia wydruku" 
                    color="primary" 
                    icon="settings" 
                    unelevated 
                    :loading="saving"
                    @click="saveProfile"
                  />
                </div>
              </div>
            </div>
          </div>
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
  logo_width: 45,
  logo_height: 20,
  logo_position: 'right',
  theme_color: '#1565C0',
})

watch(() => userStore.user, (u) => {
  if (!u) return
  Object.keys(form).forEach(k => { 
    form[k] = u[k] || (k === 'logo_width' ? 45 : k === 'logo_height' ? 20 : k === 'logo_position' ? 'right' : k === 'theme_color' ? '#1565C0' : '') 
  })
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

// --- WŁASNE LOGO ---
const activatingLogo = ref(false)
const uploadingLogo = ref(false)
const previewingLogo = ref(false)
const logoFile = ref(null)

async function purchaseLogo() {
  activatingLogo.value = true
  try {
    const response = await api.post('/auth/purchase-custom-logo/')
    userStore.user.has_custom_logo = response.data.has_custom_logo
    userStore.user.premium = response.data.premium
    Notify.create({ type: 'positive', message: response.data.message, position: 'top' })
  } catch (error) {
    Notify.create({ 
      type: 'negative', 
      message: error.response?.data?.detail || 'Błąd podczas aktywacji funkcji.', 
      position: 'top' 
    })
  } finally {
    activatingLogo.value = false
  }
}

async function uploadLogo() {
  if (!logoFile.value) return
  uploadingLogo.value = true
  
  const formData = new FormData()
  formData.append('custom_logo', logoFile.value)
  
  try {
    const response = await api.post('/auth/upload-logo/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    Notify.create({ type: 'positive', message: response.data.message, position: 'top' })
    // Odśwież dane użytkownika, aby pobrać nowy URL do logo
    await userStore.fetchUser()
    logoFile.value = null
  } catch (error) {
    Notify.create({ 
      type: 'negative', 
      message: error.response?.data?.detail || 'Błąd podczas wgrywania pliku.', 
      position: 'top' 
    })
  } finally {
    uploadingLogo.value = false
  }
}

async function removeLogo() {
  // Możemy to zrobić przez patch na /auth/user/ ustawiając custom_logo na null
  // lub stworzyć dedykowany endpoint. Dla uproszczenia tutaj:
  try {
    const formData = new FormData()
    formData.append('custom_logo', '') // Django zazwyczaj czyści plik przy pustym stringu lub przez PATCH
    await api.patch('/auth/user/', { custom_logo: null })
    await userStore.fetchUser()
    Notify.create({ type: 'positive', message: 'Logo zostało usunięte.', position: 'top' })
  } catch {
    Notify.create({ type: 'negative', message: 'Błąd podczas usuwania loga.', position: 'top' })
  }
}

function onFileRejected() {
  Notify.create({
    type: 'negative',
    message: 'Plik jest za duży lub ma niepoprawny format.'
  })
}

async function previewLogoPdf() {
  previewingLogo.value = true
  try {
    const response = await api.get('/auth/logo-preview/', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    window.open(url, '_blank')
  } catch {
    Notify.create({ type: 'negative', message: 'Nie udało się wygenerować podglądu.', position: 'top' })
  } finally {
    previewingLogo.value = false
  }
}

function getFullLogoUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  // Usuń końcowe / z baseUrl i początkowe / z url, potem połącz
  const base = api.defaults.baseURL.replace(/\/api\/?$/, '')
  const path = url.startsWith('/') ? url : '/' + url
  return `${base}${path}`
}
</script>

<style scoped>
.logo-preview-box {
  width: 100%;
  height: 120px;
  background: #f9f9f9;
  border: 1px dashed #ccc;
}
.responsive-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.border-grey {
  border: 1px solid rgba(0,0,0,0.12);
}
.body--dark .logo-preview-box {
  background: #1d1d1d;
  border-color: #444;
}
</style>
