/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        barrio: {
          bg: "#0a0e14",
          panel: "#131a24",
          border: "#1f2a3a",
          accent: "#22c55e",
          gold: "#facc15",
          danger: "#ef4444",
          muted: "#64748b",
          text: "#e2e8f0",
        },
      },
      fontFamily: {
        display: ["Bebas Neue", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
