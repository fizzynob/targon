/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        apple: {
          bg: '#FBFBFD',
          sidebar: '#F5F5F7',
          card: '#FFFFFF',
          blue: '#0071E3',
          blueHover: '#0077ED',
          text: '#1D1D1F',
          secondary: '#86868B',
          border: '#E5E5EA',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"Inter"',
          '"Segoe UI"',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        apple: '0 4px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        appleHover: '0 14px 36px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
        appleModal: '0 24px 64px rgba(0, 0, 0, 0.14), 0 4px 16px rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [],
};
