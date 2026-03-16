import { boot } from 'quasar/wrappers'
import axios from 'axios'
import { Cookies, Notify } from 'quasar'
import { useUserStore } from 'stores/user-store'

const api = axios.create({
  baseURL: process.env.API_BASE_URL || 'http://localhost:8000/api',
  withCredentials: true,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

export default boot(async ({ app, router, store }) => {

  // 1. Request Interceptor (rejestracja przed CSRF żeby obsłużyć ewentualne błędy)
  api.interceptors.request.use((config) => {
    if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
      const csrfToken = Cookies.get('csrftoken')
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
      }
    }
    return config
  })

  // 2. Response Interceptor
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config

      // --- 401 UNAUTHORIZED ---
      if (error.response && error.response.status === 401 && !originalRequest._retry) {
        if (originalRequest.url.includes('/auth/login/') || originalRequest.url.includes('/auth/token/refresh/')) {
           return Promise.reject(error)
        }

        originalRequest._retry = true
        try {
          await api.post('/auth/token/refresh/')
          return api(originalRequest)
        } catch (refreshError) {
          const userStore = useUserStore(store)
          userStore.user = null
          if (router.currentRoute.value.path !== '/login') {
             router.push({ path: '/login', query: { next: router.currentRoute.value.fullPath } })
          }
          return Promise.reject(refreshError)
        }
      }

      // --- TIMEOUT ---
      if (error.code === 'ECONNABORTED') {
        Notify.create({ type: 'negative', message: 'Brak odpowiedzi serwera. Sprawdź połączenie.', position: 'top', timeout: 5000 })
        return Promise.reject(error)
      }

      // --- GLOBALNE BŁĘDY (pomiń jeśli komponent obsługuje sam przez skipGlobalNotify) ---
      if (
        error.response &&
        error.response.status !== 401 &&
        error.response.status !== 404 &&
        !originalRequest.skipGlobalNotify
      ) {
        // Backend zawsze zwraca {"detail": "..."} dzięki custom_exception_handler
        const msg = error.response.data?.detail || 'Błąd serwera.'
        Notify.create({ type: 'negative', message: msg, position: 'top', timeout: 4000 })
      }

      return Promise.reject(error)
    }
  )

  // 3. CSRF (po interceptorach — teraz globalny handler obsługuje ewentualne błędy)
  try {
    await api.get('/auth/csrf/')
  } catch (e) {
    console.warn('[Axios] CSRF Fail', e)
  }

  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

export { api }