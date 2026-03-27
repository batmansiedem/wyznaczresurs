<template>
  <q-list bordered separator class="rounded-borders overflow-hidden faq-list">
    <q-expansion-item
      v-for="item in faqItems"
      :key="item.q"
      group="faq"
      :icon="item.icon"
      :label="item.q"
      header-class="text-weight-bold faq-header"
    >
      <q-card flat>
        <q-card-section class="text-grey-8 faq-body" :class="dark ? 'faq-body--dark' : ''">
          <div v-html="item.a" />
        </q-card-section>
      </q-card>
    </q-expansion-item>
  </q-list>
</template>

<script setup>
defineProps({ dark: Boolean })

const faqItems = [
  {
    icon: 'shopping_cart',
    q: 'Jak kupić punkty premium?',
    a: `<ol style="margin:0;padding-left:20px;line-height:1.7">
      <li>Przejdź do zakładki <strong>Cennik i punkty</strong> w menu bocznym lub kliknij <strong>Kup punkty</strong> na pulpicie.</li>
      <li>Wybierz płatność <strong>PayPal</strong> (natychmiastowa aktywacja) lub <strong>przelew bankowy</strong> (aktywacja do 24h).</li>
      <li>Punkty zostaną przypisane do Twojego konta automatycznie.</li>
    </ol>`
  },
  {
    icon: 'calculate',
    q: 'Jak wykonać obliczenie resursu?',
    a: `<p style="margin:0;line-height:1.7">Wybierz typ urządzenia z listy 22 kalkulatorów, uzupełnij dane eksploatacyjne (lata pracy, licznik cykli lub motogodziny, poziomy obciążeń). System automatycznie wyznacza stopień zużycia resursu i klasę stanu technicznego L1–L4.</p>`
  },
  {
    icon: 'verified_user',
    q: 'Czy obliczenia są zgodne z UDT?',
    a: `<p style="margin:0;line-height:1.7">Tak. Wszystkie algorytmy opracowano na podstawie Rozporządzenia MPiT z dnia 30 października 2018 r. oraz wytycznych FEM 9.511 i normy ISO 4301. Wyznaczenie resursu PDF jest akceptowane przez Urząd Dozoru Technicznego.</p>`
  },
  {
    icon: 'picture_as_pdf',
    q: 'Co zawiera raport PDF?',
    a: `<p style="margin:0;line-height:1.7">Raport zawiera: dane identyfikacyjne urządzenia, historię eksploatacji, pełne obliczenia metodą cykli pracy (Kdr, UWSK, ρ), klasę stanu technicznego L1–L4, wykres kołowy zużycia resursu oraz prognozę daty osiągnięcia resursu.</p>`
  },
  {
    icon: 'update',
    q: 'Czy mogę zaktualizować obliczenia w kolejnym roku?',
    a: `<p style="margin:0;line-height:1.7">Tak. Zapisane wyniki możesz edytować — zaktualizuj dane eksploatacyjne o kolejny rok pracy i wygeneruj nowy raport PDF. Każda aktualizacja kosztuje 80 punktów.</p>`
  },
  {
    icon: 'lock',
    q: 'Co to jest wynik zablokowany?',
    a: `<p style="margin:0;line-height:1.7">Gdy na koncie brakuje punktów, obliczenie jest wykonywane, ale wyniki pozostają zablokowane (widoczna tylko informacja o braku punktów). Wynik można odblokować w dowolnym momencie po doładowaniu konta — kosztuje to 80 pkt.</p>`
  }
]
</script>

<style scoped lang="scss">
.faq-list { background: white; }
.body--dark .faq-list { background: #1e2a38; }

.faq-header { color: $primary; }

.faq-body {
  line-height: 1.65;
  padding: 12px 20px 20px;
}
.faq-body--dark { color: rgba(255,255,255,0.72) !important; }
</style>
