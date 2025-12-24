import { createRouter, createWebHistory } from 'vue-router'
import GeneratorInput from '../components/GeneratorInput.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import History from '../views/History.vue'

const routes = [
  { path: '/', name: 'Home', component: GeneratorInput, meta: { requiresAuth: true } },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/history', name: 'History', component: History, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
