import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// axios 默认基础路径
axios.defaults.baseURL = ''
// 如果本地有 token，默认带上
const token = localStorage.getItem('access_token')
if (token) {
	axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

const app = createApp(App)
app.use(router)
app.mount('#app')
