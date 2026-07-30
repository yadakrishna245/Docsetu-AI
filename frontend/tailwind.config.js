/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6e6f2',
          100: '#b3b3d9',
          200: '#8080bf',
          300: '#4d4da6',
          400: '#26268c',
          500: '#000080',
          600: '#000073',
          700: '#000066',
          800: '#000059',
          900: '#00004d',
        },
        saffron: {
          50: '#fff5e6',
          100: '#ffe0b3',
          200: '#ffcc80',
          300: '#ffb84d',
          400: '#ffa826',
          500: '#FF9933',
          600: '#e68a2e',
          700: '#cc7a29',
          800: '#b36b24',
          900: '#995c1f',
        },
        india: {
          green: '#138808',
          white: '#FFFFFF',
          navy: '#000080',
          saffron: '#FF9933',
        },
        dark: {
          bg: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          text: '#e2e8f0',
          muted: '#94a3b8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};
