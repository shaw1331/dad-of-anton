import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#000000",
          surface: "#0a0a0a",
          raised: "#111111",
          border: "rgba(255,255,255,0.06)",
          text: "#EDEDED",
          muted: "#888888",
        },
      },
    },
  },
  plugins: [],
};

export default config;
