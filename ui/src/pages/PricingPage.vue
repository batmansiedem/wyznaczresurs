<template>
  <!-- ===== LANDING VERSION ===== -->
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
          <span class="norm-chip">80 pkt / obliczenie</span>
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
          <div class="col-12 col-md-6">
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
          <div class="col-12 col-md-6">
            <div class="pay-card">
              <div class="pay-card-header">
                <q-icon name="payments" size="22px" color="primary" />
                <span class="pay-card-title">PayPal — automatyczne doładowanie</span>
              </div>
              <p class="text-grey-7 text-body2 q-mb-lg">Punkty pojawiają się na koncie natychmiast po płatności. Pakiety:</p>
              <div class="pts-badges">
                <div v-for="pkg in packages" :key="pkg.pts" class="pts-pkg">
                  <div class="pts-pkg-num">{{ pkg.pts }}</div>
                  <div class="pts-pkg-label">pkt</div>
                  <div class="pts-pkg-price">{{ pkg.price }} PLN</div>
                </div>
              </div>
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

  <!-- ===== DASHBOARD VERSION ===== -->
  <q-page v-else padding>
    <div class="calc-page-header q-mb-xl">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Cennik i punkty</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">80 punktów za jedno obliczenie resursu · 1 pkt ≈ 1 PLN brutto</p>
    </div>

    <PricingCards />

    <q-separator class="q-my-xl" />
    <div class="section-label q-mb-lg">Metody doładowania konta</div>
    <div class="row q-col-gutter-lg">
      <div class="col-12 col-md-6">
        <q-card flat bordered class="q-pa-lg">
          <div class="row items-center q-mb-md q-gutter-sm">
            <q-icon name="account_balance" color="primary" size="sm" />
            <div class="text-h6 text-weight-bold">Przelew bankowy</div>
          </div>
          <div class="bank-details">
            <div class="bank-row"><span class="bank-key">Odbiorca</span><span class="bank-val">EDS</span></div>
            <div class="bank-row"><span class="bank-key">Nr konta</span><span class="bank-val bank-val--accent">60 1240 3116 1111 0010 9288 1740</span></div>
            <div class="bank-row"><span class="bank-key">Tytułem</span><span class="bank-val">login: <em>twój_login</em>, premium_pkt: <em>ilość</em></span></div>
          </div>
          <p class="pay-note q-mt-md">* Punkty dodawane do 24h od zaksięgowania przelewu.</p>
        </q-card>
      </div>
      <div class="col-12 col-md-6">
        <q-card flat bordered class="q-pa-lg">
          <div class="row items-center q-mb-md q-gutter-sm">
            <q-icon name="payments" color="primary" size="sm" />
            <div class="text-h6 text-weight-bold">PayPal</div>
          </div>
          <p class="text-grey-7 text-body2 q-mb-md">Natychmiastowe doładowanie. Pakiety punktów:</p>
          <div class="pts-badges">
            <div v-for="pkg in packages" :key="pkg.pts" class="pts-pkg">
              <div class="pts-pkg-num">{{ pkg.pts }}</div>
              <div class="pts-pkg-label">pkt</div>
              <div class="pts-pkg-price">{{ pkg.price }} PLN</div>
            </div>
          </div>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { useUserStore } from 'stores/user-store'
import PricingCards from 'components/shared/PricingCards.vue'
const userStore = useUserStore()

const pointsSteps = [
  { num: '01', icon: 'person_add',              title: 'Załóż konto',        text: 'Rejestracja bezpłatna — bez karty.' },
  { num: '02', icon: 'account_balance_wallet',  title: 'Kup punkty',         text: 'Przelew lub PayPal. 1 pkt ≈ 1 PLN.' },
  { num: '03', icon: 'calculate',               title: 'Oblicz resurs',       text: '80 pkt za obliczenie. Wynik od razu.' },
  { num: '04', icon: 'picture_as_pdf',          title: 'Pobierz PDF',         text: 'Orzeczenie gotowe do złożenia w UDT.' }
]

const packages = [
  { pts: 100, price: 100 },
  { pts: 250, price: 230 },
  { pts: 500, price: 440 },
  { pts: 1000, price: 800 }
]
</script>

<style scoped lang="scss">
@use "sass:color";

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
.pts-num { font-family: 'Roboto Mono', monospace; font-size: 2.2rem; font-weight: 900; color: $primary; opacity: 0.25; line-height: 1; margin-bottom: 12px; }
.pts-title { font-size: 0.95rem; font-weight: 700; margin-bottom: 8px; }
.pts-text { font-size: 0.85rem; color: #607080; line-height: 1.55; .body--dark & { color: rgba(white, 0.5); } }
.pay-card {
  padding: 28px; border: 1px solid rgba(black, 0.08); border-radius: 8px; background: white; height: 100%;
  .body--dark & { background: #1e2a38; border-color: rgba(white, 0.08); }
}
.pay-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
.pay-card-title { font-size: 1rem; font-weight: 700; }
.bank-details {
  background: #F4F7FA; border-radius: 6px; padding: 16px; margin-bottom: 14px;
  .body--dark & { background: #151f2d; }
}
.bank-row { display: flex; gap: 12px; margin-bottom: 8px; &:last-child { margin-bottom: 0; } }
.bank-key { font-size: 0.78rem; font-weight: 600; color: #8a9bb0; min-width: 72px; padding-top: 1px; }
.bank-val { font-size: 0.85rem; flex: 1; em { color: $primary; font-style: normal; } }
.bank-val--accent { font-family: 'Roboto Mono', monospace; font-weight: 700; color: $primary; font-size: 0.82rem; }
.pay-note { font-size: 0.78rem; color: #8a9bb0; margin: 0; }
.pts-badges { display: flex; gap: 10px; flex-wrap: wrap; }
.pts-pkg {
  border: 1px solid rgba($primary, 0.25); border-radius: 6px; padding: 10px 16px; text-align: center; min-width: 72px;
  .body--dark & { border-color: rgba($primary, 0.35); }
}
.pts-pkg-num { font-family: 'Roboto Mono', monospace; font-size: 1.2rem; font-weight: 800; color: $primary; line-height: 1; }
.pts-pkg-label { font-size: 0.68rem; color: #8a9bb0; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
.pts-pkg-price { font-size: 0.78rem; font-weight: 600; color: #607080; .body--dark & { color: rgba(white, 0.5); } }
.pricing-cta { background: #0A1929; padding: 72px 0; }
</style>
