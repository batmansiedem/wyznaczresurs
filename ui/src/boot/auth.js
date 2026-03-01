import { boot } from 'quasar/wrappers'
import { useUserStore } from 'stores/user-store'

export default boot(async ({ router, store }) => {
  const userStore = useUserStore(store)
  await userStore.fetchUser()

  router.beforeEach((to, from, next) => {
    const isAuthenticated = userStore.isLoggedIn
    const requiresAuth = to.meta.requiresAuth
    const requiresSuperuser = to.meta.requiresSuperuser

    if (requiresAuth && !isAuthenticated) {
      // Niezalogowany → strona logowania z powrotem do żądanej ścieżki
      next({ path: '/login', query: { next: to.fullPath } })
    } else if (requiresSuperuser && !userStore.user?.is_superuser) {
      // Nie-superuser próbuje wejść do panelu admina
      next('/dashboard')
    } else if (isAuthenticated && ['/', '/login', '/register', '/forgot-password'].includes(to.path)) {
      // Zalogowany na stronach publicznych / landing → pulpit
      next('/dashboard')
    } else {
      next()
    }
  })
})
