import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cores do SER conforme identidade visual
        primary: {
          DEFAULT: '#366595', // Azul principal
          hover: '#2d5579',
          light: '#4a7db3',
        },
        yellow: {
          DEFAULT: '#f2cc2c', // Amarelo principal
          hover: '#d9b824',
        },
        green: {
          DEFAULT: '#56991f', // Verde principal
          hover: '#47801a',
        },
        background: '#fefffa', // Branco
        sidebar: {
          DEFAULT: '#f5f5f5',
          hover: '#e8e8e8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
