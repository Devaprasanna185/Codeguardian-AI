export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      colors: {
        ink: { 950: "#0a1220", 900: "#0f1a2e", 800: "#16233b", 700: "#22334f", 500: "#6b7f9f", 300: "#aebbd0", 100: "#e8eef7" },
        guard: { DEFAULT: "#7c9cff", dark: "#5878e6" },
      },
    },
  },
  plugins: [],
};
