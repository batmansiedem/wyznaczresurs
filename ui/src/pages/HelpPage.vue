<template>
  <!-- ===== LANDING VERSION ===== -->
  <q-page v-if="!userStore.isLoggedIn" class="lp">

    <section class="help-hero text-white">
      <div class="hh-bg" aria-hidden="true">
        <svg viewBox="0 0 1200 300" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="hh-m" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M20 0L0 0 0 20" fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.12"/>
            </pattern>
            <pattern id="hh-M" width="100" height="100" patternUnits="userSpaceOnUse">
              <rect width="100" height="100" fill="url(#hh-m)"/>
              <path d="M100 0L0 0 0 100" fill="none" stroke="white" stroke-width="0.6" stroke-opacity="0.18"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#hh-M)"/>
          <g transform="translate(1100, 150)" stroke="white" fill="none" stroke-opacity="0.14">
            <circle r="190" stroke-width="0.5"/><circle r="140" stroke-width="0.7"/>
            <circle r="90" stroke-width="0.5"/>
            <line x1="-210" x2="210" y1="0" y2="0" stroke-width="0.5"/>
            <line x1="0" x2="0" y1="-210" y2="210" stroke-width="0.5"/>
            <circle r="4" fill="white" stroke="none" fill-opacity="0.2"/>
          </g>
        </svg>
      </div>
      <div class="lc q-mx-auto q-px-md" style="position:relative;z-index:1">
        <div class="eyebrow eyebrow--light q-mb-sm">Pomoc</div>
        <h1 class="page-h1">Centrum pomocy</h1>
        <p class="page-sub">Najczęstsze pytania, instrukcje i dokumentacja techniczna.</p>
      </div>
    </section>

    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="row q-col-gutter-xl">
          <div class="col-12 col-md-8">
            <div class="eyebrow q-mb-lg">Najczęstsze pytania</div>
            <FaqList />
          </div>
          <div class="col-12 col-md-4">
            <div class="eyebrow q-mb-lg">Instruktaż</div>
            <q-card flat bordered class="q-mb-lg overflow-hidden">
              <q-card-section class="q-pa-none">
                <q-video :ratio="16/9" src="https://www.youtube.com/embed/11XT8J1bP9E" />
              </q-card-section>
              <q-card-section>
                <div class="text-subtitle2 text-weight-bold q-mb-xs">Jak korzystać z serwisu?</div>
                <p class="text-caption text-grey-7 q-mb-none">Krótki film z instrukcją obliczania resursu krok po kroku.</p>
              </q-card-section>
            </q-card>
            <div class="help-cta-box">
              <q-icon name="support_agent" size="28px" color="primary" class="q-mb-sm" />
              <div class="text-weight-bold q-mb-xs">Potrzebujesz pomocy?</div>
              <p class="text-grey-7 text-body2 q-mb-md">Pon–Pt&nbsp;8:00–17:00<br>+48 666 625 752</p>
              <q-btn unelevated color="primary" label="Napisz do nas" to="/contact" class="full-width" />
            </div>
          </div>
        </div>
      </div>
    </section>

  </q-page>

  <!-- ===== DASHBOARD VERSION ===== -->
  <q-page v-else padding>
    <div class="calc-page-header q-mb-xl">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Centrum pomocy</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">Najczęstsze pytania i instrukcje</p>
    </div>
    <div class="row q-col-gutter-xl">
      <div class="col-12 col-md-8">
        <FaqList />
      </div>
      <div class="col-12 col-md-4">
        <q-card flat bordered class="q-mb-lg overflow-hidden">
          <q-card-section class="q-pa-none">
            <q-video :ratio="16/9" src="https://www.youtube.com/embed/11XT8J1bP9E" />
          </q-card-section>
          <q-card-section>
            <div class="text-subtitle2 text-weight-bold">Jak korzystać z serwisu?</div>
          </q-card-section>
        </q-card>
        <q-card flat bordered>
          <q-card-section>
            <div class="text-h6 text-weight-bold text-primary q-mb-sm">Potrzebujesz pomocy?</div>
            <p class="text-grey-7 q-mb-md">Zespół techniczny dostępny Pon–Pt 8:00–17:00.</p>
            <q-btn unelevated color="primary" label="Skontaktuj się" to="/contact" class="full-width" />
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { useUserStore } from 'stores/user-store'
import { useMeta } from 'quasar'
import FaqList from 'components/shared/FaqList.vue'

useMeta({
  title: 'Pomoc i FAQ | wyznaczresurs.com',
  meta: {
    description:   { name: 'description',       content: 'Odpowiedzi na najczęściej zadawane pytania dotyczące kalkulatora resursu UTB, metodologii FEM 9.511 / ISO 4301 oraz systemu punktów.' },
    ogTitle:       { property: 'og:title',       content: 'Pomoc i FAQ | wyznaczresurs.com' },
    ogDescription: { property: 'og:description', content: 'FAQ: obliczenia resursu UTB, metodologia FEM 9.511 / ISO 4301, system punktów, generowanie raportów PDF.' },
    ogUrl:         { property: 'og:url',         content: 'https://wyznaczresurs.com/help' },
    robots:        { name: 'robots',              content: 'index, follow' },
  },
  link: { canonical: { rel: 'canonical', href: 'https://wyznaczresurs.com/help' } },
})

const userStore = useUserStore()
</script>

<style scoped lang="scss">
@use "sass:color";

.lc { max-width: 1200px; }
.eyebrow {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase; color: $primary;
}
.eyebrow--light { color: rgba(white, 0.45); }
.help-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(145deg, $primary 0%, color.adjust($primary, $lightness: -24%) 100%);
  padding: 64px 0 56px;
}
.hh-bg { position: absolute; inset: 0; pointer-events: none; svg { width: 100%; height: 100%; } }
.page-h1 {
  font-size: clamp(1.8rem, 3.5vw, 2.8rem); font-weight: 900;
  letter-spacing: -0.02em; margin: 0 0 14px; line-height: 1.05;
}
.page-sub { font-size: 1rem; opacity: 0.65; margin: 0; line-height: 1.6; }
.help-cta-box {
  padding: 24px; border: 1px solid rgba(black, 0.08); border-radius: 8px;
  text-align: center; background: white;
  .body--dark & { background: #1e2a38; border-color: rgba(white, 0.08); }
}
</style>
