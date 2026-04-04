/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'dossier': {
          bg: '#0a0c10',
          surface: '#0f1218',
          border: '#1e2535',
          amber: '#c8a45a',
          'amber-bright': '#f0c060',
          green: '#3a7a3a',
          'green-bright': '#4ecb4e',
          red: '#c0392b',
          'red-bright': '#e74c3c',
          muted: '#4a5568',
          text: '#a8b4c0',
          'text-bright': '#e2e8f0',
        }
      },
      fontFamily: {
        typewriter: ['"Special Elite"', '"Courier New"', 'monospace'],
        mono: ['"Source Code Pro"', '"Courier New"', 'monospace'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'grid-pattern': `
          linear-gradient(rgba(30,37,53,0.4) 1px, transparent 1px),
          linear-gradient(90deg, rgba(30,37,53,0.4) 1px, transparent 1px)
        `,
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      animation: {
        'flicker': 'flicker 3s infinite',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        flicker: {
          '0%, 100%': { opacity: '1' },
          '92%': { opacity: '1' },
          '93%': { opacity: '0.8' },
          '94%': { opacity: '1' },
          '96%': { opacity: '0.9' },
          '97%': { opacity: '1' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        }
      }
    },
  },
  plugins: [],
};
