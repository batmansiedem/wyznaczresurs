<template>
  <LegalPageLayout
    icon="cookie"
    eyebrow="Cookies"
    title="Polityka plików Cookies"
    subtitle="Ostatnia aktualizacja: 1 marca 2026 r."
  >
    <section class="q-mb-lg">
      <div class="text-h6 text-primary q-mb-sm">1. Czym są pliki cookies?</div>
      <p>
        Pliki cookies (ciasteczka) to małe pliki tekstowe zapisywane na Twoim urządzeniu (komputerze, tablecie,
        smartfonie) przez przeglądarkę internetową podczas odwiedzania stron internetowych.
        Cookies pozwalają stronie zapamiętać Twoje preferencje i ułatwiają korzystanie z serwisu.
      </p>
    </section>

    <section class="q-mb-lg">
      <div class="text-h6 text-primary q-mb-sm">2. Jakich cookies używamy?</div>
      <q-list bordered separator class="rounded-borders">
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
    </section>

    <section class="q-mb-lg">
      <div class="text-h6 text-primary q-mb-sm">3. Jak zarządzać cookies?</div>
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
    </section>

    <section class="q-mb-lg">
      <div class="text-h6 text-primary q-mb-sm">4. Okres przechowywania</div>
      <p>
        Cookies sesyjne (np. <code>sessionid</code>) są usuwane po zamknięciu przeglądarki.
        Cookies trwałe (np. <code>csrftoken</code>) wygasają zgodnie z ich ustawieniami — zwykle po 1 roku.
        Tokeny JWT mają ograniczony czas życia (access token: 60 minut, refresh token: 7 dni).
      </p>
    </section>

    <section class="q-mb-lg">
      <div class="text-h6 text-primary q-mb-sm">5. Cookies stron trzecich</div>
      <p>
        Serwis <b>wyznaczresurs.com</b> <strong>nie korzysta</strong> z cookies śledzących, reklamowych ani
        analitycznych podmiotów trzecich (np. Google Analytics, Meta Pixel). Wszystkie cookies pochodzą
        wyłącznie z domeny wyznaczresurs.com.
      </p>
    </section>

    <section class="q-mb-lg">
      <div class="text-h6 text-primary q-mb-sm">6. Kontakt</div>
      <p>
        W sprawach dotyczących polityki cookies prosimy o kontakt:
        <strong>kontakt@wyznaczresurs.com</strong>
      </p>
    </section>
  </LegalPageLayout>
</template>

<script setup>
import LegalPageLayout from 'components/shared/LegalPageLayout.vue'
</script>
