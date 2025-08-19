import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      // 字符串简写写法：'/foo' -> 'http://localhost:4567/foo'
      // 我们要代理所有以 /api 开头的请求
      '/api': {
        target: 'http://127.0.0.1:5000', // 目标是我们的后端服务
        changeOrigin: true, // 必须设置为 true
        // rewrite: (path) => path.replace(/^\/api/, '') // 如果后端接口没有/api前缀，需要重写路径
      }
    }
  }
})
