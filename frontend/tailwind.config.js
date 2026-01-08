/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        google: {
          gray: '#f1f3f4',
          blue: '#1a73e8',
          text: '#3c4043',
        }
      }
    },
  },
  plugins: [],
}
