import vue from '@vitejs/plugin-vue'
import path from 'path'
import type { PluginOption } from 'vite'
import { defineConfig, loadEnv } from 'vite'
import vueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const plugins: PluginOption[] = [vue()]
  if (mode === 'development' && !process.env.CI) {
    try {
      plugins.push(vueDevTools())
    } catch (error) {
      console.warn('Vue DevTools plugin failed to load:', error.message)
    }
  }
  return {
    plugins,
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      open: true,
      proxy: {
        '/api': {
          target: env.API_PROXY_TARGET,
          changeOrigin: true
          // 如果后端接口没有 /api 前缀，取消下面注释
          // rewrite: (path) => path.replace(/^\/api/, ''),
        }
      }
    }
  }
})
