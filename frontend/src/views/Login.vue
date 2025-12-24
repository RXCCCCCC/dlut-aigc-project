<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')

const submit = async () => {
  error.value = ''
  try {
    const res = await axios.post('/api/auth/login', { username: username.value, password: password.value })
    const token = res.data.access_token
    localStorage.setItem('access_token', token)
    localStorage.setItem('username', res.data.username || username.value)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    router.push({ name: 'Home' })
  } catch (e) {
    error.value = e.response?.data?.msg || '登录失败'
  }
}
</script>

<template>
  <div class="auth-card">
    <h2>登录</h2>
    <div>
      <input v-model="username" placeholder="用户名" />
    </div>
    <div>
      <input type="password" v-model="password" placeholder="密码" />
    </div>
    <div>
      <button @click="submit">登录</button>
      <router-link to="/register">去注册</router-link>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<style scoped>
.auth-card { max-width: 400px; margin: 4rem auto; padding: 2rem; background: rgba(0,0,0,0.6); border-radius:8px; color: #fff }
input { width:100%; padding:8px; margin:6px 0 }
button { padding:8px 16px }
.error { color: #ff8080 }
</style>
