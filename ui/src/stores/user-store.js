import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    loading: false
  }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    isCompany: (state) => state.user?.is_company || false
  },

  actions: {
    async fetchUser() {
      this.loading = true
      try {
        // ZMIANA: dj-rest-auth używa '/user/' (liczba pojedyncza)
        const response = await api.get('/auth/user/')
        this.user = response.data
      } catch (error) {
        // Ignoruj błąd 401 (brak sesji) przy starcie, loguj inne
        if (error.response?.status !== 401) {
          console.error('[UserStore] Fetch User Error:', error)
        }
        this.user = null
      } finally {
        this.loading = false
      }
    },

    async login(credentials) {
      try {
        // ZMIANA: dj-rest-auth używa '/login/'
        await api.post('/auth/login/', credentials)
        await this.fetchUser()
      } catch (error) {
        console.error('[UserStore] Login Error:', error)
        throw error
      }
    },

    async logout() {
      try {
        await api.post('/auth/logout/')
      } catch (error) {
        console.warn('[UserStore] Logout Warning:', error)
      } finally {
        this.user = null
      }
    },

    async register(userData) {
      try {
        await api.post('/auth/registration/', userData)
      } catch (error) {
        console.error('[UserStore] Register Error:', error)
        throw error
      }
    }
  }
})