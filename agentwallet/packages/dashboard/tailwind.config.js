/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // local.ai-inspired brand: emerald green scale (#00bb7f core)
        brand: {
          50: "#e6fbf3",
          100: "#c3f4e2",
          200: "#8beac9",
          300: "#4ddcac",
          400: "#1fce95",
          500: "#00bb7f",
          600: "#009767",
          700: "#007a54",
          800: "#005c40",
          900: "#003d2b",
          950: "#001f16",
        },
        // local.ai warm near-black neutrals
        ink: {
          950: "#0f0e0c",
          900: "#161513",
          800: "#22201e",
          700: "#272522",
          600: "#3a3733",
          500: "#6b675f",
          400: "#8a867e",
          300: "#c9c5bd",
          200: "#d6d2ca",
          100: "#efeeeb",
        },
      },
      fontFamily: {
        sans: ["Geist Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        mono: ["Geist Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        DEFAULT: "2px",
        lg: "2px",
        md: "2px",
        sm: "1px",
      },
    },
  },
  plugins: [],
};
