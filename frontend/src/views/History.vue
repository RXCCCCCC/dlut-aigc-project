<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const records = ref([])
const error = ref('')

const fetch = async () => {
  error.value = ''
  try {
    const res = await axios.get('/api/history')
    records.value = res.data
  } catch (e) {
    error.value = '无法加载历史记录'
  }
}

const remove = async (id) => {
  try {
    await axios.delete(`/api/history/${id}`)
    await fetch()
  } catch (e) {
    error.value = '删除失败'
  }
}

const download = (id) => {
  // 简单跳转到后端下载接口，会触发文件下载
  window.location.href = `/api/history/download/${id}`
}

onMounted(fetch)
</script>

<template>
  <div class="history-card">
    <h2>我的历史</h2>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="records.length === 0">暂无历史记录</div>
    <ul>
      <li v-for="r in records" :key="r.id">
        <div><strong>{{ r.prompt }}</strong></div>
        <div>{{ new Date(r.created_at).toLocaleString() }}</div>
        <div>
          <button @click="download(r.id)">下载模型</button>
          <button @click="remove(r.id)">删除</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.history-card{ max-width:800px; margin:2rem auto; padding:1rem; color:#fff }
li{ list-style:none; margin:8px 0; padding:8px; background: rgba(0,0,0,0.4); border-radius:6px }
button{ margin-right:8px }
.error{ color:#ff8080 }
</style>
