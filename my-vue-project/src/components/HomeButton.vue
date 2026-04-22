<template>
<button class="home-button" @click="goHome" :title="$t('common.home')">
          <img class="home-button-image" :src="homeButtton" alt="Home" />
        </button>
</template>




<script setup lang="ts">


import homeButtton from '@/assets/imgs/home.webp';
import { useRouter } from 'vue-router';
const router = useRouter();

function goHome() {
  router.push('/main');
}

</script>
<style scoped>


.home-button {
    all: initial;
  background: var(--bg-card);
  border-radius: 20px;
  cursor: pointer;
  padding: 0;
  width: 45px;
  height: 45px;
    border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow);
  overflow: hidden;
}


.home-button:hover {
  background: var(--bg-card);
  box-shadow: var(--shadow-strong);
  border-color: var(--accent-color);
  transform: translateY(-1px);
}

.home-button-image {
  left: -1px;
  width: 40px;
  height: 40px;
  object-fit: contain;
  display: block;
    mask-size: contain;
  mask-position: center;
  mask-repeat: no-repeat;
  background-color: var(--primary-text);
}

.home-button:hover .home-button-image {
  transform: scale(1);
}
</style>