import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b0f14',
        card: '#111827',
        accent: '#3b82f6',
        cyan: '#06b6d4',
        critical: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981'
      },
      borderRadius: {
        xl2: '1rem'
      }
    }
  },
  plugins: []
} satisfies Config;
