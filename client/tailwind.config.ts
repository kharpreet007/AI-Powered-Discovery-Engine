import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "surface-container-high": "#2e2a20",
        "on-surface": "#eae1d3",
        "on-surface-variant": "#d1c5ae",
        "on-background": "#eae1d3",
        "on-primary-fixed": "#241a00",
        "primary-container": "#f8cb46",
        "tertiary-fixed": "#aeecff",
        "tertiary-container": "#64e0ff",
        "on-secondary-container": "#b4b5b5",
        "on-error-container": "#ffdad6",
        "tertiary-fixed-dim": "#58d6f5",
        "secondary-container": "#454747",
        "error-container": "#93000a",
        "outline-variant": "#4e4634",
        "on-tertiary-fixed-variant": "#004e5d",
        "on-tertiary-fixed": "#001f26",
        "on-primary": "#3d2e00",
        "inverse-primary": "#755b00",
        "surface-tint": "#edc13d",
        "secondary-fixed": "#e2e2e2",
        "on-secondary-fixed": "#1a1c1c",
        "surface-variant": "#39342a",
        "surface-container-lowest": "#110e06",
        "surface-bright": "#3d392f",
        "tertiary": "#cdf3ff",
        "on-primary-fixed-variant": "#584400",
        "secondary": "#c6c6c7",
        "primary": "#ffebbc",
        "surface-container-low": "#1f1b12",
        "surface": "#16130b",
        "error": "#ffb4ab",
        "secondary-fixed-dim": "#c6c6c7",
        "on-tertiary-container": "#006274",
        "primary-fixed": "#ffe08f",
        "surface-container": "#231f16",
        "on-secondary-fixed-variant": "#454747",
        "on-secondary": "#2f3131",
        "inverse-surface": "#eae1d3",
        "surface-container-highest": "#39342a",
        "on-error": "#690005",
        "on-tertiary": "#003641",
        "primary-fixed-dim": "#edc13d",
        "background": "#16130b",
        "inverse-on-surface": "#343026",
        "outline": "#9a907b",
        "on-primary-container": "#6e5600",
        "surface-dim": "#16130b"
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "card-gap": "20px",
        "container-padding": "32px",
        "gutter": "24px",
        "unit": "8px"
      },
      fontFamily: {
        "body-lg": ["Inter", "sans-serif"],
        "label-caps": ["Inter", "sans-serif"],
        "display-lg": ["Outfit", "sans-serif"],
        "headline-lg-mobile": ["Outfit", "sans-serif"],
        "body-sm": ["Inter", "sans-serif"],
        "headline-lg": ["Outfit", "sans-serif"],
        "title-md": ["Outfit", "sans-serif"],
        "mono": ["JetBrains Mono", "monospace"]
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
export default config;
