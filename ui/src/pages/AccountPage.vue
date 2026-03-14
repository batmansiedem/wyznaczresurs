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

        <!-- WŁASNE LOGOTYPY -->
        <div class="section-label q-mt-xl">Logotypy na orzeczeniach</div>
        <q-card flat bordered class="shadow-1 q-pa-lg">
          <div class="row q-col-gutter-md items-center q-mb-lg border-bottom q-pb-md">
            <div class="col-12 col-sm">
              <div class="text-subtitle1 text-weight-bold">Personalizacja orzeczeń PDF</div>
              <div class="text-body2 text-grey-7">
                Możesz posiadać wiele logotypów i wybierać, który ma zostać użyty na orzeczeniu.
                Każde kolejne logo kosztuje <strong>200 punktów premium</strong>.
              </div>
            </div>
            <div class="col-12 col-sm-auto">
              <q-btn 
                label="Dodaj nowe logo (200 pkt)" 
                color="primary" 
                unelevated 
                dense
                icon="add_photo_alternate"
                class="q-px-lg"
                :loading="addingLogo"
                @click="showAddLogoDialog = true"
              />
            </div>
          </div>

          <!-- USTAWIENIA PDF W SEKCJI LOGOTYPY -->
          <div class="row q-col-gutter-md q-mb-lg">
            <div class="col-12">
              <div class="text-subtitle2 text-weight-bold q-mb-xs">Ustawienia wyświetlania</div>
              <q-toggle
                v-model="form.show_logo_on_pdf"
                label="Pokazuj logo na orzeczeniu PDF"
                color="primary"
                left-label
                class="full-width justify-between border-toggle q-pa-sm rounded-borders"
                @update:model-value="saveProfile"
              />
              <div class="text-caption text-grey-6 q-mt-xs">
                Opcja ta pozwala na szybkie włączenie lub wyłączenie logotypu na generowanych dokumentach PDF.
              </div>
            </div>
          </div>

          <div v-if="userStore.user?.logos?.length > 0">
            <div class="row q-col-gutter-md">
              <div v-for="logo in userStore.user.logos" :key="logo.id" class="col-12 col-sm-6">
                <q-card flat bordered class="logo-card" :class="{ 'is-default': logo.is_default }">
                  <q-card-section class="row items-center q-pb-none">
                    <div class="text-weight-bold text-subtitle2 ellipsis" style="max-width: 150px">
                      {{ logo.name || 'Bez nazwy' }}
                    </div>
                    <q-chip v-if="logo.is_default" color="primary" text-color="white" size="xs" dense label="Domyślne" class="q-ml-sm" />
                    <q-space />
                    <q-btn icon="more_vert" flat round dense>
                      <q-menu auto-close>
                        <q-list style="min-width: 150px">
                          <q-item clickable @click="editLogo(logo)">
                            <q-item-section avatar><q-icon name="edit" size="xs" /></q-item-section>
                            <q-item-section>Edytuj</q-item-section>
                          </q-item>
                          <q-item clickable @click="setDefaultLogo(logo.id)" :disable="logo.is_default">
                            <q-item-section avatar><q-icon name="check_circle" size="xs" /></q-item-section>
                            <q-item-section>Ustaw domyślne</q-item-section>
                          </q-item>
                          <q-item clickable @click="previewLogoPdf(logo.id)">
                            <q-item-section avatar><q-icon name="picture_as_pdf" size="xs" /></q-item-section>
                            <q-item-section>Podgląd PDF</q-item-section>
                          </q-item>
                          <q-separator />
                          <q-item clickable @click="deleteLogo(logo.id)" class="text-negative">
                            <q-item-section avatar><q-icon name="delete" size="xs" color="negative" /></q-item-section>
                            <q-item-section>Usuń logo</q-item-section>
                          </q-item>
                        </q-list>
                      </q-menu>
                    </q-btn>
                  </q-card-section>

                  <q-card-section class="text-center q-pt-sm">
                    <div class="logo-preview-box rounded-borders overflow-hidden row items-center justify-center">
                      <img :src="getFullLogoUrl(logo.image)" class="responsive-img" />
                    </div>
                    <div class="q-mt-sm text-caption text-grey-7">
                      {{ logo.width }}x{{ logo.height }}mm | {{ logo.position }}
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </div>
          <div v-else class="text-center q-pa-xl text-grey-5 border-dashed rounded-borders">
            <q-icon name="image_not_supported" size="4rem" class="q-mb-md" />
            <div class="text-h6">Nie masz jeszcze żadnych logotypów</div>
            <div class="text-body2">Kliknij przycisk powyżej, aby dodać swoje pierwsze logo.</div>
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
                <q-btn unelevated color="primary" label="Doładuj" to="/pricing" no-caps class="q-px-xl" />
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

    <!-- DIALOG DODAWANIA / EDYCJI LOGA -->
    <q-dialog v-model="showAddLogoDialog" persistent>
      <q-card style="min-width: 400px; max-width: 600px">
        <q-card-section class="bg-primary text-white row items-center">
          <div class="text-h6 text-weight-bold">
            {{ editingLogoId ? 'Edytuj logo' : 'Dodaj nowe logo' }}
          </div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pa-md">
          <q-form @submit="handleLogoSubmit">
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input v-model="logoForm.name" label="Nazwa własna (np. Marka A)" outlined dense />
              </div>
              
              <div class="col-12">
                <q-file
                  v-model="logoForm.imageFile"
                  label="Wybierz plik loga"
                  outlined
                  dense
                  accept=".jpg, .jpeg, .png"
                  :required="!editingLogoId"
                >
                  <template v-slot:prepend>
                    <q-icon name="attach_file" />
                  </template>
                </q-file>
              </div>

              <div class="col-12 col-sm-6">
                <div class="text-caption text-grey-7">Szerokość (mm)</div>
                <q-slider v-model="logoForm.width" :min="20" :max="120" label label-always />
              </div>

              <div class="col-12 col-sm-6">
                <div class="text-caption text-grey-7">Wysokość (mm)</div>
                <q-slider v-model="logoForm.height" :min="10" :max="60" label label-always />
              </div>

              <div class="col-12">
                <div class="text-caption text-grey-7 q-mb-xs">Pozycja na orzeczeniu:</div>
                <q-btn-toggle
                  v-model="logoForm.position"
                  spread no-caps unelevated
                  toggle-color="primary" color="grey-2" text-color="grey-7"
                  :options="[
                    { label: 'Lewo', value: 'left' },
                    { label: 'Góra', value: 'top_center' },
                    { label: 'Prawo', value: 'right' }
                  ]"
                />
              </div>

              <div class="col-12">
                <div class="text-caption text-grey-7 q-mb-xs">Kolor motywu dokumentu:</div>
                <q-input v-model="logoForm.theme_color" outlined dense readonly class="cursor-pointer">
                  <template v-slot:append>
                    <q-icon name="colorize" class="cursor-pointer" color="primary" />
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-color v-model="logoForm.theme_color" no-header-footer />
                    </q-popup-proxy>
                  </template>
                </q-input>
              </div>

              <div class="col-12 q-mt-md" v-if="!editingLogoId">
                <q-banner dense class="bg-orange-1 text-orange-9 rounded-borders">
                  <template v-slot:avatar><q-icon name="warning" /></template>
                  Dodanie nowego logotypu pobierze <strong>200 punktów</strong> z Twojego konta.
                </q-banner>
              </div>

              <div class="col-12 row justify-end q-gutter-sm q-mt-md">
                <q-btn label="Anuluj" flat v-close-popup />
                <q-btn 
                  :label="editingLogoId ? 'Zapisz zmiany' : 'Dodaj i zapłać 200 pkt'" 
                  color="primary" 
                  unelevated 
                  type="submit" 
                  :loading="submittingLogo"
                />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useUserStore } from 'stores/user-store'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'

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
  show_logo_on_pdf: true,
  show_signature_on_pdf: true,
  })

  watch(() => userStore.user, (u) => {
  if (!u) return
  Object.keys(form).forEach(k => { 
  if (k in u) {
    form[k] = u[k]
  }
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

// --- ZARZĄDZANIE LOGOTYPAMI ---
const addingLogo = ref(false)
const showAddLogoDialog = ref(false)
const submittingLogo = ref(false)
const editingLogoId = ref(null)

const logoForm = reactive({
  name: '',
  imageFile: null,
  width: 45,
  height: 20,
  position: 'right',
  theme_color: '#1565C0'
})

function resetLogoForm() {
  logoForm.name = ''
  logoForm.imageFile = null
  logoForm.width = 45
  logoForm.height = 20
  logoForm.position = 'right'
  logoForm.theme_color = '#1565C0'
  editingLogoId.value = null
}

watch(showAddLogoDialog, (val) => {
  if (!val) resetLogoForm()
})

function editLogo(logo) {
  editingLogoId.value = logo.id
  logoForm.name = logo.name
  logoForm.width = logo.width
  logoForm.height = logo.height
  logoForm.position = logo.position
  logoForm.theme_color = logo.theme_color
  showAddLogoDialog.value = true
}

async function handleLogoSubmit() {
  submittingLogo.value = true
  const formData = new FormData()
  if (logoForm.name) formData.append('name', logoForm.name)
  if (logoForm.imageFile) formData.append('image', logoForm.imageFile)
  formData.append('width', logoForm.width)
  formData.append('height', logoForm.height)
  formData.append('position', logoForm.position)
  formData.append('theme_color', logoForm.theme_color)

  try {
    if (editingLogoId.value) {
      await api.patch(`/auth/logos/${editingLogoId.value}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      Notify.create({ type: 'positive', message: 'Logo zostało zaktualizowane.' })
    } else {
      await api.post('/auth/logos/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      Notify.create({ type: 'positive', message: 'Nowe logo zostało dodane.' })
    }
    await userStore.fetchUser()
    showAddLogoDialog.value = false
  } catch (err) {
    Notify.create({ 
      type: 'negative', 
      message: err.response?.data?.detail || 'Błąd podczas zapisywania loga.' 
    })
  } finally {
    submittingLogo.value = false
  }
}

async function setDefaultLogo(id) {
  try {
    await api.post(`/auth/logos/${id}/set_default/`)
    await userStore.fetchUser()
    Notify.create({ type: 'positive', message: 'Zmieniono domyślne logo.' })
  } catch {
    Notify.create({ type: 'negative', message: 'Błąd podczas ustawiania domyślnego loga.' })
  }
}

async function deleteLogo(id) {
  Dialog.create({
    title: 'Usuń logo',
    message: 'Czy na pewno chcesz usunąć to logo? Ta operacja jest nieodwracalna.',
    cancel: true,
    persistent: true,
    ok: { color: 'negative', label: 'Usuń' }
  }).onOk(async () => {
    try {
      await api.delete(`/auth/logos/${id}/`)
      await userStore.fetchUser()
      Notify.create({ type: 'positive', message: 'Logo zostało usunięte.' })
    } catch {
      Notify.create({ type: 'negative', message: 'Błąd podczas usuwania loga.' })
    }
  })
}

async function previewLogoPdf(id) {
  try {
    const response = await api.get(`/auth/logo-preview/?logo_id=${id}`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    window.open(url, '_blank')
  } catch {
    Notify.create({ type: 'negative', message: 'Nie udało się wygenerować podglądu.', position: 'top' })
  }
}

function getFullLogoUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const base = api.defaults.baseURL.replace(/\/api\/?$/, '')
  const path = url.startsWith('/') ? url : '/' + url
  return `${base}${path}`
}
</script>

<style scoped>
.logo-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(0,0,0,0.12);
}
.logo-card.is-default {
  border: 2px solid var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.02);
}
.logo-preview-box {
  width: 100%;
  height: 120px;
  background: white;
  border: 1px dashed #ccc;
}
.responsive-img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}
.border-dashed {
  border: 2px dashed #ccc;
}
.border-toggle {
  border: 1px solid rgba(0,0,0,0.12);
  transition: background 0.3s;
}
.border-toggle:hover {
  background: rgba(0,0,0,0.02);
}
.body--dark .border-toggle {
  border-color: rgba(255,255,255,0.12);
}
.body--dark .logo-preview-box {
  background: #1d1d1d;
  border-color: #444;
}
</style>
