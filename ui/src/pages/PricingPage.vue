<template>
  <!-- ===== LANDING VERSION (niezalogowani) ===== -->
  <q-page v-if="!userStore.isLoggedIn" class="lp">

    <section class="pricing-hero text-white">
      <div class="ph-bg" aria-hidden="true">
        <svg viewBox="0 0 1200 360" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="ph-m" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M20 0L0 0 0 20" fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.12"/>
            </pattern>
            <pattern id="ph-M" width="100" height="100" patternUnits="userSpaceOnUse">
              <rect width="100" height="100" fill="url(#ph-m)"/>
              <path d="M100 0L0 0 0 100" fill="none" stroke="white" stroke-width="0.6" stroke-opacity="0.18"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#ph-M)"/>
          <g transform="translate(1140, 180)" stroke="white" fill="none" stroke-opacity="0.14">
            <circle r="220" stroke-width="0.5"/><circle r="170" stroke-width="0.7"/>
            <circle r="120" stroke-width="0.5"/><circle r="70" stroke-width="0.9"/>
            <line x1="-240" x2="240" y1="0" y2="0" stroke-width="0.5"/>
            <line x1="0" x2="0" y1="-240" y2="240" stroke-width="0.5"/>
            <circle r="4" fill="white" stroke="none" fill-opacity="0.2"/>
          </g>
          <g transform="translate(1160, 330)" stroke="white" fill="none" stroke-opacity="0.14">
            <path d="M0 -280 L0 0" stroke-width="1"/>
            <line x1="-7" y1="-70" x2="7" y2="-70" stroke-width="1"/>
            <line x1="-7" y1="-140" x2="7" y2="-140" stroke-width="1"/>
            <line x1="-7" y1="-210" x2="7" y2="-210" stroke-width="1"/>
          </g>
        </svg>
      </div>
      <div class="lc q-mx-auto q-px-md" style="position:relative;z-index:1;text-align:center">
        <div class="norm-chips q-mb-lg" style="justify-content:center">
          <span class="norm-chip">100 pkt / obliczenie</span>
          <span class="norm-chip">1 pkt ≈ 1 PLN brutto</span>
        </div>
        <h1 class="page-h1">Cennik i punkty</h1>
        <p class="page-sub">Bez abonamentów — kupujesz punkty i rozliczasz tylko wykonane obliczenia.</p>
      </div>
    </section>

    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <PricingCards />
      </div>
    </section>

    <section class="points-section q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="text-center q-mb-xl">
          <div class="eyebrow">System punktowy</div>
          <h2 class="section-h2">Jak działają punkty?</h2>
        </div>
        <div class="row q-col-gutter-lg">
          <div v-for="pt in pointsSteps" :key="pt.num" class="col-12 col-md-3">
            <div class="pts-card">
              <div class="pts-num">{{ pt.num }}</div>
              <q-icon :name="pt.icon" size="28px" color="primary" class="q-mb-md" />
              <div class="pts-title">{{ pt.title }}</div>
              <div class="pts-text">{{ pt.text }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="text-center q-mb-xl">
          <div class="eyebrow">Płatności</div>
          <h2 class="section-h2">Metody doładowania konta</h2>
        </div>
        <div class="row q-col-gutter-lg">
          <div class="col-12 col-md-4">
            <div class="pay-card">
              <div class="pay-card-header">
                <q-icon name="account_balance" size="22px" color="primary" />
                <span class="pay-card-title">Przelew bankowy</span>
              </div>
              <div class="bank-details">
                <div class="bank-row"><span class="bank-key">Odbiorca</span><span class="bank-val">EDS</span></div>
                <div class="bank-row"><span class="bank-key">Nr konta</span><span class="bank-val bank-val--accent">60 1240 3116 1111 0010 9288 1740</span></div>
                <div class="bank-row"><span class="bank-key">Tytułem</span><span class="bank-val">login: <em>twój_login</em>, premium_pkt: <em>ilość</em></span></div>
              </div>
              <p class="pay-note">Punkty dodawane do 24h od zaksięgowania przelewu.</p>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="pay-card">
              <div class="pay-card-header">
                <q-icon name="contactless" size="22px" color="primary" />
                <span class="pay-card-title">BLIK na numer telefonu</span>
              </div>
              <div class="bank-details">
                <div class="bank-row"><span class="bank-key">Telefon</span><span class="bank-val bank-val--accent">+48 666 625 752</span></div>
                <div class="bank-row"><span class="bank-key">Tytułem</span><span class="bank-val">BLIK na telefon, login: <em>twój_login</em>, premium_pkt: <em>ilość</em></span></div>
              </div>
              <p class="pay-note">Punkty dodawane do 24h po potwierdzeniu płatności.</p>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="pay-card">
              <div class="pay-card-header">
                <q-icon name="payments" size="22px" color="primary" />
                <span class="pay-card-title">PayPal — automatyczne doładowanie</span>
              </div>
              <p class="text-grey-7 text-body2 q-mb-lg">Punkty pojawiają się na koncie natychmiast po płatności.</p>
              <div class="pts-badges">
                <div v-for="pkg in fixedPackages" :key="pkg.pts" class="pts-pkg">
                  <div class="pts-pkg-num">{{ pkg.pts }}</div>
                  <div class="pts-pkg-label">pkt</div>
                  <div class="pts-pkg-price">{{ pkg.price }} PLN</div>
                </div>
              </div>
              <p class="pay-note q-mt-md">Zaloguj się, aby zapłacić przez PayPal.</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="pricing-cta text-white text-center">
      <div class="lc q-mx-auto q-px-md">
        <h2 class="section-h2 text-white q-mb-sm">Gotowy do pracy?</h2>
        <p class="q-mb-xl" style="color:rgba(255,255,255,0.5)">Zarejestruj się bezpłatnie. Punkty dokupujesz gdy potrzebujesz.</p>
        <q-btn unelevated size="lg" color="primary" label="Otwórz konto" to="/register" class="text-weight-bold q-mr-md" />
        <q-btn outline size="lg" color="white" label="Zaloguj się" to="/login" />
      </div>
    </section>

  </q-page>

  <!-- ===== DASHBOARD VERSION (zalogowani) ===== -->
  <q-page v-else padding>
    <div class="calc-page-header q-mb-xl">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Cennik i punkty</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">100 punktów za jedno obliczenie resursu · 1 pkt ≈ 1 PLN brutto</p>
    </div>

    <PricingCards />

    <q-separator class="q-my-xl" />
    <div class="section-label q-mb-lg">Metody doładowania konta</div>

    <div class="row q-col-gutter-lg">

      <!-- ======= PAYPAL (priorytetowa, szersza kolumna) ======= -->
      <div class="col-12 col-lg-7">
        <q-card flat bordered class="rounded-borders shadow-1 paypal-main-card">

          <!-- Nagłówek z akcentem -->
          <div class="paypal-card-header row items-center no-wrap q-pa-lg q-pb-md">
            <div class="paypal-icon-wrap q-mr-md">
              <q-icon name="payments" size="28px" color="white" />
            </div>
            <div class="col">
              <div class="text-subtitle1 text-weight-bold">PayPal</div>
              <div class="text-caption" style="opacity:.75">Natychmiastowe doładowanie · faktura i KSeF automatycznie</div>
            </div>
            <q-badge color="positive" class="q-ml-sm" style="font-size:.7rem;padding:4px 8px">
              Natychmiast
            </q-badge>
          </div>

          <q-separator />

          <div class="q-pa-lg">
            <!-- 1. Wybór pakietu -->
            <div class="text-overline text-grey-7 q-mb-sm">1. Wybierz pakiet</div>
            <div class="pkg-grid q-mb-md">
              <!-- Stałe pakiety -->
              <div
                v-for="pkg in fixedPackages"
                :key="pkg.pts"
                class="pkg-tile"
                :class="{ 'pkg-tile--active': selectedPkg.key === pkg.key }"
                @click="selectPackage(pkg)"
              >
                <div class="pkg-tile-pts">{{ pkg.pts }}</div>
                <div class="pkg-tile-sub">pkt</div>
                <div class="pkg-tile-price">{{ pkg.price }} PLN</div>
                <q-icon v-if="selectedPkg.key === pkg.key" name="check_circle" class="pkg-tile-check" size="16px" />
              </div>

              <!-- Kafelek: własna ilość -->
              <div
                class="pkg-tile pkg-tile--custom"
                :class="{ 'pkg-tile--active': selectedPkg.key === 'custom' }"
                @click="selectPackage(customPkg)"
              >
                <div class="pkg-tile-pts pkg-tile-pts--small">Inna</div>
                <div class="pkg-tile-sub">ilość</div>
                <div class="pkg-tile-price">1 pkt / PLN</div>
                <q-icon v-if="selectedPkg.key === 'custom'" name="check_circle" class="pkg-tile-check" size="16px" />
              </div>
            </div>

            <!-- Pole własnej ilości (widoczne gdy custom) -->
            <div v-if="selectedPkg.key === 'custom'" class="q-mb-md">
              <q-input
                v-model.number="customPoints"
                type="number"
                label="Liczba punktów"
                outlined dense
                :min="50" :max="9999"
                suffix="pkt"
                hint="min. 50 · max. 9999 · 1 pkt = 1 PLN"
                @update:model-value="onCustomPointsChange"
              />
            </div>

            <!-- 2. Podsumowanie wybranego pakietu -->
            <div class="pkg-summary q-mb-lg">
              <div class="row items-center justify-between">
                <div>
                  <span class="text-body2 text-weight-bold">{{ selectedPkg.pts }} punktów premium</span>
                  <span class="text-caption text-grey-6 q-ml-sm">
                    netto {{ netForPkg(selectedPkg.price) }} PLN + VAT 23%
                  </span>
                </div>
                <div class="text-h6 text-weight-bolder text-primary">
                  {{ selectedPkg.price }} PLN
                </div>
              </div>
            </div>

            <!-- 3. Przyciski PayPal -->
            <div class="text-overline text-grey-7 q-mb-sm">2. Zapłać przez PayPal</div>

            <!-- Brak konfiguracji Client ID -->
            <q-banner
              v-if="!paypalConfigured"
              dense
              class="bg-warning text-white rounded-borders q-mb-sm shadow-2"
            >
              <template v-slot:avatar>
                <q-icon name="warning" color="white" />
              </template>
              PayPal wymaga ustawienia <strong>PAYPAL_CLIENT_ID</strong> w konfiguracji aplikacji.
            </q-banner>

            <!-- Spinner inicjalizacji -->
            <div v-else-if="paypalLoading" class="text-center q-py-md">
              <q-spinner color="primary" size="2em" />
              <div class="text-caption text-grey-7 q-mt-sm">Inicjalizacja PayPal...</div>
            </div>

            <!-- Kontener przycisków PayPal — v-show: musi być w DOM gdy SDK renderuje -->
            <div v-else-if="!paypalError">
              <div id="paypal-button-container" />
            </div>

            <!-- Błąd ładowania SDK -->
            <div v-if="paypalError" class="paypal-error q-mt-sm">
              <q-icon name="error_outline" size="sm" color="negative" class="q-mr-xs" />
              <span class="text-caption text-negative">{{ paypalError }}</span>
              <q-btn
                flat dense no-caps size="sm" color="primary"
                label="Spróbuj ponownie"
                class="q-ml-sm"
                @click="initPaypal"
              />
            </div>

            <!-- Stopka informacyjna -->
            <div class="paypal-footer q-mt-md">
              <div class="row items-center q-gutter-x-sm text-caption text-grey-6">
                <q-icon name="verified_user" size="14px" color="positive" />
                <span>Faktura wystawiana automatycznie przez system</span>
              </div>
              <div class="row items-center q-gutter-x-sm text-caption text-grey-6 q-mt-xs">
                <q-icon name="receipt_long" size="14px" color="info" />
                <span>Zgłoszenie do KSeF i akceptacja przed udostępnieniem PDF</span>
              </div>
            </div>
          </div>
        </q-card>
      </div>

      <!-- ======= PRZELEW + BLIK (prawa kolumna) ======= -->
      <div class="col-12 col-lg-5">
        <div class="column q-col-gutter-lg">

          <!-- Przelew bankowy -->
          <div class="col">
            <q-card flat bordered class="q-pa-lg rounded-borders shadow-1">
              <div class="row items-center q-mb-md q-gutter-sm">
                <q-icon name="account_balance" color="primary" size="sm" />
                <div class="text-h6 text-weight-bold">Przelew bankowy</div>
              </div>
              <p class="text-caption text-grey-7 q-mb-md">Punkty dodawane ręcznie do 24h od zaksięgowania.</p>
              <div class="bank-details">
                <div class="bank-row">
                  <span class="bank-key">Odbiorca</span>
                  <span class="bank-val">EDS</span>
                </div>
                <div class="bank-row">
                  <span class="bank-key">Nr konta</span>
                  <span class="bank-val bank-val--accent">60 1240 3116 1111 0010 9288 1740</span>
                </div>
                <div class="bank-row">
                  <span class="bank-key">Tytułem</span>
                  <span class="bank-val">login: <em>twój_login</em>, premium_pkt: <em>ilość</em></span>
                </div>
              </div>
            </q-card>
          </div>

          <!-- BLIK na numer telefonu -->
          <div class="col">
            <q-card flat bordered class="q-pa-lg rounded-borders shadow-1">
              <div class="row items-center q-mb-md q-gutter-sm">
                <q-icon name="contactless" color="primary" size="sm" />
                <div class="text-h6 text-weight-bold">BLIK na numer telefonu</div>
              </div>
              <p class="text-caption text-grey-7 q-mb-md">Punkty dodawane ręcznie do 24h po potwierdzeniu.</p>
              <div class="bank-details">
                <div class="bank-row">
                  <span class="bank-key">Telefon</span>
                  <span class="bank-val bank-val--accent">+48 666 625 752</span>
                </div>
                <div class="bank-row">
                  <span class="bank-key">Tytułem</span>
                  <span class="bank-val">BLIK na telefon, login: <em>twój_login</em>, premium_pkt: <em>ilość</em></span>
                </div>
              </div>
            </q-card>
          </div>

        </div>
      </div>

    </div>

    <!-- ======= REALIZACJA KODU BONUSOWEGO ======= -->
    <div class="row q-mt-lg">
      <div class="col-12">
        <q-card flat bordered class="rounded-borders shadow-1 bg-blue-grey-1">
          <q-card-section class="row items-center q-gutter-md">
            <q-avatar icon="confirmation_number" color="primary" text-color="white" size="md" />
            <div class="col">
              <div class="text-subtitle1 text-weight-bold text-primary">Masz kod bonusowy?</div>
              <div class="text-caption text-grey-7">Wprowadź otrzymany kod, aby otrzymać darmowe punkty premium.</div>
            </div>
            <div class="col-12 col-sm-auto row q-gutter-sm items-center">
              <q-input
                v-model="bonusCode"
                label="Twój kod"
                outlined
                dense
                bg-color="white"
                style="min-width: 200px"
                @keyup.enter="redeemCode"
              />
              <q-btn
                label="Zrealizuj"
                color="primary"
                unelevated
                :loading="redeeming"
                @click="redeemCode"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useQuasar, useMeta } from 'quasar'

useMeta({
  title: 'Cennik i punkty | wyznaczresurs.com',
  meta: {
    description:   { name: 'description',       content: '100 punktów za obliczenie resursu UTB. Bez abonamentu — płacisz tylko za wyniki. Obsługujemy 22 typy urządzeń. Faktury VAT.' },
    ogTitle:       { property: 'og:title',       content: 'Cennik i punkty | wyznaczresurs.com' },
    ogDescription: { property: 'og:description', content: '100 punktów za obliczenie resursu UTB. Bez abonamentu — płacisz tylko za wyniki.' },
    ogUrl:         { property: 'og:url',         content: 'https://wyznaczresurs.com/pricing' },
    robots:        { name: 'robots',              content: 'index, follow' },
  },
  link: { canonical: { rel: 'canonical', href: 'https://wyznaczresurs.com/pricing' } },
})
import { api } from 'boot/axios'
import { useUserStore } from 'stores/user-store'
import PricingCards from 'components/shared/PricingCards.vue'

const $q = useQuasar()
const userStore = useUserStore()

// --- Kody bonusowe ---
const bonusCode = ref('')
const redeeming = ref(false)

const redeemCode = async () => {
  if (!bonusCode.value) return
  redeeming.value = true
  try {
    const res = await api.post('/billing/redeem-code/', { code: bonusCode.value })
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: res.data.detail,
      position: 'top'
    })
    bonusCode.value = ''
    await userStore.fetchUser()
  } catch (e) {
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: e.response?.data?.detail || 'Błąd podczas realizacji kodu.',
      position: 'top'
    })
  } finally {
    redeeming.value = false
  }
}

// ─── Dane statyczne ────────────────────────────────────────────────────────
const pointsSteps = [
  { num: '01', icon: 'person_add',             title: 'Załóż konto',   text: 'Rejestracja bezpłatna — bez karty.' },
  { num: '02', icon: 'account_balance_wallet', title: 'Kup punkty',    text: 'Przelew lub PayPal. 1 pkt ≈ 1 PLN.' },
  { num: '03', icon: 'calculate',              title: 'Oblicz resurs', text: '100 pkt za obliczenie. Wynik od razu.' },
  { num: '04', icon: 'picture_as_pdf',         title: 'Pobierz PDF',   text: 'Wyznaczenie resursu gotowe do złożenia w UDT.' }
]

// Stałe pakiety PayPal — zgodne z PAYPAL_PACKAGES w models.py
const fixedPackages = [
  { key: '100', pts: 100,  price: 100 },
  { key: '250', pts: 250,  price: 250 },
  { key: '500', pts: 500,  price: 500 },
  { key: '1000', pts: 1000, price: 1000 },
]

// ─── PayPal ────────────────────────────────────────────────────────────────

const paypalClientId = ref('')
const isSandbox      = ref(true)
const paypalConfigured = computed(() => !!paypalClientId.value && paypalClientId.value !== 'SANDBOX_CLIENT_ID_TUTAJ')

const customPoints  = ref(200)
const customPkg     = ref({ key: 'custom', pts: 200, price: 200 })
const selectedPkg   = ref(fixedPackages[0])
const paypalLoading = ref(false)
const paypalError   = ref('')

const netForPkg = (gross) => (gross / 1.23).toFixed(2)

const onCustomPointsChange = (val) => {
  const pts = Math.max(50, Math.min(9999, parseInt(val) || 50))
  customPkg.value = { key: 'custom', pts, price: pts }
  if (selectedPkg.value.key === 'custom') selectedPkg.value = customPkg.value
}

const selectPackage = (pkg) => {
  selectedPkg.value = pkg.key === 'custom' ? customPkg.value : pkg
}

const loadPaypalSdk = () => new Promise((resolve, reject) => {
  if (window.paypal) { resolve(); return }
  const script = document.createElement('script')
  // Dynamiczne ID pobrane z backendu
  script.src = `https://www.paypal.com/sdk/js?client-id=${paypalClientId.value}&currency=PLN`
  script.onload  = resolve
  script.onerror = () => reject(new Error('Nie udało się pobrać SDK PayPal. Sprawdź połączenie lub Client ID.'))
  document.head.appendChild(script)
})

const initPaypal = async () => {
  if (!paypalConfigured.value) return
  paypalLoading.value = true
  paypalError.value   = ''

  try {
    await loadPaypalSdk()
    paypalLoading.value = false
    await nextTick()  // poczekaj aż Vue wyrenderuje #paypal-button-container

    window.paypal.Buttons({
      style: { layout: 'vertical', color: 'blue', shape: 'rect', label: 'pay' },

      // createOrder czyta selectedPkg.value w momencie kliknięcia — zawsze aktualny pakiet
      createOrder: async () => {
        const pkg = selectedPkg.value
        const payload = pkg.key === 'custom'
          ? { package: 'custom', points: pkg.pts }
          : { package: pkg.key }
        const res = await api.post('/billing/paypal/create-order/', payload)
        return res.data.order_id
      },

      onApprove: async (data) => {
        try {
          const res = await api.post(`/billing/paypal/capture-order/${data.orderID}/`)
          const invoice = res.data.invoice
          await userStore.fetchUser()
          $q.notify({
            type:    'positive',
            icon:    'check_circle',
            timeout: 7000,
            position: 'top',
            message: `Dodano ${selectedPkg.value.pts} punktów premium!`,
            caption: `Faktura ${invoice.invoice_number} • status KSeF: ${invoice.ksef_status}`,
          })
        } catch (e) {
          $q.notify({
            type:    'negative',
            icon:    'error',
            position: 'top',
            message: e.response?.data?.detail || 'Błąd podczas finalizacji płatności.'
          })
        }
      },

      onCancel: () => {
        $q.notify({ type: 'info', icon: 'info', message: 'Płatność anulowana.', position: 'top' })
      },

      onError: (err) => {
        paypalError.value = `Błąd PayPal: ${err?.message || 'Nieznany błąd'}`
      },
    }).render('#paypal-button-container')

  } catch (e) {
    paypalLoading.value = false
    paypalError.value   = e.message || 'Nie udało się załadować PayPal.'
  }
}

const fetchPaypalConfig = async () => {
  try {
    const res = await api.get('/billing/public-config/')
    paypalClientId.value = res.data.paypal_client_id
    isSandbox.value      = res.data.is_sandbox
    if (userStore.isLoggedIn) initPaypal()
  } catch (e) {
    console.error('Błąd pobierania konfiguracji PayPal:', e)
  }
}

onMounted(() => {
  fetchPaypalConfig()
})
</script>

<style scoped lang="scss">
@use "sass:color";

// ── Landing ──────────────────────────────────────────────────────────────────
.lc { max-width: 1200px; }
.eyebrow {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase; color: $primary; margin-bottom: 10px;
}
.section-h2 { font-size: 2rem; font-weight: 800; line-height: 1.15; margin: 0 0 16px; }
.pricing-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(145deg, $primary 0%, color.adjust($primary, $lightness: -24%) 100%);
  padding: 72px 0 64px;
}
.ph-bg { position: absolute; inset: 0; pointer-events: none; svg { width: 100%; height: 100%; } }
.norm-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.norm-chip {
  font-family: 'Roboto Mono', monospace; font-size: 0.65rem; font-weight: 600;
  letter-spacing: 0.08em; padding: 3px 10px;
  border: 1px solid rgba(white, 0.35); border-radius: 3px;
  color: rgba(white, 0.8); background: rgba(white, 0.07);
}
.page-h1 {
  font-size: clamp(2rem, 4vw, 3rem); font-weight: 900;
  letter-spacing: -0.02em; margin: 0 0 16px; line-height: 1.05;
}
.page-sub { font-size: 1.05rem; line-height: 1.6; opacity: 0.65; margin: 0; }
.points-section { background: #F4F7FA; .body--dark & { background: #151f2d; } }
.pts-card { padding-top: 24px; border-top: 2px solid rgba($primary, 0.15); }
.pts-num {
  font-family: 'Roboto Mono', monospace; font-size: 2.2rem; font-weight: 900;
  color: $primary; opacity: 0.25; line-height: 1; margin-bottom: 12px;
}
.pts-title { font-size: 0.95rem; font-weight: 700; margin-bottom: 8px; }
.pts-text  { font-size: 0.85rem; color: #607080; line-height: 1.55; .body--dark & { color: rgba(white, 0.5); } }
.pay-card {
  padding: 28px; border: 1px solid rgba(black, 0.08); border-radius: 8px;
  background: white; height: 100%;
  .body--dark & { background: #1e2a38; border-color: rgba(white, 0.08); }
}
.pay-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
.pay-card-title  { font-size: 1rem; font-weight: 700; }
.pricing-cta     { background: #0A1929; padding: 72px 0; }

// ── Wspólne (landing + dashboard) ────────────────────────────────────────────
.bank-details {
  background: #F4F7FA; border-radius: 6px; padding: 16px; margin-bottom: 4px;
  .body--dark & { background: #151f2d; }
}
.bank-row { display: flex; gap: 12px; margin-bottom: 8px; &:last-child { margin-bottom: 0; } }
.bank-key { font-size: 0.78rem; font-weight: 600; color: #8a9bb0; min-width: 72px; padding-top: 1px; }
.bank-val { font-size: 0.85rem; flex: 1; em { color: $primary; font-style: normal; } }
.bank-val--accent { font-family: 'Roboto Mono', monospace; font-weight: 700; color: $primary; font-size: 0.82rem; }
.pay-note { font-size: 0.78rem; color: #8a9bb0; margin: 0; }
.pts-badges { display: flex; gap: 10px; flex-wrap: wrap; }
.pts-pkg {
  border: 1px solid rgba($primary, 0.25); border-radius: 6px;
  padding: 10px 16px; text-align: center; min-width: 72px;
  .body--dark & { border-color: rgba($primary, 0.35); }
}
.pts-pkg-num   { font-family: 'Roboto Mono', monospace; font-size: 1.2rem; font-weight: 800; color: $primary; line-height: 1; }
.pts-pkg-label { font-size: 0.68rem; color: #8a9bb0; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
.pts-pkg-price { font-size: 0.78rem; font-weight: 600; color: #607080; .body--dark & { color: rgba(white, 0.5); } }

// ── Dashboard PayPal card ─────────────────────────────────────────────────────
.paypal-main-card {
  border-color: rgba($primary, 0.3) !important;
  .body--dark & { border-color: rgba($primary, 0.4) !important; }
}

.paypal-card-header {
  background: linear-gradient(135deg, $primary 0%, color.adjust($primary, $lightness: -12%) 100%);
  color: white;
  border-radius: 7px 7px 0 0;
}

.paypal-icon-wrap {
  width: 48px; height: 48px;
  background: rgba(white, 0.15);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

// Siatka pakietów
.pkg-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  @media (max-width: 480px) { grid-template-columns: repeat(2, 1fr); }
}

.pkg-tile {
  position: relative;
  border: 2px solid rgba($primary, 0.2);
  border-radius: 8px;
  padding: 14px 8px 12px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
  user-select: none;
  background: white;
  .body--dark & { background: #1a2535; border-color: rgba($primary, 0.25); }

  &:hover {
    border-color: $primary;
    box-shadow: 0 2px 12px rgba($primary, 0.15);
  }

  &--active {
    border-color: $primary;
    background: rgba($primary, 0.05);
    box-shadow: 0 2px 16px rgba($primary, 0.18);
    .body--dark & { background: rgba($primary, 0.1); }
  }
}

.pkg-tile-pts {
  font-family: 'Roboto Mono', monospace;
  font-size: 1.5rem; font-weight: 900;
  color: $primary; line-height: 1;
  &--small { font-size: 1rem; }
}
.pkg-tile--custom { border-style: dashed; }
.pkg-tile-sub {
  font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.12em; color: #8a9bb0; margin-bottom: 6px;
}
.pkg-tile-price {
  font-size: 0.82rem; font-weight: 700;
  color: #444;
  .body--dark & { color: rgba(white, 0.75); }
}
.pkg-tile-check {
  position: absolute; top: 6px; right: 6px;
  color: $positive;
}

// Podsumowanie wybranego
.pkg-summary {
  background: #F4F7FA;
  border-radius: 8px; padding: 14px 16px;
  border-left: 3px solid $primary;
  .body--dark & { background: #151f2d; }
}

// Błąd PayPal
.paypal-error {
  display: flex; align-items: center;
  background: rgba($negative, 0.06);
  border-radius: 6px; padding: 10px 12px;
  .body--dark & { background: rgba($negative, 0.1); }
}

// Stopka
.paypal-footer { border-top: 1px solid rgba(black, 0.07); padding-top: 12px; }
.body--dark .paypal-footer { border-color: rgba(white, 0.08); }
</style>
