import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        deepNavy: '#020617',
        grey: '#64748b',
        midnightViolet: '#1e293b',
        onyx: '#020617',
        jetBlack: '#0f172a',
        brandAccent: '#8b5cf6',
        textSoft: '#e2e8f0'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif']
      }
    }
  },
  plugins: []
};

export default config;

