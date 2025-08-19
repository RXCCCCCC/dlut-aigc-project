<script setup>
import GeneratorInput from './components/GeneratorInput.vue'
</script>

<template>
  <main>
    <GeneratorInput />
  </main>
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
