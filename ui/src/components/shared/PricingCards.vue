<template>
  <div class="row q-col-gutter-lg justify-center">

    <div class="col-12 col-sm-6 col-md-4">
      <q-card flat bordered class="pc column full-height">
        <q-card-section class="col q-pa-xl">
          <div class="pricing-label">STANDARD</div>
          <div class="pricing-price">100 <span class="pricing-unit">PLN brutto</span></div>
          <div class="text-grey-7 text-body2 q-mb-lg">Resurs jednego urządzenia</div>
          <q-separator class="q-mb-lg" />
          <q-list dense>
            <q-item v-for="f in standardFeatures" :key="f" class="q-px-none">
              <q-item-section avatar style="min-width:28px">
                <q-icon name="check" color="positive" size="xs" />
              </q-item-section>
              <q-item-section class="text-body2">{{ f }}</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-actions class="q-pa-lg q-pt-none">
          <q-btn unelevated color="primary" label="Kup punkty" to="/pricing" class="full-width" />
        </q-card-actions>
      </q-card>
    </div>

    <div class="col-12 col-sm-6 col-md-4">
      <q-card flat class="pc pc--featured column full-height">
        <div class="pc-badge">POLECANE</div>
        <q-card-section class="col q-pa-xl">
          <div class="pricing-label">PREMIUM</div>
          <div class="pricing-price">Indywidualnie</div>
          <div class="text-grey-7 text-body2 q-mb-lg">Flota urządzeń / firma</div>
          <q-separator class="q-mb-lg" />
          <q-list dense>
            <q-item v-for="f in premiumFeatures" :key="f" class="q-px-none">
              <q-item-section avatar style="min-width:28px">
                <q-icon name="check" color="positive" size="xs" />
              </q-item-section>
              <q-item-section class="text-body2">{{ f }}</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-actions class="q-pa-lg q-pt-none">
          <q-btn unelevated color="primary" label="Zapytaj o wycenę"
            to="/contact" class="full-width text-weight-bold" />
        </q-card-actions>
      </q-card>
    </div>

    <div class="col-12 col-sm-6 col-md-4">
      <q-card flat bordered class="pc column full-height">
        <q-card-section class="col q-pa-xl">
          <div class="pricing-label">EXPRESS</div>
          <div class="pricing-price">250 <span class="pricing-unit">PLN brutto</span></div>
          <div class="text-grey-7 text-body2 q-mb-lg">Pomoc techniczna na telefon</div>
          <q-separator class="q-mb-lg" />
          <p class="text-grey-7 text-body2 q-mb-none">
            Potrzebujesz wyniku natychmiast? Zadzwoń — przeprowadzimy przez
            obliczenia lub wykonamy je za Ciebie.
          </p>
        </q-card-section>
        <q-card-actions class="q-pa-lg q-pt-none">
          <q-btn flat color="primary" icon="phone" label="+48 666 625 752"
            class="full-width text-weight-bold" href="tel:+48666625752" />
        </q-card-actions>
      </q-card>
    </div>

  </div>
</template>

<script setup>
const standardFeatures = [
  'Kalkulator zgodny z FEM 9.511 / ISO 4301',
  'Archiwizacja wyników w chmurze',
  'Edycja i aktualizacja zapisanych wyników',
  'Wyznaczenie resursu PDF z tabelami i wykresem'
]
const premiumFeatures = [
  'Priorytetowe wsparcie techniczne',
  'Personalizacja obliczeń (logo firmy)',
  'Historia zakupów i rozliczeń',
  'Nielimitowana liczba urządzeń'
]
</script>

<style scoped lang="scss">
.pc {
  border-radius: 8px;
  transition: box-shadow 0.2s;
  &:hover { box-shadow: 0 6px 24px rgba(black, 0.08); }
}
.pc--featured {
  border: 2px solid $primary !important;
  position: relative;
}
.pc-badge {
  position: absolute;
  top: -13px; left: 50%;
  transform: translateX(-50%);
  background: $primary; color: white;
  font-size: 0.62rem; font-weight: 700;
  letter-spacing: 0.15em;
  padding: 4px 14px; border-radius: 20px;
}
.pricing-label {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.15em; color: $primary; margin-bottom: 10px;
}
.pricing-price {
  font-size: 2rem; font-weight: 800; margin-bottom: 4px; line-height: 1.1;
}
.pricing-unit {
  font-size: 0.85rem; font-weight: 400; color: #8a9bb0;
}
</style>
