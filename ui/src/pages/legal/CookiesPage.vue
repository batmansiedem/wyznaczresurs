<template>
  <q-page padding class="legal-page">
    <div class="legal-container">
      <div class="row items-center q-mb-lg">
        <q-icon name="cookie" size="2rem" color="primary" class="q-mr-sm" />
        <div>
          <div class="text-h5 text-weight-bold">Polityka plików Cookies</div>
          <div class="text-caption text-grey-6">Ostatnia aktualizacja: 1 marca 2026 r.</div>
        </div>
      </div>

      <q-card flat bordered class="q-pa-lg q-mb-md">
        <div class="text-h6 text-primary q-mb-sm">1. Czym są pliki cookies?</div>
        <p>
          Pliki cookies (ciasteczka) to małe pliki tekstowe zapisywane na Twoim urządzeniu (komputerze, tablecie,
          smartfonie) przez przeglądarkę internetową podczas odwiedzania stron internetowych.
          Cookies pozwalają stronie zapamiętać Twoje preferencje i ułatwiają korzystanie z serwisu.
        </p>

        <div class="text-h6 text-primary q-mb-sm q-mt-md">2. Jakich cookies używamy?</div>
        <q-list bordered separator class="rounded-borders q-mb-md">
          <q-item>
            <q-item-section avatar><q-icon name="security" color="positive" /></q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">Niezbędne (sesja i bezpieczeństwo)</q-item-label>
              <q-item-label caption>
                <b>csrftoken</b> — token CSRF chroniący przed atakami CSRF. Wymagany do prawidłowego działania formularzy.<br>
                <b>sessionid / access_token / refresh_token</b> — cookies uwierzytelniające (HttpOnly), przechowują sesję zalogowanego użytkownika.
              </q-item-label>
            </q-item-section>
            <q-item-section side><q-badge color="positive">Wymagane</q-badge></q-item-section>
          </q-item>
          <q-item>
            <q-item-section avatar><q-icon name="settings" color="info" /></q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">Funkcjonalne (preferencje)</q-item-label>
              <q-item-label caption>
                Przechowują preferencje interfejsu, np. tryb ciemny. Nie zbierają danych osobowych.
              </q-item-label>
            </q-item-section>
            <q-item-section side><q-badge color="info">Opcjonalne</q-badge></q-item-section>
          </q-item>
        </q-list>

        <div class="text-h6 text-primary q-mb-sm q-mt-md">3. Jak zarządzać cookies?</div>
        <p>
          Możesz kontrolować i usuwać pliki cookies poprzez ustawienia swojej przeglądarki.
          Usunięcie cookies niezbędnych spowoduje wylogowanie z serwisu i może uniemożliwić korzystanie z niektórych funkcji.
        </p>
        <p>Instrukcje zarządzania cookies dla popularnych przeglądarek:</p>
        <ul>
          <li>Chrome: Ustawienia → Prywatność i bezpieczeństwo → Pliki cookie</li>
          <li>Firefox: Opcje → Prywatność i bezpieczeństwo → Ciasteczka</li>
          <li>Edge: Ustawienia → Prywatność, wyszukiwanie i usługi → Pliki cookie</li>
          <li>Safari: Preferencje → Prywatność → Pliki cookie i dane witryn</li>
        </ul>

        <div class="text-h6 text-primary q-mb-sm q-mt-md">4. Okres przechowywania</div>
        <p>
          Cookies sesyjne (np. <code>sessionid</code>) są usuwane po zamknięciu przeglądarki.
          Cookies trwałe (np. <code>csrftoken</code>) wygasają zgodnie z ich ustawieniami — zwykle po 1 roku.
          Tokeny JWT mają ograniczony czas życia (access token: 60 minut, refresh token: 7 dni).
        </p>

        <div class="text-h6 text-primary q-mb-sm q-mt-md">5. Cookies stron trzecich</div>
        <p>
          Serwis <b>wyznaczresurs.com</b> <strong>nie korzysta</strong> z cookies śledzących, reklamowych ani
          analitycznych podmiotów trzecich (np. Google Analytics, Meta Pixel). Wszystkie cookies pochodzą
          wyłącznie z domeny wyznaczresurs.com.
        </p>

        <div class="text-h6 text-primary q-mb-sm q-mt-md">6. Kontakt</div>
        <p>
          W sprawach dotyczących polityki cookies prosimy o kontakt:
          <strong>kontakt@wyznaczresurs.com</strong>
        </p>
      </q-card>

      <div class="text-center q-mt-lg">
        <q-btn outline color="primary" icon="arrow_back" label="Powrót" @click="$router.back()" />
      </div>
    </div>
  </q-page>
</template>

<script setup>
</script>

<style scoped>
.legal-container {
  max-width: 860px;
  margin: 0 auto;
}
p { line-height: 1.7; margin-bottom: 10px; }
ul { line-height: 1.8; padding-left: 20px; }
code { background: #f0f4ff; padding: 1px 5px; border-radius: 3px; font-size: 0.9em; }
</style>
