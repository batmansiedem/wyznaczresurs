const routes = [
  // Landing + auth — zawsze LandingLayout
  {
    path: '/',
    component: () => import('layouts/LandingLayout.vue'),
    children: [
      { path: '', component: () => import('pages/LandingPage.vue') },
      { path: 'login',          meta: { title: 'Logowanie' },            component: () => import('pages/auth/LoginPage.vue') },
      { path: 'register',       meta: { title: 'Rejestracja' },          component: () => import('pages/auth/RegisterPage.vue') },
      { path: 'forgot-password', meta: { title: 'Resetuj hasło' },       component: () => import('pages/auth/ForgotPasswordPage.vue') },
      { path: 'password-reset/confirm/:uid/:token', props: true,         component: () => import('pages/auth/ResetPasswordConfirmPage.vue') },
      { path: 'confirm-email/:key', props: true,                         component: () => import('pages/auth/EmailConfirmPage.vue') }
    ]
  },

  // Strony prawne — DualLayout (dostępne dla wszystkich)
  {
    path: '/',
    component: () => import('layouts/DualLayout.vue'),
    children: [
      { path: 'regulamin', meta: { title: 'Regulamin',             breadcrumbs: [{ label: 'Regulamin' }] },             component: () => import('pages/legal/TermsPage.vue') },
      { path: 'rodo',      meta: { title: 'Polityka prywatności',  breadcrumbs: [{ label: 'Polityka prywatności' }] },  component: () => import('pages/legal/RodoPage.vue') },
      { path: 'cookies',   meta: { title: 'Polityka cookies',      breadcrumbs: [{ label: 'Polityka cookies' }] },      component: () => import('pages/legal/CookiesPage.vue') }
    ]
  },

  // App — chronione (wymagają logowania)
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        meta: { title: 'Pulpit', breadcrumbs: [{ label: 'Pulpit' }] },
        component: () => import('pages/DashboardPage.vue')
      },
      {
        path: 'calculators',
        meta: { title: 'Kalkulatory', breadcrumbs: [{ label: 'Kalkulatory' }] },
        component: () => import('pages/CalculatorsListPage.vue')
      },
      {
        path: 'calculators/:slug',
        name: 'calculator',
        props: true,
        meta: { title: 'Kalkulator', breadcrumbs: [{ label: 'Kalkulatory', to: '/calculators' }, { label: '' }] },
        component: () => import('pages/calculators/UniversalCalculator.vue')
      },
      {
        path: 'saved-results',
        meta: { title: 'Zapisane wyniki', breadcrumbs: [{ label: 'Zapisane wyniki' }] },
        component: () => import('pages/SavedResultsPage.vue')
      },
      {
        path: 'account',
        meta: { title: 'Moje konto', breadcrumbs: [{ label: 'Moje konto' }] },
        component: () => import('pages/AccountPage.vue')
      },
      {
        path: 'change-password',
        meta: { title: 'Zmień hasło', breadcrumbs: [{ label: 'Moje konto', to: '/account' }, { label: 'Zmień hasło' }] },
        component: () => import('pages/auth/ChangePasswordPage.vue')
      },
      {
        path: 'invoices',
        meta: { title: 'Faktury', breadcrumbs: [{ label: 'Faktury' }] },
        component: () => import('pages/InvoicesPage.vue')
      },
      {
        path: 'notifications',
        meta: { title: 'Powiadomienia', breadcrumbs: [{ label: 'Powiadomienia' }], requiresSuperuser: true },
        component: () => import('pages/NotificationsPage.vue')
      },
      {
        path: 'admin',
        meta: { title: 'Panel administratora', breadcrumbs: [{ label: 'Panel administratora' }], requiresSuperuser: true },
        component: () => import('pages/AdminPage.vue')
      }
    ]
  },

  // DualLayout — kontakt, cennik, pomoc (MainLayout dla zalogowanych, LandingLayout dla gości)
  {
    path: '/',
    component: () => import('layouts/DualLayout.vue'),
    children: [
      {
        path: 'contact',
        meta: { title: 'Kontakt', breadcrumbs: [{ label: 'Kontakt' }] },
        component: () => import('pages/ContactPage.vue')
      },
      {
        path: 'pricing',
        meta: { title: 'Cennik i punkty', breadcrumbs: [{ label: 'Cennik i punkty' }] },
        component: () => import('pages/PricingPage.vue')
      },
      {
        path: 'help',
        meta: { title: 'Pomoc / FAQ', breadcrumbs: [{ label: 'Pomoc / FAQ' }] },
        component: () => import('pages/HelpPage.vue')
      }
    ]
  },

  { path: '/:catchAll(.*)*', component: () => import('pages/ErrorNotFound.vue') }
]

export default routes
