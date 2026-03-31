import { boot } from 'quasar/wrappers'

// Wyrejestruj stare service workery (pozostałość po PWA build)
export default boot(() => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      for (const reg of registrations) {
        reg.unregister()
      }
    })
  }
})
