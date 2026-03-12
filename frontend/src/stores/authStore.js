import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const ADMIN_EMAIL    = import.meta.env.VITE_ADMIN_EMAIL    || 'admin@predictfc.com'
const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD || 'predictfc2026'

export const useAuthStore = create(
  persist(
    (set) => ({
      user:    null,
      token:   null,
      isAuth:  false,

      login: async (email, password) => {
        if (email === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
          const user  = { email, role: 'admin', name: 'Admin' }
          const token = btoa(`${email}:${Date.now()}`)
          set({ user, token, isAuth: true })
          return { success: true }
        }
        return { success: false, error: 'Identifiants incorrects' }
      },

      logout: () => set({ user: null, token: null, isAuth: false }),
    }),
    {
      name:    'predictfc-auth',
      partialize: (s) => ({ user: s.user, token: s.token, isAuth: s.isAuth }),
    }
  )
)
