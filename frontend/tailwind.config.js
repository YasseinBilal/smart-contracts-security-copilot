/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0d1117',
        surface: '#161b22',
        border: '#30363d',
        text: '#c9d1d9',
        muted: '#8b949e',
        critical: '#ff4d4f',
        high: '#fa8c16',
        medium: '#fadb14',
        low: '#1677ff',
        info: '#8b949e',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
