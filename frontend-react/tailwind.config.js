/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        beige: {
          50: '#fdfcfa',
          100: '#faf8f3',
          200: '#f5f1e8',
          300: '#e8e3d6',
          400: '#d4cbb8',
          500: '#c0b49a',
          600: '#a89080',
          700: '#8b7355',
          800: '#6b5744',
          900: '#4a3d2f',
        },
        accent: {
          50: '#f0ede8',
          100: '#e1dbd1',
          200: '#c3b7a3',
          300: '#a89080',
          400: '#8b7355',
          500: '#6b5744',
          600: '#5a4938',
          700: '#4a3d2f',
          800: '#3a3024',
          900: '#2a231a',
        },
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        display: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
