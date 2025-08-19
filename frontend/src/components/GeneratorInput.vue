<script setup>
// 导入Vue的响应式API和工具函数
import { ref, nextTick } from 'vue'
// 导入axios用于与后端通信
import axios from 'axios'
// 导入three.js及其GLTF加载器和轨道控制器，用于3D模型渲染
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// -------------------- 核心状态变量定义 --------------------
// 文本输入框内容
const textInput = ref('');
// 图片文件对象
const imageFile = ref(null);
// 音频Blob对象（录音）
const audioBlob = ref(null);
// 是否正在加载（生成中）状态
const isLoading = ref(false);
// 错误消息
const errorMsg = ref('');
// 3D模型文件URL
const modelUrl = ref('');
// 2D预览图URL
const previewImageUrl = ref('');
// 本地图片预览URL
const imagePreviewUrl = ref('');
// 3D渲染canvas容器引用
const canvasContainer = ref(null);
// 是否正在录音
const isRecording = ref(false);
// 录音器实例
let mediaRecorder = null;
// 录音数据块数组
let audioChunks = [];

// -------------------- 文件和音频处理函数 --------------------
/**
 * 处理图片上传事件，生成本地预览图
 * @param {Event} event - 文件选择事件
 */
const handleImageUpload = (event) => {
  const file = event.target.files[0];
  if (!file) {
    imageFile.value = null;
    imagePreviewUrl.value = '';
    return;
  }
  imageFile.value = file;
  // 使用FileReader生成本地预览图
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreviewUrl.value = e.target.result;
  };
  reader.readAsDataURL(file);
};

/**
 * 切换录音状态（开始/停止录音）
 * 录音结束后生成音频Blob对象
 */
const toggleRecording = async () => {
  if (isRecording.value) {
    // 停止录音
    mediaRecorder.stop();
    isRecording.value = false;
    console.log('录音结束');
  } else {
    // 开始录音
    try {
      // 1. 获取麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // 2. 创建MediaRecorder实例
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = []; // 清空之前的录音块
      // 3. 收集音频数据
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      // 4. 停止时合成Blob对象
      mediaRecorder.onstop = () => {
        audioBlob.value = new Blob(audioChunks, { type: 'audio/wav' });
        console.log('录音文件已生成:', audioBlob.value);
        // 停止媒体流，关闭麦克风指示灯
        stream.getTracks().forEach(track => track.stop());
      };
      // 5. 开始录制并更新状态
      mediaRecorder.start();
      isRecording.value = true;
      console.log('录音开始...');
    } catch (error) {
      console.error('无法获取麦克风权限:', error);
      alert('无法获取麦克风权限，请检查浏览器设置。');
    }
  }
};

// -------------------- 3D模型渲染函数 --------------------
/**
 * 初始化three.js场景并加载3D模型
 * @param {string} tencentModelUrl - 腾讯云返回的模型URL
 */
const initAndLoadModel = (tencentModelUrl) => {
  const canvas = canvasContainer.value;
  if (!canvas) return;

  // 清理之前的场景，防止模型重叠
  while (canvas.firstChild) {
    canvas.removeChild(canvas.firstChild);
  }

  // 创建three.js场景、相机和渲染器
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xeeeeee);
  const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);

  // 添加环境光和方向光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
  scene.add(ambientLight);
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(5, 10, 7.5).normalize();
  scene.add(directionalLight);

  // 添加轨道控制器，支持鼠标旋转缩放
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; // 拖动更平滑

  const loader = new GLTFLoader();

  // 构造后端代理URL，避免跨域和临时URL失效
  const proxyUrl = `/api/model-proxy?url=${encodeURIComponent(tencentModelUrl)}`;
  console.log("前端将通过代理URL加载模型:", proxyUrl);

  // 加载3D模型
  loader.load(proxyUrl, (gltf) => {
    // 加载成功后自动缩放和居中模型
    const model = gltf.scene;
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    model.position.sub(center);
    const maxDim = Math.max(size.x, size.y, size.z);
    const desiredSize = 4;
    const scale = desiredSize / maxDim;
    model.scale.set(scale, scale, scale);
    camera.position.set(0, size.y * scale * 0.5, size.z * scale * 1.5);
    controls.target.set(0, size.y * scale * 0.5, 0);
    scene.add(model);
  }, undefined, (error) => {
    // 加载失败处理
    console.error('通过代理加载3D模型出错:', error);
    errorMsg.value = '3D模型加载失败，代理服务可能出错。';
  });

  // 动画循环渲染
  const animate = () => {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();
};

// -------------------- 数据提交函数 --------------------
/**
 * 向后端提交文本、图片（和音频）数据，获取生成的3D模型和预览图
 */
const submitData = async () => {
  // 清理状态
  errorMsg.value = '';
  modelUrl.value = '';
  previewImageUrl.value = '';
  isLoading.value = true;

  // 构造FormData对象
  const formData = new FormData();
  if (textInput.value) formData.append('text', textInput.value);
  if (imageFile.value) formData.append('image', imageFile.value);
  // 语音暂不处理
  // if (audioBlob.value) formData.append('audio', audioBlob.value, 'user_recording.wav');

  try {
    // 向后端发送POST请求
    const response = await axios.post('/api/generate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    console.log('后端返回成功:', response.data);

    // 赋值模型和预览图URL
    modelUrl.value = response.data.modelUrl;
    previewImageUrl.value = response.data.previewImageUrl;

    // 有模型URL时渲染3D模型
    if (modelUrl.value) {
      await nextTick();
      initAndLoadModel(modelUrl.value);
    }

  } catch (error) {
    // 错误处理
    console.error('请求后端出错了:', error);
    errorMsg.value = '生成失败了，请检查网络或联系我们。';
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="creation-station">
    <!-- 顶部标题区 -->
    <header class="station-header">
      <h1>模型创造台 ✨</h1>
      <p>将你的文字或图片，变为独一无二的3D模型</p>
    </header>

    <!-- 输入卡片区 -->
    <div class="input-card">
      <!-- 文本输入 -->
      <div class="input-group">
        <label for="text-prompt">1. 输入你的想法（文字描述）</label>
        <textarea id="text-prompt" v-model="textInput" placeholder="例如：一个漂浮在云端的魔法图书馆..."></textarea>
      </div>

      <!-- 图片上传 -->
      <div class="input-group">
        <label>2. 上传参考图片（可选）</label>
        <label for="image-upload" class="custom-file-upload">
          {{ imageFile ? imageFile.name : '选择图片' }}
        </label>
        <input id="image-upload" type="file" @change="handleImageUpload" accept="image/*">

        <!-- 图片本地预览 -->
        <div v-if="imagePreviewUrl" class="image-preview-container">
          <img :src="imagePreviewUrl" alt="图片预览" class="image-preview">
        </div>
      </div>
    </div>

    <!-- 提交按钮区 -->
    <div class="submit-section">
      <button @click="submitData" :disabled="isLoading" class="generate-button">
        <span v-if="isLoading" class="spinner"></span>
        <span>{{ isLoading ? '正在咏唱咒语...' : '开始生成！' }}</span>
      </button>
    </div>

    <!-- 加载提示 -->
    <transition name="fade">
      <div v-if="isLoading" class="status-card loading-tip">
        <p>AI正在解析你的想法，请稍等片刻...</p>
        <div class="progress-bar"></div>
      </div>
    </transition>

    <!-- 结果展示区 -->
    <transition name="fade">
      <div v-if="modelUrl || previewImageUrl" class="status-card result-section">
        <h3>生成成功！</h3>
        <div class="result-display">
          <!-- 2D预览图 -->
          <div class="preview-container">
            <h4>2D预览图</h4>
            <img v-if="previewImageUrl" :src="previewImageUrl" alt="生成的模型预览图" class="preview-image">
            <p v-else>暂无2D预览图</p>
          </div>
          <!-- 3D交互预览 -->
          <div class="canvas-container">
            <h4>3D交互预览</h4>
            <canvas ref="canvasContainer" class="model-canvas"></canvas>
          </div>
        </div>
        <!-- 下载按钮 -->
        <div class="download-section">
          <a v-if="modelUrl" :href="modelUrl" :download="`model_${Date.now()}.glb`" class="download-button">
            下载3D模型 (.GLB)
          </a>
          <p v-else>无有效的模型文件可供下载</p>
        </div>
      </div>
    </transition>

    <!-- 错误提示区 -->
    <transition name="fade">
      <div v-if="errorMsg" class="status-card error-section">
        <h3>出错了！</h3>
        <p>{{ errorMsg }}</p>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* 整体布局样式：居中、卡片风格、背景模糊等 */
.creation-station {
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: center;
}

.station-header {
  text-align: center;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.station-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #fff;
}

.station-header p {
  font-size: 1.1rem;
  color: #c0c0ff;
}

.input-card {
  width: 100%;
  max-width: 600px;
  background: rgba(40, 42, 60, 0.7);
  border: 1px solid rgba(132, 118, 255, 0.4);
  border-radius: 16px;
  padding: 2.5rem;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  gap: 3rem;
  align-items: center;
}

.input-group {
  width: 90%;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #c0c0ff;
}

textarea, .custom-file-upload {
  width: 100%;
  background: rgba(23, 24, 39, 0.8);
  border: 1px solid rgba(132, 118, 255, 0.4);
  border-radius: 8px;
  padding: 12px;
  color: #f0f0f0;
  font-family: inherit;
  font-size: 1rem;
  transition: all 0.3s ease;
}

textarea:focus, input[type="file"]:focus + .custom-file-upload {
  outline: none;
  border-color: #a89fff;
  box-shadow: 0 0 0 3px rgba(132, 118, 255, 0.3);
}
textarea::-webkit-scrollbar {
  width: 8px;
}
textarea::-webkit-scrollbar-track {
  background: rgba(23, 24, 39, 0.8);
  border-radius: 10px;
}
textarea::-webkit-scrollbar-thumb {
  background-color: #5344d9;
  border-radius: 10px;
  border: 2px solid rgba(23, 24, 39, 0.8);
}
textarea::-webkit-scrollbar-thumb:hover {
  background-color: #8476ff;
}
/* 隐藏原始的文件上传按钮 */
input[type="file"] {
  display: none;
}
.custom-file-upload {
  display: inline-block;
  cursor: pointer;
  text-align: center;
}
.custom-file-upload:hover {
  background: rgba(40, 42, 60, 0.9);
}
/* 图片预览容器样式，居中显示 */
.image-preview-container {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}
.image-preview {
  max-width: 100%;
  max-height: 250px;
  border-radius: 8px;
  border: 1px solid rgba(132, 118, 255, 0.4);
  object-fit: contain;
  background-color: rgba(0, 0, 0, 0.2);
}
.submit-section {
  text-align: center;
}

.generate-button {
  padding: 15px 30px;
  font-size: 1.2rem;
  font-weight: bold;
  color: #fff;
  background: linear-gradient(45deg, #8476ff, #5344d9);
  border: none;
  border-radius: 50px;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(83, 68, 217, 0.5);
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.generate-button:disabled {
  background: #555;
  cursor: not-allowed;
  box-shadow: none;
}

.generate-button:not(:disabled):hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(83, 68, 217, 0.7);
}

/* 加载中的小圈圈动画 */
.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 加载提示的进度条动画 */
.progress-bar {
  width: 100%;
  height: 4px;
  background-color: rgba(132, 118, 255, 0.3);
  border-radius: 2px;
  margin-top: 1rem;
  overflow: hidden;
}
.progress-bar::after {
  content: '';
  display: block;
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, #8476ff, #a89fff);
  border-radius: 2px;
  animation: progress-indeterminate 1.5s ease-in-out infinite;
}
@keyframes progress-indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(250%); }
}

/* 结果展示区样式 */
.result-display {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}
.preview-container, .canvas-container {
  flex: 1;
  min-width: 300px;
}
.preview-image, .model-canvas {
  width: 100%;
  height: 350px;
  border: 1px solid rgba(132, 118, 255, 0.4);
  border-radius: 12px;
}
.download-section {
  margin-top: 1.5rem;
  text-align: center;
}
.download-button {
  padding: 10px 20px;
  font-size: 1rem;
  font-weight: bold;
  color: #fff;
  background: linear-gradient(45deg, #28a745, #218838);
  border: none;
  border-radius: 50px;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
}
.download-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(40, 167, 69, 0.6);
}

.error-section {
  color: #ff7b7b;
  border-color: #ff7b7b;
}

/* 过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
