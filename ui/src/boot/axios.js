import { boot } from 'quasar/wrappers'
import axios from 'axios'
import { Cookies, Notify } from 'quasar'
import { useUserStore } from 'stores/user-store'

const api = axios.create({
  baseURL: process.env.API_BASE_URL || 'http://localhost:8000/api',
  withCredentials: true,
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

      // --- GLOBALNE BŁĘDY (pomiń jeśli komponent obsługuje sam przez skipGlobalNotify) ---
      if (
        error.response &&
        error.response.status !== 401 &&
        error.response.status !== 404 &&
        !originalRequest.skipGlobalNotify
      ) {
         let msg = 'Błąd serwera.'
         const data = error.response.data
         if (data && typeof data === 'object') {
            const keys = Object.keys(data)
            if (keys.length > 0) {
               const firstKey = keys[0]
               const val = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey]
               msg = (firstKey === 'non_field_errors' || firstKey === 'detail') ? val : `${firstKey}: ${val}`
            }
         }
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