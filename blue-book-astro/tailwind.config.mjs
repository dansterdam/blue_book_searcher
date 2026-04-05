/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'dossier': {
          bg:           '#c8d8dc',   // Blue Book cover: pale blue-grey
          surface:      '#b8ccd2',   // slightly deeper blue-grey for cards
          border:       '#9ab4bc',   // medium blue-grey border
          amber:        '#7a4f18',   // deep amber/brown for light bg
          'amber-bright': '#5a3a10', // darker amber for headings
          green:        '#1e5c1e',
          'green-bright': '#156615',
          red:          '#9a2020',
          'red-bright': '#c02828',
          muted:        '#5a7278',   // blue-grey medium
          text:         '#1e2c30',   // near-black with blue tint
          'text-bright': '#0e1820',  // true near-black
        }
      },
      fontFamily: {
        display:    ['"Special Elite"', 'monospace'],
        typewriter: ['"Special Elite"', '"Courier New"', 'monospace'],
        mono:       ['"Source Code Pro"', '"Courier New"', 'monospace'],
        sans:       ['"Inter"', 'system-ui', 'sans-serif'],
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
