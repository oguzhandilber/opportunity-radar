/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base Dark Mode
        darkest: "#0a0e14",
        dark: "#151a23",
        medium: "#1e242e",
        light: "#2a313d",

        // Text colors
        "text-primary": "#e6eaf0",
        "text-secondary": "#8892a6",
        "text-tertiary": "#5c6370",

        // Signal System (Accents)
        radar: {
          400: "#00cc6a",
          500: "#00ff88",
          600: "#00dd77",
        },
        signal: {
          critical: "#ff0055",
          warning: "#ffaa00",
          success: "#00ff88",
          info: "#00ccff",
          violet: "#aa00ff",
        },

        // Legacy primary for compatibility
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#00ff88",
          600: "#00dd77",
          700: "#00bb66",
          800: "#009955",
          900: "#007744",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        display: ["Space Mono", "monospace"],
        body: ["Inter Tight", "sans-serif"],
      },
      animation: {
        "radar-pulse": "radar-pulse 2s ease-out infinite",
        "scan-in": "scan-in 0.3s ease-out forwards",
        "count-up": "count-up 0.8s steps(20) forwards",
        flash: "flash 0.15s ease-out",
      },
      keyframes: {
        "radar-pulse": {
          "0%": { transform: "scale(0.8)", opacity: "0.8" },
          "50%": { transform: "scale(1.2)", opacity: "0.4" },
          "100%": { transform: "scale(0.8)", opacity: "0.8" },
        },
        "scan-in": {
          "0%": { transform: "translateX(-20px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        "count-up": {
          "0%": { opacity: "0.5" },
          "100%": { opacity: "1" },
        },
        flash: {
          "0%": { opacity: "1" },
          "50%": { opacity: "0.5" },
          "100%": { opacity: "1" },
        },
      },
      backgroundImage: {
        scanlines:
          "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255,255,255,0.02) 3px, rgba(255,255,255,0.02) 4px)",
        "dot-grid":
          "radial-gradient(circle, rgba(255,255,255,0.03) 1px, transparent 1px)",
        "diagonal-stripes":
          "repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 11px)",
      },
      backgroundSize: {
        "dot-grid": "16px 16px",
      },
    },
  },
  plugins: [],
};
