import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark' | 'system'

const THEME_KEY = 'theme'

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'dark'
}

function applyTheme(theme: Theme) {
  const html = document.documentElement
  const body = document.body
  const effectiveTheme = theme === 'system' ? getSystemTheme() : theme
  
  if (effectiveTheme === 'dark') {
    html.classList.add('dark')
    body.setAttribute('arco-theme', 'dark')
  } else {
    html.classList.remove('dark')
    body.removeAttribute('arco-theme')
  }
}

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>((localStorage.getItem(THEME_KEY) as Theme) || 'system')

  function setTheme(newTheme: Theme) {
    theme.value = newTheme
    localStorage.setItem(THEME_KEY, newTheme)
    applyTheme(newTheme)
  }

  function initTheme() {
    applyTheme(theme.value)
    
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        if (theme.value === 'system') {
          applyTheme('system')
        }
      }
      
      mediaQuery.addEventListener('change', handleChange)
      
      watch(theme, (newTheme) => {
        applyTheme(newTheme)
      })
    }
  }

  return {
    theme,
    setTheme,
    initTheme
  }
})