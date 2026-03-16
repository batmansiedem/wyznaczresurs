<template>
  <q-page class="landing-page">

    <!-- ===== HERO ===== -->
    <section class="hero-section text-white">
      <div class="hero-tech-bg" aria-hidden="true">
        <svg viewBox="0 0 1200 520" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="h-minor" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M20 0L0 0 0 20" fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.15"/>
            </pattern>
            <pattern id="h-major" width="100" height="100" patternUnits="userSpaceOnUse">
              <rect width="100" height="100" fill="url(#h-minor)"/>
              <path d="M100 0L0 0 0 100" fill="none" stroke="white" stroke-width="0.6" stroke-opacity="0.2"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#h-major)"/>
          <g transform="translate(1060, 260)" stroke="white" fill="none" stroke-opacity="0.18">
            <circle r="240" stroke-width="0.5"/>
            <circle r="190" stroke-width="0.7"/>
            <circle r="140" stroke-width="0.5"/>
            <circle r="90"  stroke-width="0.9"/>
            <circle r="44"  stroke-width="0.6"/>
            <line x1="-260" x2="260" y1="0"    y2="0"   stroke-width="0.6"/>
            <line x1="0"    x2="0"   y1="-260" y2="260" stroke-width="0.6"/>
            <line x1="-169" y1="-169" x2="0" y2="0" stroke-width="0.3" stroke-dasharray="5 9"/>
            <line x1="169"  y1="-169" x2="0" y2="0" stroke-width="0.3" stroke-dasharray="5 9"/>
            <circle r="5" fill="white" stroke="none" fill-opacity="0.25"/>
            <line x1="-240" y1="-5" x2="-240" y2="5" stroke-width="1.2" stroke-opacity="0.35"/>
            <line x1="-190" y1="-4" x2="-190" y2="4" stroke-width="1"   stroke-opacity="0.35"/>
            <line x1="-140" y1="-5" x2="-140" y2="5" stroke-width="1.2" stroke-opacity="0.35"/>
            <line x1="-90"  y1="-4" x2="-90"  y2="4" stroke-width="1"   stroke-opacity="0.35"/>
          </g>
          <g transform="translate(40, 480)" stroke="white" fill="none" stroke-opacity="0.2">
            <path d="M0 -240 L0 0 L260 0" stroke-width="1.2"/>
            <line x1="0" y1="-18" x2="260" y2="-18" stroke-width="0.6" stroke-dasharray="7 5" stroke-opacity="0.15"/>
            <polygon points="0,-18 9,-24 9,-12"       fill="white" fill-opacity="0.2" stroke="none"/>
            <polygon points="260,-18 251,-24 251,-12" fill="white" fill-opacity="0.2" stroke="none"/>
            <line x1="-7" y1="-60"  x2="7" y2="-60"  stroke-width="1" stroke-opacity="0.3"/>
            <line x1="-7" y1="-120" x2="7" y2="-120" stroke-width="1" stroke-opacity="0.3"/>
            <line x1="-7" y1="-180" x2="7" y2="-180" stroke-width="1" stroke-opacity="0.3"/>
            <line x1="65"  y1="-7" x2="65"  y2="7" stroke-width="1" stroke-opacity="0.3"/>
            <line x1="130" y1="-7" x2="130" y2="7" stroke-width="1" stroke-opacity="0.3"/>
            <line x1="195" y1="-7" x2="195" y2="7" stroke-width="1" stroke-opacity="0.3"/>
          </g>
          <g stroke="white" fill="none" stroke-opacity="0.22">
            <circle cx="320" cy="80"  r="5"  stroke-width="1"/>
            <circle cx="320" cy="80"  r="14" stroke-width="0.5"/>
            <circle cx="600" cy="400" r="5"  stroke-width="1"/>
            <circle cx="600" cy="400" r="14" stroke-width="0.5"/>
            <circle cx="820" cy="120" r="5"  stroke-width="1"/>
            <circle cx="820" cy="120" r="14" stroke-width="0.5"/>
          </g>
        </svg>
      </div>

      <div class="lc q-mx-auto q-px-md" style="position:relative;z-index:1">
        <div class="row items-center q-col-gutter-xl">
          <div class="col-12 col-md-6">
            <div class="norm-chips q-mb-lg">
              <span class="norm-chip">FEM 9.511</span>
              <span class="norm-chip">ISO 4301</span>
              <span class="norm-chip">Rozp. MPiT 2018</span>
            </div>
            <h1 class="hero-h1">Kalkulator<br>Resursu UTB</h1>
            <p class="hero-sub">
              Wyznaczanie trwałości eksploatacyjnej urządzeń transportu bliskiego
              metodą cykli pracy — zgodnie z wymaganiami Urzędu Dozoru Technicznego.
            </p>
            <ul class="hero-spec-list q-mb-xl">
              <li>22 typy urządzeń: suwnicy, żurawie, podesty, wózki, układnice</li>
              <li>Metoda cykli pracy wg FEM 9.511 i normy ISO 4301</li>
              <li>Orzeczenie PDF akceptowane przez UDT</li>
              <li>Archiwizacja i aktualizacja wyników w kolejnych latach</li>
            </ul>
            <q-separator class="q-mb-lg"/>
            <div class="q-gutter-md row no-wrap items-center">
              <template v-if="userStore.isLoggedIn">
                <q-btn unelevated size="lg" color="white" text-color="primary"
                  label="Przejdź do pulpitu" to="/dashboard" class="text-weight-bold" />
              </template>
              <template v-else>
                <q-btn unelevated size="lg" color="white" text-color="primary"
                  label="Otwórz konto" to="/register" class="text-weight-bold" />
                <q-btn flat size="lg" color="white" label="Zaloguj się" to="/login" />
              </template>
            </div>
          </div>

          <div class="col-12 col-md-6 gt-sm flex flex-center">
            <svg viewBox="0 0 420 340" class="hero-illustration" xmlns="http://www.w3.org/2000/svg">
              <rect x="1" y="1" width="418" height="338" rx="4" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
              <rect x="10" y="10" width="400" height="320" rx="2" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
              <g stroke="rgba(255,255,255,0.07)" stroke-width="0.5">
                <line x1="10" x2="410" y1="90"  y2="90"/>
                <line x1="10" x2="410" y1="170" y2="170"/>
                <line x1="10" x2="410" y1="250" y2="250"/>
                <line x1="140" x2="140" y1="10" y2="330"/>
                <line x1="280" x2="280" y1="10" y2="330"/>
              </g>
              <g>
                <text x="8" y="88"  font-size="7" fill="rgba(255,255,255,0.4)" text-anchor="end">100%</text>
                <text x="8" y="168" font-size="7" fill="rgba(255,255,255,0.4)" text-anchor="end">50%</text>
                <text x="8" y="248" font-size="7" fill="rgba(255,255,255,0.4)" text-anchor="end">0%</text>
                <rect x="30"  y="150" width="36" height="100" rx="2" fill="rgba(255,255,255,0.55)"/>
                <rect x="30"  y="148" width="36" height="4"   rx="1" fill="rgba(255,255,255,0.9)"/>
                <text x="48"  y="265" font-size="7" fill="rgba(255,255,255,0.5)" text-anchor="middle">Podnoszenie</text>
                <rect x="80"  y="110" width="36" height="140" rx="2" fill="rgba(255,255,255,0.55)"/>
                <rect x="80"  y="108" width="36" height="4"   rx="1" fill="rgba(255,255,255,0.9)"/>
                <text x="98"  y="265" font-size="7" fill="rgba(255,255,255,0.5)" text-anchor="middle">Jazda</text>
                <rect x="130" y="175" width="36" height="75"  rx="2" fill="rgba(255,255,255,0.4)"/>
                <rect x="130" y="173" width="36" height="4"   rx="1" fill="rgba(255,255,255,0.7)"/>
                <text x="148" y="265" font-size="7" fill="rgba(255,255,255,0.5)" text-anchor="middle">Obrót</text>
              </g>
              <g transform="translate(290, 170)">
                <circle r="72" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="14"/>
                <circle r="72" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="14"
                  stroke-dasharray="306 200" stroke-dashoffset="56"
                  stroke-linecap="round" transform="rotate(-90)"/>
                <circle r="56" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
                <circle r="40" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
                <line x1="-82" x2="82" y1="0" y2="0" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
                <line x1="0" x2="0" y1="-82" y2="82" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
                <text y="-6"  font-size="20" font-weight="700" fill="white" text-anchor="middle">68%</text>
                <text y="12"  font-size="7.5" fill="rgba(255,255,255,0.55)" text-anchor="middle">RESURS</text>
                <text y="22"  font-size="7.5" fill="rgba(255,255,255,0.55)" text-anchor="middle">WYKORZ.</text>
              </g>
              <g fill="rgba(255,255,255,0.5)" font-size="8">
                <text x="210" y="78">Stan obciążenia: Q3</text>
                <text x="210" y="91">Klasa pracy: A6</text>
                <text x="210" y="104">Cykle: 48 320 / 71 000</text>
                <text x="210" y="117">F<tspan font-size="6" dy="2">X</tspan><tspan dy="-2"> = 1.35</tspan></text>
              </g>
              <text x="210" y="30" font-size="9" font-weight="600" fill="rgba(255,255,255,0.65)" text-anchor="middle">
                ANALIZA RESURSU — SUWNICA POMOSTOWA
              </text>
              <line x1="15" y1="38" x2="405" y2="38" stroke="rgba(255,255,255,0.12)" stroke-width="0.5"/>
            </svg>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== PASEK ZGODNOŚCI ===== -->
    <section class="compliance-strip">
      <div class="lc q-mx-auto q-px-md">
        <div class="row">
          <div v-for="spec in complianceSpecs" :key="spec.code" class="col-6 col-md-3 compliance-item">
            <div class="compliance-code">{{ spec.code }}</div>
            <div class="compliance-label">{{ spec.label }}</div>
            <div class="compliance-desc">{{ spec.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== METODOLOGIA OBLICZEŃ ===== -->
    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="text-center q-mb-xl">
          <div class="eyebrow">Algorytm obliczeń</div>
          <h2 class="section-h2">Metodologia zgodna z FEM 9.511</h2>
          <p class="section-sub">
            Obliczenia opierają się na ściśle zdefiniowanych wzorach norm europejskich.
            Żadnych przybliżeń — wyniki identyczne jak przy obliczeniach ręcznych.
          </p>
        </div>
        <div class="row q-col-gutter-lg">
          <div v-for="m in methodology" :key="m.step" class="col-12 col-md-4">
            <div class="method-card full-height">
              <div class="method-step">{{ m.step }}</div>
              <h3 class="method-title">{{ m.title }}</h3>
              <div class="method-formula">{{ m.formula }}</div>
              <p class="method-desc">{{ m.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== DZIENNIK EKSPLOATACJI ===== -->
    <section class="q-py-xl bg-primary text-white overflow-hidden relative-position">
      <div class="lc q-mx-auto q-px-md relative-position" style="z-index:2">
        <div class="row items-center q-col-gutter-xl">
          <div class="col-12 col-md-6">
            <div class="eyebrow eyebrow--light">Darmowe narzędzie</div>
            <h2 class="section-h2 text-white">Dziennik eksploatacji UTB</h2>
            <p class="section-sub text-white opacity-70 q-mb-xl">
              Pobierz bezpłatnie profesjonalnie przygotowany arkusz do rejestracji przebiegu eksploatacji. 
              Niezbędny dokument do poprawnego monitorowania resursu Twojego urządzenia.
            </p>
            <q-list class="q-mb-xl">
              <q-item class="q-px-none">
                <q-item-section avatar>
                  <q-icon name="check_circle" color="white" />
                </q-item-section>
                <q-item-section>Zgodny z wymaganiami Rozporządzenia MPiT</q-item-section>
              </q-item>
              <q-item class="q-px-none">
                <q-item-section avatar>
                  <q-icon name="check_circle" color="white" />
                </q-item-section>
                <q-item-section>Przejrzysty układ tabelaryczny</q-item-section>
              </q-item>
              <q-item class="q-px-none">
                <q-item-section avatar>
                  <q-icon name="check_circle" color="white" />
                </q-item-section>
                <q-item-section>Miejsce na dane eksploatującego i parametry pracy</q-item-section>
              </q-item>
            </q-list>
            <q-btn unelevated size="lg" color="white" text-color="primary" 
              label="Pobierz dziennik (PDF)" icon="picture_as_pdf" 
              @click="showLogbookDialog = true" class="text-weight-bold" />
          </div>
          <div class="col-12 col-md-6 flex flex-center">
            <div class="logbook-preview shadow-24">
              <div class="logbook-header">Dziennik Eksploatacji</div>
              <div class="logbook-lines">
                <div v-for="n in 12" :key="n" class="logbook-line"></div>
              </div>
              <div class="logbook-stamp">PDF</div>
            </div>
          </div>
        </div>
      </div>
      <!-- Dekoracja tła -->
      <q-icon name="menu_book" class="bg-icon-deco" />
    </section>

    <!-- ===== OBSŁUGIWANE URZĄDZENIA ===== -->
    <section class="devices-section q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="row q-col-gutter-xl items-start">
          <div class="col-12 col-md-4">
            <div class="eyebrow">Zakres obliczeń</div>
            <h2 class="section-h2">22 typy urządzeń UTB</h2>
            <p class="text-grey-7 q-mb-lg">
              Każdy kalkulator uwzględnia specyfikę danego urządzenia:
              sposób rejestracji eksploatacji, współczynniki normowe
              oraz wymagania UDT dotyczące resursu.
            </p>
            <q-btn unelevated color="primary" label="Zobacz kalkulatory"
              :to="userStore.isLoggedIn ? '/calculators' : '/register'" class="text-weight-bold" />
          </div>
          <div class="col-12 col-md-8">
            <div class="devices-group q-mb-md">
              <div class="devices-group-label">Urządzenia dźwignicowe</div>
              <div class="devices-grid">
                <div v-for="d in devicesHoisting" :key="d" class="device-tag">{{ d }}</div>
              </div>
            </div>
            <div class="devices-group q-mb-md">
              <div class="devices-group-label">Urządzenia transportowe</div>
              <div class="devices-grid">
                <div v-for="d in devicesTransport" :key="d" class="device-tag">{{ d }}</div>
              </div>
            </div>
            <div class="devices-group">
              <div class="devices-group-label">Mechanizmy (analiza czasowa)</div>
              <div class="devices-grid">
                <div v-for="d in devicesMech" :key="d" class="device-tag device-tag--mech">{{ d }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== PODSTAWY PRAWNE ===== -->
    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="row q-col-gutter-xl items-center">
          <div class="col-12 col-md-6">
            <div class="eyebrow">Obowiązek prawny</div>
            <h2 class="section-h2">Rozporządzenie MPiT 2018</h2>
            <p class="text-grey-7 q-mb-lg">
              Od 2018 roku eksploatujący urządzenia transportu bliskiego
              są zobowiązani do wyznaczania i dokumentowania resursu.
              Brak dokumentacji resursu to nieprawidłowość stwierdzana przez UDT podczas kontroli.
            </p>
            <q-list separator class="legal-list rounded-borders overflow-hidden">
              <q-item v-for="item in legalItems" :key="item.par" class="q-py-md">
                <q-item-section avatar>
                  <div class="legal-par">{{ item.par }}</div>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold text-body2">{{ item.title }}</q-item-label>
                  <q-item-label caption class="q-mt-xs">{{ item.text }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
          <div class="col-12 col-md-6">
            <q-video :ratio="16/9" src="https://www.youtube.com/embed/11XT8J1bP9E"
              class="rounded-borders shadow-8" />
          </div>
        </div>
      </div>
    </section>

    <!-- ===== KROKI (ciemna sekcja) ===== -->
    <section class="steps-section">
      <div class="lc q-mx-auto q-px-md">
        <div class="text-center q-mb-xl">
          <div class="eyebrow eyebrow--light">Proces obliczenia</div>
          <h2 class="section-h2 text-white">Trzy kroki do orzeczenia</h2>
        </div>
        <div class="row q-col-gutter-xl">
          <div v-for="(step, i) in steps" :key="i" class="col-12 col-md-4">
            <div class="step-card">
              <div class="step-num">0{{ i + 1 }}</div>
              <div class="step-icon">
                <q-icon :name="step.icon" size="24px" color="primary" />
              </div>
              <h3 class="step-title">{{ step.title }}</h3>
              <p class="step-text">{{ step.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== CENNIK ===== -->
    <section class="q-py-xl">
      <div class="lc q-mx-auto q-px-md">
        <div class="text-center q-mb-xl">
          <div class="eyebrow">Cennik</div>
          <h2 class="section-h2">Prosta polityka cenowa</h2>
          <p class="section-sub">Bez abonamentów — płacisz za obliczenia których potrzebujesz.</p>
        </div>
        <div class="row q-col-gutter-lg justify-center">

          <div class="col-12 col-sm-6 col-md-4">
            <q-card flat bordered class="pricing-card column full-height">
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
                <q-btn unelevated color="primary" label="Rozpocznij" class="full-width"
                  :to="userStore.isLoggedIn ? '/dashboard' : '/register'" />
              </q-card-actions>
            </q-card>
          </div>

          <div class="col-12 col-sm-6 col-md-4">
            <q-card flat class="pricing-card pricing-card--featured column full-height">
              <div class="pricing-badge">POLECANE</div>
              <q-card-section class="col q-pa-xl">
                <div class="pricing-label">PREMIUM</div>
                <div class="pricing-price">Indywidualnie</div>
                <div class="text-grey-7 text-body2 q-mb-lg">Flota urządzeń UTB</div>
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
                  class="full-width text-weight-bold" to="/contact" />
              </q-card-actions>
            </q-card>
          </div>

          <div class="col-12 col-sm-6 col-md-4">
            <q-card flat bordered class="pricing-card column full-height">
              <q-card-section class="col q-pa-xl">
                <div class="pricing-label">EXPRESS</div>
                <div class="pricing-price">250 <span class="pricing-unit">PLN brutto</span></div>
                <div class="text-grey-7 text-body2 q-mb-lg">Pomoc techniczna na telefon</div>
                <q-separator class="q-mb-lg" />
                <p class="text-grey-7 text-body2">
                  Potrzebujesz wyniku natychmiast? Zadzwoń — przeprowadzimy Cię
                  przez obliczenia lub wykonamy je za Ciebie na podstawie danych eksploatacyjnych.
                </p>
              </q-card-section>
              <q-card-actions class="q-pa-lg q-pt-none">
                <q-btn flat color="primary" icon="phone" label="+48 666 625 752"
                  class="full-width text-weight-bold" href="tel:+48666625752" />
              </q-card-actions>
            </q-card>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== CTA ===== -->
    <section class="cta-section text-white text-center">
      <div class="lc q-mx-auto q-px-md">
        <div class="eyebrow eyebrow--light">Zacznij teraz</div>
        <h2 class="section-h2 text-white q-mb-md">Gotowy do wyznaczenia resursu?</h2>
        <p class="cta-sub q-mb-xl">
          Zarejestruj się bezpłatnie. Pierwsze obliczenie dostępne od razu.
        </p>
        <template v-if="userStore.isLoggedIn">
          <q-btn unelevated size="lg" color="primary" label="Otwórz kalkulator"
            to="/calculators" class="text-weight-bold" />
        </template>
        <template v-else>
          <q-btn unelevated size="lg" color="primary"
            label="Otwórz konto" to="/register" class="text-weight-bold q-mr-md" />
          <q-btn outline size="lg" color="white"
            label="Zaloguj się" to="/login" />
        </template>
      </div>
    </section>

    <!-- ===== DIALOG DZIENNIKA ===== -->
    <q-dialog v-model="showLogbookDialog">
      <q-card style="width: 500px; max-width: 90vw;" class="rounded-borders">
        <q-card-section class="bg-primary text-white row items-center">
          <div class="text-h6 text-weight-bold">Pobierz Dziennik Eksploatacji</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pa-md">
          <p class="text-grey-7 q-mb-md">
            Wprowadź dane urządzenia, aby wygenerować spersonalizowany nagłówek dziennika.
          </p>
          <q-form @submit="downloadLogbook" class="row q-col-gutter-md">
            <div class="col-12">
              <q-input v-model="logbookForm.email" label="Twój adres e-mail" outlined dense required type="email" />
            </div>
            <div class="col-12">
              <q-input v-model="logbookForm.rodzaj_urzadzenia" label="Rodzaj urządzenia (np. Suwnica)" outlined dense required />
            </div>
            <div class="col-12 col-sm-6">
              <q-input v-model="logbookForm.nr_fabryczny" label="Numer fabryczny" outlined dense required />
            </div>
            <div class="col-12 col-sm-6">
              <q-input v-model="logbookForm.nr_udt" label="Numer ewidencyjny UDT" outlined dense required />
            </div>
            <div class="col-12 col-sm-6">
              <q-input v-model="logbookForm.rok_budowy" label="Rok budowy" outlined dense required />
            </div>
            <div class="col-12 col-sm-6">
              <q-input v-model="logbookForm.rok_dop" label="Rok dopuszczenia" outlined dense required />
            </div>
            
            <div class="col-12 q-mt-md">
              <q-banner dense class="bg-blue-1 text-primary rounded-borders q-mb-md">
                <template v-slot:avatar>
                  <q-icon name="info" />
                </template>
                Pobierając dziennik, akceptujesz regulamin serwisu.
              </q-banner>
              <q-btn type="submit" color="primary" label="Generuj i pobierz PDF" 
                class="full-width" :loading="downloadingLogbook" icon="download" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from 'stores/user-store'
import { api } from 'boot/axios'
import { useQuasar, exportFile } from 'quasar'

const userStore = useUserStore()
const $q = useQuasar()

const showLogbookDialog = ref(false)
const downloadingLogbook = ref(false)
const logbookForm = ref({
  email: '',
  rodzaj_urzadzenia: '',
  nr_fabryczny: '',
  nr_udt: '',
  rok_budowy: '',
  rok_dop: ''
})

const downloadLogbook = async () => {
  downloadingLogbook.value = true
  try {
    const response = await api.post('/calculators/generate-logbook/', logbookForm.value, {
      responseType: 'blob'
    })
    
    const status = exportFile(
      `dziennik_${logbookForm.value.nr_fabryczny || 'utb'}.pdf`,
      response.data,
      'application/pdf'
    )

    if (status === true) {
      $q.notify({ type: 'positive', message: 'Dziennik został pobrany.', position: 'top' })
      showLogbookDialog.value = false
    }
  } catch (error) {
    console.error('Błąd pobierania dziennika:', error)
    $q.notify({ type: 'negative', message: 'Nie udało się wygenerować dziennika.', position: 'top' })
  } finally {
    downloadingLogbook.value = false
  }
}

const complianceSpecs = [
  { code: '22', label: 'Typy urządzeń', desc: 'Pełny zakres UTB' },
  { code: 'FEM', label: '9.511 / ISO 4301', desc: 'Standard obliczeń' },
  { code: 'UDT', label: 'Rozp. MPiT 2018', desc: 'Zgodność z prawem' },
  { code: 'PDF', label: 'Orzeczenie resursu', desc: 'Gotowy do złożenia' }
]

const methodology = [
  {
    step: '01',
    title: 'Widmo obciążeń',
    formula: 'Kdr = Σ [ cᵢ/100 × (Qᵢ/Qmax)³ ]',
    desc: 'Współczynnik widma obciążeń wyznaczany na podstawie historii pracy urządzenia — udziałów procentowych poszczególnych poziomów obciążenia.'
  },
  {
    step: '02',
    title: 'Projektowa zdolność cyklowa',
    formula: 'U_WSK = Qmax × Cm × 1/(Kdr × FX)',
    desc: 'Maksymalna liczba cykli jaką urządzenie może wykonać przy danym widmie obciążeń, wyznaczona na podstawie klasy pracy i współczynnika niepewności FX.'
  },
  {
    step: '03',
    title: 'Stopień zużycia resursu',
    formula: 'ρ = (n × FX) / U_WSK × 100%',
    desc: 'Procentowy stopień zużycia resursu — im bliżej 100%, tym urządzenie bliżej granicy projektowej trwałości. Wynik klasyfikowany jako L1–L4.'
  }
]

const devicesHoisting = [
  'Wciągarka', 'Wciągnik', 'Suwnica', 'Żuraw', 'Żuraw przeładunkowy',
  'Układnica magazynowa', 'Dźwignik', 'Dźwig', 'Winda dekarska'
]
const devicesTransport = [
  'Hakowiec', 'Podnosnik samochodowy', 'Autotransporter',
  'Podest ruchomy', 'Podest załadowczy', 'Wózek jezdniowy', 'Wózek specjalizowany'
]
const devicesMech = [
  'Mech. podnoszenia', 'Mech. jazdy suwnicy', 'Mech. jazdy wciągarki',
  'Mech. jazdy żurawia', 'Mech. zmiany wysięgu', 'Mech. zmiany obrotu'
]

const legalItems = [
  {
    par: '§7.4',
    title: 'Brak rejestracji eksploatacji',
    text: 'Eksploatujący odtwarza przebieg eksploatacji na podstawie wiedzy technicznej i dobrej praktyki inżynierskiej.'
  },
  {
    par: '§7.5',
    title: 'Nieznany resurs projektowy',
    text: 'Eksploatujący wyznacza resurs samodzielnie — na podstawie obliczeń metodą cykli pracy zgodną z FEM / ISO.'
  },
  {
    par: '§8',
    title: 'Obowiązek dokumentowania',
    text: 'Wyniki wyznaczenia resursu muszą być udostępnione organowi dozoru technicznego na żądanie.'
  }
]

const steps = [
  {
    icon: 'precision_manufacturing',
    title: 'Wskaż urządzenie',
    text: 'Wybierz typ UTB z 22 dostępnych kalkulatorów. System wyświetla tylko pola wymagane dla danego urządzenia.'
  },
  {
    icon: 'edit_note',
    title: 'Wprowadź dane eksploatacyjne',
    text: 'Uzupełnij historię pracy: lata eksploatacji, licznik cykli lub motogodziny, poziomy i udziały obciążeń, wyniki badań specjalnych.'
  },
  {
    icon: 'picture_as_pdf',
    title: 'Pobierz orzeczenie PDF',
    text: 'Wynik zawiera pełne obliczenia, klasę stanu technicznego L1–L4, wykres zużycia i prognozę resursu. Gotowy do złożenia w UDT.'
  }
]

const standardFeatures = [
  'Kalkulator zgodny z FEM 9.511',
  'Archiwizacja wyników',
  'Aktualizacja w kolejnych latach',
  'Orzeczenie PDF z tabelami i wykresem'
]

const premiumFeatures = [
  'Priorytetowe wsparcie techniczne',
  'Personalizacja orzeczenia (logo firmy)',
  'Zbiorcza faktura miesięczna',
  'Nielimitowana liczba urządzeń'
]
</script>

<style scoped lang="scss">
@use "sass:color";

// ────────────────────────────────────────
// Kontenery i typografia wspólna
// ────────────────────────────────────────
.lc { max-width: 1200px; }

.eyebrow {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: $primary;
  margin-bottom: 10px;
}

.eyebrow--light { color: rgba(white, 0.45); }

.section-h2 {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1.15;
  margin: 0 0 16px;
}

.section-sub {
  font-size: 1rem;
  color: #607080;
  margin: 0;
}

// ────────────────────────────────────────
// Hero
// ────────────────────────────────────────
.hero-section {
  position: relative;
  overflow: hidden;
  background: linear-gradient(145deg, $primary 0%, color.adjust($primary, $lightness: -24%) 100%);
  padding: 88px 0 80px;
}

.hero-tech-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  svg { width: 100%; height: 100%; }
}

.norm-chips { display: flex; gap: 8px; flex-wrap: wrap; }

.norm-chip {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border: 1px solid rgba(white, 0.35);
  border-radius: 3px;
  color: rgba(white, 0.8);
  background: rgba(white, 0.07);
}

.hero-h1 {
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: -0.02em;
  margin: 0 0 20px;
}

.hero-sub {
  font-size: 1.05rem;
  line-height: 1.6;
  opacity: 0.72;
  margin: 0 0 24px;
  max-width: 520px;
}

.hero-spec-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    font-size: 0.9rem;
    opacity: 0.8;
    padding-left: 20px;
    position: relative;

    &::before {
      content: '—';
      position: absolute;
      left: 0;
      opacity: 0.5;
    }
  }
}

.hero-illustration {
  width: 100%;
  max-width: 440px;
  height: auto;
  filter: drop-shadow(0 8px 32px rgba(0, 0, 0, 0.35));
}

// ────────────────────────────────────────
// Pasek zgodności
// ────────────────────────────────────────
.compliance-strip {
  background: #0A1929;
  padding: 0;
}

.compliance-item {
  padding: 28px 20px;
  border-right: 1px solid rgba(white, 0.06);
  &:last-child { border-right: none; }
}

.compliance-code {
  font-family: 'Roboto Mono', monospace;
  font-size: 1.9rem;
  font-weight: 900;
  color: $primary;
  letter-spacing: -0.02em;
  line-height: 1;
  margin-bottom: 4px;
}

.compliance-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: rgba(white, 0.85);
  margin-bottom: 2px;
}

.compliance-desc {
  font-size: 0.68rem;
  color: rgba(white, 0.35);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

// ────────────────────────────────────────
// Metodologia
// ────────────────────────────────────────
.method-card {
  padding: 28px 24px;
  border-top: 3px solid $primary;
  border-left: 1px solid rgba(black, 0.07);
  border-right: 1px solid rgba(black, 0.07);
  border-bottom: 1px solid rgba(black, 0.07);
  border-radius: 0 0 6px 6px;
  background: white;

  .body--dark & {
    background: #1e2a38;
    border-left-color: rgba(white, 0.08);
    border-right-color: rgba(white, 0.08);
    border-bottom-color: rgba(white, 0.08);
  }
}

.method-step {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: $primary;
  margin-bottom: 12px;
}

.method-title {
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0 0 14px;
  color: inherit;
}

.method-formula {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
  background: rgba($primary, 0.06);
  border-left: 3px solid rgba($primary, 0.4);
  padding: 10px 14px;
  border-radius: 0 4px 4px 0;
  color: color.adjust($primary, $lightness: -10%);
  margin-bottom: 16px;
  word-break: break-all;

  .body--dark & {
    background: rgba($primary, 0.12);
    color: color.adjust($primary, $lightness: 25%);
  }
}

.method-desc {
  font-size: 0.88rem;
  color: #607080;
  line-height: 1.6;
  margin: 0;

  .body--dark & { color: rgba(white, 0.55); }
}

// ────────────────────────────────────────
// Urządzenia UTB
// ────────────────────────────────────────
.devices-section {
  background: #F4F7FA;
  .body--dark & { background: #151f2d; }
}

.devices-group { }

.devices-group-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #8a9bb0;
  margin-bottom: 10px;
}

.devices-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.device-tag {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 5px 12px;
  border-radius: 4px;
  border: 1px solid rgba($primary, 0.2);
  color: $primary;
  background: rgba($primary, 0.05);

  .body--dark & {
    border-color: rgba($primary, 0.3);
    background: rgba($primary, 0.1);
  }
}

.device-tag--mech {
  border-color: rgba(#546E7A, 0.3);
  color: #546E7A;
  background: rgba(#546E7A, 0.05);

  .body--dark & {
    border-color: rgba(#90A4AE, 0.3);
    color: #90A4AE;
    background: rgba(#546E7A, 0.1);
  }
}

// ────────────────────────────────────────
// Podstawy prawne
// ────────────────────────────────────────
.legal-list {
  background: white;
  .body--dark & { background: #1e2a38; }
}

.legal-par {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  color: $primary;
  white-space: nowrap;
}

// ────────────────────────────────────────
// Kroki
// ────────────────────────────────────────
.steps-section {
  background: #0A1929;
  padding: 80px 0;
}

.step-card {
  padding: 32px 0 0;
  border-top: 2px solid rgba(white, 0.08);
}

.step-num {
  font-family: 'Roboto Mono', monospace;
  font-size: 3.5rem;
  font-weight: 900;
  color: $primary;
  opacity: 0.35;
  line-height: 1;
  margin-bottom: 16px;
}

.step-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: rgba($primary, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.step-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
  margin: 0 0 10px;
}

.step-text {
  font-size: 0.9rem;
  color: rgba(white, 0.5);
  line-height: 1.65;
  margin: 0;
}

// ────────────────────────────────────────
// Cennik
// ────────────────────────────────────────
.pricing-card {
  border-radius: 8px;
  transition: box-shadow 0.2s;
  &:hover { box-shadow: 0 6px 24px rgba(black, 0.08); }
}

.pricing-card--featured {
  border: 2px solid $primary !important;
  position: relative;
}

.pricing-badge {
  position: absolute;
  top: -13px;
  left: 50%;
  transform: translateX(-50%);
  background: $primary;
  color: white;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  padding: 4px 14px;
  border-radius: 20px;
}

.pricing-label {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: $primary;
  margin-bottom: 10px;
}

.pricing-price {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 4px;
  line-height: 1.1;
}

.pricing-unit {
  font-size: 0.85rem;
  font-weight: 400;
  color: #8a9bb0;
}

// ────────────────────────────────────────
// CTA
// ────────────────────────────────────────
.cta-section {
  background: #0A1929;
  padding: 88px 0;
}

.cta-sub {
  font-size: 1.05rem;
  color: rgba(white, 0.5);
  margin: 0;
}

// ────────────────────────────────────────
// Dziennik Eksploatacji
// ────────────────────────────────────────
.logbook-preview {
  width: 300px;
  height: 400px;
  background: white;
  border-radius: 4px;
  padding: 30px 20px;
  position: relative;
  color: #334155;
  transform: rotate(3deg);
  transition: transform 0.3s;
  &:hover { transform: rotate(0deg) scale(1.05); }
}

.logbook-header {
  font-weight: 800;
  font-size: 1.1rem;
  text-align: center;
  border-bottom: 2px solid $primary;
  padding-bottom: 10px;
  margin-bottom: 20px;
  text-transform: uppercase;
}

.logbook-lines {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.logbook-line {
  height: 1px;
  background: rgba(0,0,0,0.1);
  width: 100%;
}

.logbook-stamp {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 60px;
  height: 60px;
  border: 3px double $primary;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  color: $primary;
  opacity: 0.4;
  transform: rotate(-15deg);
}

.bg-icon-deco {
  position: absolute;
  right: -50px;
  top: -50px;
  font-size: 300px;
  color: white;
  opacity: 0.05;
  pointer-events: none;
}
</style>
