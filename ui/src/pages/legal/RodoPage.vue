<template>
  <q-page padding class="legal-page">
    <div class="legal-container">
      <div class="row items-center q-mb-lg">
        <q-icon name="privacy_tip" size="2rem" color="primary" class="q-mr-sm" />
        <div>
          <div class="text-h5 text-weight-bold">Polityka Prywatności (RODO)</div>
          <div class="text-caption text-grey-6">Rozporządzenie RODO / GDPR — obowiązuje od 1 marca 2026 r.</div>
        </div>
      </div>

      <q-card flat bordered class="q-pa-lg">

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">1. Administrator danych osobowych</div>
          <p>
            Administratorem Twoich danych osobowych jest właściciel serwisu <strong>wyznaczresurs.com</strong>
            (dalej: „Administrator"). Kontakt z Administratorem w sprawach dotyczących danych osobowych:
            <strong>kontakt@wyznaczresurs.com</strong>.
          </p>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">2. Jakie dane zbieramy?</div>
          <q-list bordered separator class="rounded-borders">
            <q-item>
              <q-item-section avatar><q-icon name="email" color="primary" /></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">Dane konta</q-item-label>
                <q-item-label caption>Adres e-mail (login), imię, nazwisko, hasło (hashowane).</q-item-label>
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar><q-icon name="corporate_fare" color="primary" /></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">Dane firmowe</q-item-label>
                <q-item-label caption>Nazwa firmy, NIP, adres — wyłącznie dla kont firmowych, na potrzeby wystawiania faktur.</q-item-label>
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar><q-icon name="calculate" color="primary" /></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">Dane obliczeń</q-item-label>
                <q-item-label caption>Dane wejściowe i wyniki kalkulatorów zapisywane na koncie Użytkownika.</q-item-label>
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar><q-icon name="history" color="primary" /></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">Dane logowań</q-item-label>
                <q-item-label caption>Data i czas ostatniego logowania, historia prób logowania (na potrzeby bezpieczeństwa — ochrona przed brute-force).</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">3. Podstawa prawna i cel przetwarzania</div>
          <q-table
            :rows="legalBases"
            :columns="legalBaseCols"
            row-key="cel"
            flat bordered dense hide-bottom
            :rows-per-page-options="[0]"
          />
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">4. Odbiorcy danych</div>
          <p>Twoje dane mogą być udostępniane:</p>
          <ul>
            <li><strong>Podmiotom przetwarzającym dane w imieniu Administratora</strong> — hostingodawca (serwer aplikacji).</li>
            <li><strong>Operatorom płatności</strong> — wyłącznie dane niezbędne do realizacji transakcji (np. e-mail).</li>
            <li><strong>Krajowej Administracji Skarbowej (KSeF)</strong> — dane fakturowe przesyłane do systemu e-faktur.</li>
          </ul>
          <p>Dane nie są przekazywane do państw trzecich (poza EOG).</p>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">5. Okres przechowywania danych</div>
          <ul>
            <li>Dane konta — do czasu usunięcia konta lub przez 5 lat od ostatniej aktywności.</li>
            <li>Dane fakturowe — 5 lat od zakończenia roku podatkowego (wymogi prawa podatkowego).</li>
            <li>Logi bezpieczeństwa — 12 miesięcy.</li>
            <li>Dane obliczeń — do czasu usunięcia przez Użytkownika lub usunięcia konta.</li>
          </ul>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">6. Twoje prawa</div>
          <div class="row q-col-gutter-md">
            <div v-for="right in rights" :key="right.title" class="col-12 col-md-6">
              <q-card flat bordered class="q-pa-md">
                <div class="row items-center q-mb-xs">
                  <q-icon :name="right.icon" color="primary" class="q-mr-sm" />
                  <div class="text-weight-bold">{{ right.title }}</div>
                </div>
                <div class="text-caption text-grey-7">{{ right.desc }}</div>
              </q-card>
            </div>
          </div>
          <p class="q-mt-md">
            Aby skorzystać z przysługujących Ci praw, skontaktuj się z nami pod adresem:
            <strong>kontakt@wyznaczresurs.com</strong>.
            Odpowiemy w ciągu 30 dni.
          </p>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">7. Bezpieczeństwo danych</div>
          <ul>
            <li>Hasła są przechowywane w postaci skrótu kryptograficznego (hash).</li>
            <li>Sesje chronione tokenami JWT w HttpOnly cookies (niedostępne z poziomu JavaScript).</li>
            <li>Ochrona przed atakami brute-force (blokowanie konta po wielokrotnych nieudanych próbach logowania — django-axes).</li>
            <li>Komunikacja szyfrowana protokołem HTTPS (TLS).</li>
            <li>Ochrona przed CSRF (Cross-Site Request Forgery) — token CSRF.</li>
          </ul>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">8. Pliki cookies</div>
          <p>
            Szczegółowe informacje o używanych plikach cookies znajdziesz w
            <router-link to="/cookies" class="text-primary">Polityce cookies</router-link>.
          </p>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">9. Prawo do skargi</div>
          <p>
            Masz prawo wniesienia skargi do organu nadzorczego — Prezesa Urzędu Ochrony Danych Osobowych (PUODO),
            ul. Stawki 2, 00-193 Warszawa, uodo.gov.pl.
          </p>
        </section>

        <section class="q-mb-lg">
          <div class="text-h6 text-primary q-mb-sm">10. Zmiany polityki prywatności</div>
          <p>
            Administrator zastrzega prawo do zmiany niniejszej Polityki. O zmianach poinformujemy
            e-mailem z 14-dniowym wyprzedzeniem.
          </p>
        </section>

      </q-card>

      <div class="text-center q-mt-lg">
        <q-btn outline color="primary" icon="arrow_back" label="Powrót" @click="$router.back()" />
      </div>
    </div>
  </q-page>
</template>

<script setup>
const legalBases = [
  { cel: 'Obsługa konta i logowanie', podstawa: 'Art. 6 ust. 1 lit. b RODO', opis: 'Wykonanie umowy o świadczenie usług' },
  { cel: 'Wystawianie faktur', podstawa: 'Art. 6 ust. 1 lit. c RODO', opis: 'Obowiązek prawny (przepisy podatkowe)' },
  { cel: 'Archiwizacja obliczeń', podstawa: 'Art. 6 ust. 1 lit. b RODO', opis: 'Wykonanie umowy — funkcja konta' },
  { cel: 'Bezpieczeństwo (logi)', podstawa: 'Art. 6 ust. 1 lit. f RODO', opis: 'Prawnie uzasadniony interes Administratora' },
  { cel: 'Marketing (newsletter)', podstawa: 'Art. 6 ust. 1 lit. a RODO', opis: 'Zgoda Użytkownika (jeśli wyrażona)' },
]
const legalBaseCols = [
  { name: 'cel', label: 'Cel przetwarzania', field: 'cel', align: 'left' },
  { name: 'podstawa', label: 'Podstawa prawna', field: 'podstawa', align: 'left' },
  { name: 'opis', label: 'Opis', field: 'opis', align: 'left' },
]

const rights = [
  { icon: 'visibility', title: 'Prawo dostępu', desc: 'Możesz żądać informacji o przetwarzanych danych osobowych.' },
  { icon: 'edit', title: 'Prawo do sprostowania', desc: 'Możesz żądać poprawienia nieprawidłowych lub uzupełnienia niekompletnych danych.' },
  { icon: 'delete_forever', title: 'Prawo do usunięcia', desc: 'Możesz żądać usunięcia danych („prawo do bycia zapomnianym").' },
  { icon: 'block', title: 'Prawo do ograniczenia', desc: 'Możesz żądać ograniczenia przetwarzania w określonych przypadkach.' },
  { icon: 'sync_alt', title: 'Prawo do przenoszenia', desc: 'Możesz otrzymać swoje dane w formacie nadającym się do odczytu maszynowego.' },
  { icon: 'pan_tool', title: 'Prawo do sprzeciwu', desc: 'Możesz wnieść sprzeciw wobec przetwarzania opartego na prawnie uzasadnionym interesie.' },
]
</script>

<style scoped>
.legal-container {
  max-width: 860px;
  margin: 0 auto;
}
ol, ul { line-height: 1.8; padding-left: 22px; margin-bottom: 8px; }
li { margin-bottom: 4px; }
p { line-height: 1.7; }
section { border-left: 3px solid #e3f2fd; padding-left: 16px; }
</style>
