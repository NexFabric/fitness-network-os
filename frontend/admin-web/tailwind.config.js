/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0D9488',
          deep: '#0F766E',
          light: '#14B8A6',
        },
        ink: '#0B1220',
        surface: '#F4F6F8',
        accent: {
          DEFAULT: '#34D399',
          warn: '#F59E0B',
          danger: '#DC2626',
        },
      },
      fontFamily: {
        sans: [
          '"DM Sans"',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      borderRadius: {
        card: '12px',
        control: '8px',
      },
      boxShadow: {
        card: '0 1px 2px rgb(0 0 0 / 0.05)',
        elevated: '0 4px 24px rgb(11 18 32 / 0.08), 0 1px 2px rgb(0 0 0 / 0.04)',
      },
    },
  },
  plugins: [],
}
