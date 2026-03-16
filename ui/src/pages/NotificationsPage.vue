<template>
  <q-page padding class="container">
    <div class="row items-center q-mb-lg">
      <div class="col calc-page-header" style="margin-bottom:0">
        <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Powiadomienia i E-maile</h1>
        <p class="text-subtitle1 text-grey-7 q-mb-none">
          Wysyłaj wiadomości e-mail do użytkowników serwisu.
        </p>
      </div>
    </div>

    <div class="row q-col-gutter-lg">
      <!-- Formularz wysyłki -->
      <div class="col-12 col-md-7">
        <q-card flat bordered class="rounded-borders shadow-1">
          <q-card-section class="row items-center border-b">
            <div class="text-h6 text-primary text-weight-bold">Nowa wiadomość</div>
            <q-space />
            <q-icon name="send" color="primary" size="sm" class="email-animation" />
          </q-card-section>

          <q-card-section class="q-pa-md">
            <q-form @submit="sendEmail" class="q-gutter-y-md">
              <!-- Odbiorcy -->
              <div class="row q-col-gutter-md">
                <div class="col-12">
                  <q-toggle
                    v-model="formData.all_users"
                    label="Wyślij do wszystkich aktywnych użytkowników"
                    color="primary"
                    @update:model-value="onAllUsersToggle"
                  />
                </div>
                
                <div class="col-12" v-if="!formData.all_users">
                  <div class="row items-center q-mb-sm q-gutter-sm">
                    <div class="text-caption text-grey-7">Szybki wybór:</div>
                    <q-btn size="xs" outline color="primary" label="Wszyscy" @click="selectAll" />
                    <q-btn size="xs" outline color="primary" label="Wszystkie firmy" @click="selectCompanies" />
                    <q-btn size="xs" outline color="primary" label="Wszystkie osoby" @click="selectIndividuals" />
                    <q-btn size="xs" outline color="negative" label="Wyczyść" @click="formData.user_ids = []" />
                    <q-space />
                    <div class="text-caption text-weight-bold" :class="formData.user_ids.length > 0 ? 'text-primary' : 'text-grey'">
                      Wybrano: {{ formData.user_ids.length }}
                    </div>
                  </div>
                  
                  <q-select
                    v-model="formData.user_ids"
                    :options="filteredUserOptions"
                    label="Wyszukaj odbiorców (imię, nazwa, e-mail)"
                    multiple
                    use-chips
                    stack-label
                    emit-value
                    map-options
                    option-value="id"
                    option-label="display_name"
                    outlined
                    use-input
                    @filter="filterUsers"
                    :rules="[val => !!val && val.length > 0 || 'Wybierz przynajmniej jednego odbiorcę']"
                  >
                    <template v-slot:no-option>
                      <q-item>
                        <q-item-section class="text-grey">
                          Nie znaleziono użytkownika
                        </q-item-section>
                      </q-item>
                    </template>
                  </q-select>
                </div>
              </div>

              <!-- Bonus Code Option -->
              <div class="row q-col-gutter-md q-mb-sm">
                <div class="col-12 col-sm-6">
                  <q-checkbox
                    v-model="formData.include_bonus_code"
                    label="Dołącz kod na punkty PREMIUM"
                    color="secondary"
                  />
                </div>
                <div class="col-12 col-sm-6" v-if="formData.include_bonus_code">
                  <q-input
                    v-model.number="formData.bonus_points"
                    type="number"
                    label="Liczba punktów w kodzie"
                    outlined
                    dense
                    :rules="[val => !!val && val > 0 || 'Podaj liczbę punktów']"
                  />
                </div>
              </div>

              <!-- Temat -->
              <q-input
                v-model="formData.subject"
                label="Temat wiadomości"
                outlined
                :rules="[val => !!val || 'Temat jest wymagany']"
              />

              <!-- Treść -->
              <div class="text-subtitle2 q-mb-xs">Treść wiadomości (HTML)</div>
              <q-editor
                v-model="formData.content"
                min-height="300px"
                :toolbar="[
                  ['bold', 'italic', 'strike', 'underline'],
                  ['quote', 'unordered', 'ordered', 'outdent', 'indent'],
                  ['undo', 'redo'],
                  ['viewsource']
                ]"
                flat
                bordered
              />

              <div class="row justify-end q-mt-md">
                <q-btn
                  label="Wyślij wiadomość"
                  color="primary"
                  icon="send"
                  type="submit"
                  :loading="sending"
                  class="send-btn"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </div>

      <!-- Podgląd -->
      <div class="col-12 col-md-5">
        <div class="section-label">Podgląd stylu e-maila</div>
        <q-card flat bordered class="rounded-borders shadow-1 overflow-hidden email-preview-card" style="min-height: 400px;">
          <!-- Hero Section (Backend style) -->
          <div style="background: linear-gradient(145deg, #1565C0 0%, #0c3c73 100%); color: #ffffff; padding: 40px 20px; text-align: center;">
            <div style="font-size: 28px; font-weight: 900; letter-spacing: -1px;">
              wyznacz<span style="color: #1976D2;">resurs</span>.com
            </div>
            <div v-if="formData.subject" style="margin-top: 10px; font-size: 14px; opacity: 0.85; font-weight: 400;">
              {{ formData.subject }}
            </div>
          </div>

          <!-- Compliance Strip -->
          <div style="background-color: #0A1929; color: #ffffff; padding: 10px 15px; text-align: center; font-family: monospace; font-size: 9px; letter-spacing: 1px; text-transform: uppercase; border-bottom: 2px solid #1976D2;">
            FEM 9.511 &bull; ISO 4301 &bull; ROZP. MPiT 2018 &bull; UDT
          </div>
          
          <!-- Content Container -->
          <div class="email-content-wrapper">
            <div class="email-body">
              <div v-html="formData.content || '<p class=\'text-grey-5\'>Wprowadź treść wiadomości, aby zobaczyć podgląd...</p>'"></div>
              
              <!-- Bonus Code Preview -->
              <div v-if="formData.include_bonus_code && formData.bonus_points" class="bonus-code-box">
                <div style="font-size: 11px; color: #1565C0; font-weight: 700; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;">
                  Twój kod bonusowy na punkty premium
                </div>
                <div style="font-family: monospace; font-size: 20px; font-weight: 900; color: #0A1929; letter-spacing: 2px; margin-bottom: 5px;">
                  ABCD-1234-EFGH
                </div>
                <div style="font-size: 14px; color: #1976D2; font-weight: 700;">
                  +{{ formData.bonus_points }} pkt PREMIUM
                </div>
                <div style="font-size: 10px; color: #64748B; margin-top: 10px;">
                  Kod możesz zrealizować w panelu użytkownika.
                </div>
              </div>
            </div>
          </div>
          
          <!-- Footer -->
          <div style="background-color: #0A1929; padding: 30px 20px; text-align: center; color: rgba(255, 255, 255, 0.5); font-size: 10px;">
            <div style="font-weight: 700; color: #ffffff; font-size: 12px; margin-bottom: 8px;">
              wyznaczresurs.com
            </div>
            Profesjonalny system wyznaczania resursu UTB.<br>
            Zgodność z normami FEM/ISO i wymogami UDT.<br><br>
            &copy; {{ new Date().getFullYear() }} Wszystkie prawa zastrzeżone.
          </div>
        </q-card>

        <div class="q-mt-md">
          <q-banner dense class="bg-blue-1 text-primary rounded-borders">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            Wiadomość zostanie wysłana w profesjonalnym szablonie HTML zgodnym z identyfikacją wizualną serwisu.
          </q-banner>
        </div>
      </div>
    </div>

    <!-- Dialog po wysyłce -->
    <q-dialog v-model="showResultDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section class="row items-center">
          <q-avatar icon="check_circle" color="positive" text-color="white" v-if="resultData?.success_count > 0" />
          <q-avatar icon="error" color="negative" text-color="white" v-else />
          <span class="q-ml-sm text-h6">Status wysyłki</span>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <p v-if="resultData">
            {{ resultData.detail }}
          </p>
          <div v-if="resultData?.errors && resultData.errors.length" class="q-mt-md">
            <div class="text-weight-bold text-negative">Wystąpiły błędy:</div>
            <q-scroll-area style="height: 100px;">
              <ul class="q-pl-md">
                <li v-for="(err, idx) in resultData.errors" :key="idx" class="text-caption">{{ err }}</li>
              </ul>
            </q-scroll-area>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Zamknij" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Notify } from 'quasar'

const formData = ref({
  all_users: false,
  user_ids: [],
  subject: '',
  content: '',
  include_bonus_code: false,
  bonus_points: 100
})

const userOptions = ref([])
const filteredUserOptions = ref([])
const sending = ref(false)
const showResultDialog = ref(false)
const resultData = ref(null)

const fetchUsers = async () => {
  try {
    const response = await api.get('/notifications/users-list/')
    userOptions.value = response.data
    filteredUserOptions.value = response.data
  } catch (error) {
    console.error('Błąd pobierania użytkowników:', error)
    Notify.create({ type: 'negative', message: 'Nie udało się pobrać listy użytkowników.', position: 'top' })
  }
}

const filterUsers = (val, update) => {
  if (val === '') {
    update(() => {
      filteredUserOptions.value = userOptions.value
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    filteredUserOptions.value = userOptions.value.filter(
      v => v.display_name.toLowerCase().indexOf(needle) > -1
    )
  })
}

const selectAll = () => {
  formData.value.user_ids = userOptions.value.map(u => u.id)
}

const selectCompanies = () => {
  formData.value.user_ids = userOptions.value
    .filter(u => u.is_company)
    .map(u => u.id)
}

const selectIndividuals = () => {
  formData.value.user_ids = userOptions.value
    .filter(u => !u.is_company)
    .map(u => u.id)
}

const onAllUsersToggle = (val) => {
  if (val) formData.value.user_ids = []
}

const sendEmail = async () => {
  sending.value = true
  try {
    const response = await api.post('/notifications/send-email/', formData.value)
    resultData.value = response.data
    showResultDialog.value = true
    
    // Resetuj formularz jeśli sukces
    if (response.data.success_count > 0 && !response.data.errors) {
      formData.value = {
        all_users: false,
        user_ids: [],
        subject: '',
        content: ''
      }
    }
  } catch (error) {
    const errorMsg = error.response?.data?.detail || 'Wystąpił nieoczekiwany błąd podczas wysyłki.'
    Notify.create({ type: 'negative', message: errorMsg, position: 'top' })
    resultData.value = error.response?.data
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style lang="scss" scoped>
.email-animation {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translateY(0) rotate(0); }
  50% { transform: translateY(-5px) rotate(5deg); }
  100% { transform: translateY(0) rotate(0); }
}

.send-btn {
  transition: all 0.3s;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(var(--q-primary-rgb), 0.3);
  }
}

.border-b {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  .body--dark & {
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  }
}

.email-preview-card {
  background: #f4f7f9;
  .body--dark & {
    background: #0d1b2a;
  }
}

.email-content-wrapper {
  padding: 30px 25px;
  margin: 0 15px;
}

.email-body {
  background: white;
  padding: 30px;
  border-radius: 4px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  color: #334155;
  line-height: 1.6;
  min-height: 200px;
}

.bonus-code-box {
  margin-top: 30px;
  text-align: center;
  border: 2px dashed #1976D2;
  padding: 20px;
  border-radius: 8px;
  background-color: #f8fbff;
}
</style>
