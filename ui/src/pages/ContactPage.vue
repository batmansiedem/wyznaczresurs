<template>
  <!-- ===== LANDING VERSION ===== -->
  <q-page v-if="!userStore.isLoggedIn" class="lp">

    <section class="contact-hero text-white">
      <div class="ch-bg" aria-hidden="true">
        <svg viewBox="0 0 1200 300" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="ch-m" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M20 0L0 0 0 20" fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.12"/>
            </pattern>
            <pattern id="ch-M" width="100" height="100" patternUnits="userSpaceOnUse">
              <rect width="100" height="100" fill="url(#ch-m)"/>
              <path d="M100 0L0 0 0 100" fill="none" stroke="white" stroke-width="0.6" stroke-opacity="0.18"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#ch-M)"/>
          <g transform="translate(1130, 150)" stroke="white" fill="none" stroke-opacity="0.14">
            <circle r="200" stroke-width="0.5"/><circle r="150" stroke-width="0.7"/>
            <circle r="100" stroke-width="0.5"/>
            <line x1="-220" x2="220" y1="0"    y2="0"   stroke-width="0.5"/>
            <line x1="0"    x2="0"   y1="-220" y2="220" stroke-width="0.5"/>
            <circle r="4" fill="white" stroke="none" fill-opacity="0.2"/>
          </g>
        </svg>
      </div>
      <div class="lc q-mx-auto q-px-md" style="position:relative;z-index:1">
        <div class="eyebrow eyebrow--light q-mb-sm">Kontakt</div>
        <h1 class="page-h1">Skontaktuj się z nami</h1>
        <p class="page-sub">Odpowiadamy w ciągu 24 godzin. Pon–Pt 8:00–17:00.</p>
      </div>
    </section>

    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="row q-col-gutter-xl">
          <div class="col-12 col-md-4">
            <div class="eyebrow q-mb-md">Dane kontaktowe</div>
            <div class="contact-cards">
              <div v-for="item in contactItems" :key="item.icon" class="contact-info-card">
                <div class="cic-icon"><q-icon :name="item.icon" size="20px" color="primary" /></div>
                <div>
                  <div class="cic-label">{{ item.label }}</div>
                  <div class="cic-value">{{ item.value }}</div>
                  <div v-if="item.note" class="cic-note">{{ item.note }}</div>
                </div>
              </div>
            </div>
            <div class="eyebrow q-mt-xl q-mb-md">Tematy zapytań</div>
            <div class="topic-tags">
              <div v-for="t in subjects" :key="t" class="topic-tag">{{ t }}</div>
            </div>
            <div class="social-row q-mt-xl">
              <q-btn flat round dense icon="facebook" color="primary" size="md"
                href="https://www.facebook.com/Wyznacz-resurs-107911734048291/" target="_blank" />
              <q-btn flat round dense icon="smart_display" color="primary" size="md"
                href="https://www.youtube.com/channel/UC-fqGlD3TSgE" target="_blank" />
            </div>
          </div>
          <div class="col-12 col-md-8">
            <div class="eyebrow q-mb-md">Formularz kontaktowy</div>
            <div class="contact-form-wrap">
              <q-form @submit="onSubmit">
                <div class="row q-col-gutter-md">
                  <div class="col-12 col-sm-7"><q-input v-model="form.name" label="Imię i nazwisko / Nazwa firmy" outlined :rules="[v => !!v || 'Wymagane']" /></div>
                  <div class="col-12 col-sm-5"><q-input v-model="form.phone" label="Telefon" outlined /></div>
                  <div class="col-12"><q-input v-model="form.email" label="Adres e-mail" type="email" outlined :rules="[v => !!v || 'Wymagane']" /></div>
                  <div class="col-12"><q-select v-model="form.subject" :options="subjects" label="Temat" outlined /></div>
                  <div class="col-12"><q-input v-model="form.message" label="Treść wiadomości" type="textarea" outlined rows="6" :rules="[v => !!v || 'Wymagane']" /></div>
                  <div class="col-12"><q-btn type="submit" color="primary" label="Wyślij wiadomość" icon-right="send" size="lg" unelevated :loading="loading" class="text-weight-bold" /></div>
                </div>
              </q-form>
            </div>
          </div>
        </div>
      </div>
    </section>

  </q-page>

  <!-- ===== DASHBOARD VERSION ===== -->
  <q-page v-else padding>
    <div class="calc-page-header q-mb-xl">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">Kontakt</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">Odpowiemy na Twoje pytania w ciągu 24h</p>
    </div>
    <div class="row q-col-gutter-xl">
      <div class="col-12 col-md-8">
        <div class="section-label q-mb-md">Formularz kontaktowy</div>
        <q-card flat bordered class="q-pa-lg">
          <q-form @submit="onSubmit">
            <div class="row q-col-gutter-md">
              <div class="col-12"><q-input v-model="form.name" label="Imię i nazwisko / Nazwa firmy" outlined :rules="[v => !!v || 'Wymagane']" /></div>
              <div class="col-12 col-sm-6"><q-input v-model="form.email" label="Adres e-mail" type="email" outlined :rules="[v => !!v || 'Wymagane']" /></div>
              <div class="col-12 col-sm-6"><q-input v-model="form.phone" label="Telefon" outlined /></div>
              <div class="col-12"><q-select v-model="form.subject" :options="subjects" label="Temat wiadomości" outlined /></div>
              <div class="col-12"><q-input v-model="form.message" label="Treść wiadomości" type="textarea" outlined rows="6" :rules="[v => !!v || 'Wymagane']" /></div>
              <div class="col-12"><q-btn type="submit" color="primary" label="Wyślij wiadomość" icon-right="send" size="lg" unelevated :loading="loading" /></div>
            </div>
          </q-form>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <div class="section-label q-mb-md">Dane kontaktowe</div>
        <q-card flat bordered class="q-pa-lg">
          <q-list>
            <q-item v-for="item in contactItems" :key="item.icon" class="q-px-none q-py-md">
              <q-item-section avatar>
                <div class="cic-icon"><q-icon :name="item.icon" size="20px" color="primary" /></div>
              </q-item-section>
              <q-item-section>
                <q-item-label caption class="cic-label">{{ item.label }}</q-item-label>
                <q-item-label class="text-weight-medium">{{ item.value }}</q-item-label>
                <q-item-label v-if="item.note" caption>{{ item.note }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from 'stores/user-store'
import { api } from 'boot/axios'
import { Notify, useMeta } from 'quasar'

useMeta({
  title: 'Kontakt | wyznaczresurs.com',
  meta: {
    description:   { name: 'description',       content: 'Skontaktuj się z nami w sprawie obliczeń resursu UTB, metodologii FEM 9.511 / ISO 4301 lub wsparcia technicznego.' },
    ogTitle:       { property: 'og:title',       content: 'Kontakt | wyznaczresurs.com' },
    ogDescription: { property: 'og:description', content: 'Formularz kontaktowy — pomoc techniczna, pytania o obliczenia resursu UTB.' },
    ogUrl:         { property: 'og:url',         content: 'https://wyznaczresurs.com/contact' },
    robots:        { name: 'robots',              content: 'index, follow' },
  },
  link: { canonical: { rel: 'canonical', href: 'https://wyznaczresurs.com/contact' } },
})

const userStore = useUserStore()
const loading = ref(false)
const form = ref({ name: '', email: '', phone: '', subject: 'Zapytanie o ofertę', message: '' })

const subjects = ['Zapytanie o ofertę', 'Problem techniczny', 'Punkty premium', 'Błąd w obliczeniach', 'Inny']

const contactItems = [
  { icon: 'email',    label: 'E-mail',       value: 'info@wyznaczresurs.com' },
  { icon: 'phone',    label: 'Telefon',      value: '+48 666 625 752' },
  { icon: 'schedule', label: 'Godziny pracy',value: 'Poniedziałek – Piątek', note: '8:00 – 17:00' }
]

function prefillForm() {
  if (userStore.isLoggedIn && userStore.user) {
    const u = userStore.user
    form.value.name = u.company_name || `${u.first_name || ''} ${u.last_name || ''}`.trim()
    form.value.email = u.email || ''
    // Jeśli w modelu User nie ma telefonu, zostanie puste
    form.value.phone = u.phone || ''
  }
}

onMounted(() => {
  prefillForm()
})

const onSubmit = async () => {
  loading.value = true
  try {
    await api.post('/contacts/', form.value)
    Notify.create({ type: 'positive', message: 'Wiadomość wysłana!' })
    form.value = { name: '', email: '', phone: '', subject: 'Zapytanie o ofertę', message: '' }
  } catch {
    Notify.create({ type: 'negative', message: 'Nie udało się wysłać wiadomości.' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@use "sass:color";

.lc { max-width: 1200px; }
.eyebrow {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase; color: $primary;
}
.eyebrow--light { color: rgba(white, 0.45); }
.contact-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(145deg, $primary 0%, color.adjust($primary, $lightness: -24%) 100%);
  padding: 64px 0 56px;
}
.ch-bg { position: absolute; inset: 0; pointer-events: none; svg { width: 100%; height: 100%; } }
.page-h1 {
  font-size: clamp(1.8rem, 3.5vw, 2.8rem); font-weight: 900;
  letter-spacing: -0.02em; margin: 0 0 14px; line-height: 1.05;
}
.page-sub { font-size: 1rem; opacity: 0.65; margin: 0; line-height: 1.6; }
.contact-cards { display: flex; flex-direction: column; gap: 16px; }
.contact-info-card {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 16px; border: 1px solid rgba(black, 0.08); border-radius: 8px; background: white;
  .body--dark & { background: #1e2a38; border-color: rgba(white, 0.08); }
}
.cic-icon {
  width: 36px; height: 36px; border-radius: 8px; background: rgba($primary, 0.08);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.cic-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #8a9bb0; margin-bottom: 2px; }
.cic-value { font-size: 0.95rem; font-weight: 600; }
.cic-note { font-size: 0.82rem; color: #607080; .body--dark & { color: rgba(white, 0.45); } }
.topic-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.topic-tag {
  font-size: 0.78rem; padding: 4px 12px; border-radius: 4px;
  border: 1px solid rgba($primary, 0.2); color: $primary; background: rgba($primary, 0.05);
  .body--dark & { border-color: rgba($primary, 0.3); background: rgba($primary, 0.1); }
}
.social-row { display: flex; gap: 4px; }
.contact-form-wrap {
  padding: 32px; border: 1px solid rgba(black, 0.08); border-radius: 8px; background: white;
  .body--dark & { background: #1e2a38; border-color: rgba(white, 0.08); }
}
</style>

