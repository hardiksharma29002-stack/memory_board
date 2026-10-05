import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--bg-canvas)",
        surface: "var(--bg-surface)",
        surfaceMuted: "var(--bg-surface-muted)",
        surfaceElevated: "var(--bg-surface-elevated)",
        textPrimary: "var(--text-primary)",
        textSecondary: "var(--text-secondary)",
        textTertiary: "var(--text-tertiary)",
        borderSubtle: "var(--border-subtle)",
        brand: {
          DEFAULT: "var(--primary)",
          soft: "var(--primary-soft)",
        },
        success: {
          DEFAULT: "var(--success)",
          soft: "var(--success-soft)",
        },
        warning: {
          DEFAULT: "var(--warning)",
          soft: "var(--warning-soft)",
        },
      },
      borderRadius: {
        card: "20px",
        tile: "12px",
        sheet: "28px",
      },
      boxShadow: {
        card: "var(--shadow-1)",
        sheet: "var(--shadow-2)",
      },
    },
  },
  plugins: [],
};
export default config;

