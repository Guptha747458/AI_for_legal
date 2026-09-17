/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            color: '#334155',
            'h1, h2, h3, h4': { color: '#1e293b' },
            'a': { color: '#2563eb', 'text-decoration': 'none' },
          },
        },
      },
    },
  },
  plugins: [],
}