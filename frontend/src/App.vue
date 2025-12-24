<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref(localStorage.getItem('username') || '')

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('username')
  delete window.axiosDefaults
  username.value = ''
  router.push({ name: 'Login' })
}
</script>

<template>
  <div id="app">
    <header class="topnav">
      <div class="brand">DLUT AIGC</div>
      <nav>
        <router-link to="/">生成</router-link>
        <router-link to="/history">历史</router-link>
        <span v-if="localStorage.getItem('username')">{{ localStorage.getItem('username') }}</span>
        <button v-if="localStorage.getItem('access_token')" @click="logout">登出</button>
        <router-link v-else to="/login">登录</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
body {
  /* 设置一个从深蓝到紫色的柔和渐变背景 */
  background: linear-gradient(135deg, #1e2a4a 0%, #3b2a53 100%);
  color: #f0f0f0; /* 将默认文字颜色改为浅色 */
  font-family: 'M PLUS Rounded 1c', sans-serif; /* 应用我们引入的字体 */
  min-height: 100vh;
}
#app {
  display: flex;
  justify-content: center;
  padding: 2rem;
}
</style>
