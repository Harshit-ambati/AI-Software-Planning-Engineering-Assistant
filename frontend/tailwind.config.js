/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#17202A",
        panel: "#F6F7F9",
        line: "#D8DEE7",
        signal: "#2563EB",
        success: "#15803D",
        caution: "#B45309",
      },
    },
  },
  plugins: [],
};

