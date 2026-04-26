import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        deepNavy: '#032258',
        grey: '#747779',
        midnightViolet: '#2a1c33',
        onyx: '#141515',
        jetBlack: '#192830',
        leafGreen: '#747779',
        softGreen: '#d7d9dc'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif']
      }
    }
  },
  plugins: []
};

export default config;
