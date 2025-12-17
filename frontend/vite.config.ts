import vue from '@vitejs/plugin-vue'
import path from 'path'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
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
