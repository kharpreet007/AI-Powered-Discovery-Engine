---
name: Blinkit Discovery Engine
colors:
  surface: '#16130b'
  surface-dim: '#16130b'
  surface-bright: '#3d392f'
  surface-container-lowest: '#110e06'
  surface-container-low: '#1f1b12'
  surface-container: '#231f16'
  surface-container-high: '#2e2a20'
  surface-container-highest: '#39342a'
  on-surface: '#eae1d3'
  on-surface-variant: '#d1c5ae'
  inverse-surface: '#eae1d3'
  inverse-on-surface: '#343026'
  outline: '#9a907b'
  outline-variant: '#4e4634'
  surface-tint: '#edc13d'
  primary: '#ffebbc'
  on-primary: '#3d2e00'
  primary-container: '#f8cb46'
  on-primary-container: '#6e5600'
  inverse-primary: '#755b00'
  secondary: '#c6c6c7'
  on-secondary: '#2f3131'
  secondary-container: '#454747'
  on-secondary-container: '#b4b5b5'
  tertiary: '#cdf3ff'
  on-tertiary: '#003641'
  tertiary-container: '#64e0ff'
  on-tertiary-container: '#006274'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe08f'
  primary-fixed-dim: '#edc13d'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#584400'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#aeecff'
  tertiary-fixed-dim: '#58d6f5'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5d'
  background: '#16130b'
  on-background: '#eae1d3'
  surface-variant: '#39342a'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  card-gap: 20px
---

## Brand & Style
The design system for the Blinkit Discovery Engine evokes a sense of high-velocity intelligence and premium technical precision. It is built for a professional audience requiring real-time insights and decision-making capabilities. 

The aesthetic is a sophisticated evolution of **Glassmorphism**, merging high-tech utility with a luxury "dark mode" experience. The interface relies on deep spatial depth, utilizing frosted glass textures and vibrant background blurs to create a sense of multi-layered information architecture. The overall emotional response is one of clarity, speed, and state-of-the-art reliability.

## Colors
The palette is intentionally restricted to maintain a high-end, cinematic feel. 

- **Primary:** Blinkit Yellow (#F8CB46) is used sparingly as a high-contrast accent for interactive elements, critical data points, and active states.
- **Backgrounds:** A true Deep Black (#000000) provides the canvas, ensuring that glass effects and glow accents achieve maximum luminosity.
- **Surfaces:** Dark greys and translucent white overlays (10-15% opacity) create the "glass" containers.
- **Functional Colors:** Success, warning, and error states should utilize desaturated versions of their respective hues to avoid clashing with the primary yellow.

## Typography
This design system employs a dual-font strategy. **Outfit** is used for headings and display metrics to provide a geometric, modern, and slightly tech-forward personality. **Inter** is utilized for all body text, UI labels, and data tables to ensure maximum legibility and a systematic feel. 

Large display sizes should use tighter letter spacing to maintain a "locked-in" editorial look. Captions and small labels should utilize increased tracking and uppercase styling for better scannability against dark backgrounds.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a maximum content width of 1600px for desktop. It uses a base 8px rhythmic scale.

- **Desktop:** 12-column grid with 24px gutters. Dashboard modules should span 3, 4, 6, or 12 columns.
- **Tablet:** 8-column grid with 16px margins. Sidebars collapse into a compact icon-only rail.
- **Mobile:** 4-column grid with 16px margins. All glass cards stack vertically with 16px vertical spacing.

Layouts should prioritize "breathing room" around data visualizations, using generous padding (32px) within cards to maintain the premium feel.

## Elevation & Depth
Depth is created through transparency and refraction rather than traditional shadows. 

1.  **Base Layer:** Solid #000000.
2.  **Mantle Layer:** Subtle background blurs (32px - 64px) using low-opacity primary colors to create "blooms" of light behind active modules.
3.  **Glass Surface:** Semi-transparent white (rgba(255, 255, 255, 0.05)) with a `backdrop-filter: blur(20px)`.
4.  **Stroke:** Every glass card must have a 1px solid border at 10% white opacity to define its edges against the dark background.
5.  **Interactive Elevation:** When hovered, cards should increase their backdrop blur and the border opacity should shift to 25% white or 50% Primary Yellow.

## Shapes
The design system utilizes an aggressive rounding strategy to soften the high-tech aesthetic. 
- **Standard Cards:** Use `rounded-2xl` (1.5rem) for all main dashboard modules.
- **Inner Elements:** Buttons and input fields use `rounded-lg` (0.5rem) to provide a structural contrast to the larger cards.
- **Chat Bubbles:** Utilize asymmetric rounding; 1.5rem on three corners and 0.25rem on the anchor corner to signify the speaker.

## Components

### Metric Cards
Metric cards feature a large `headline-lg` value in White, with a small sparkline chart below it. A subtle "inner glow" of Primary Yellow (10% opacity) should emanate from the top-left corner of the card.

### Buttons
- **Primary:** Solid #F8CB46 with black text. No gradient.
- **Secondary:** Transparent glass with a 1px white border.
- **Tertiary/Ghost:** Text only, shifting to Primary Yellow on hover.

### Conversational Interface
The chat interface uses a streaming-ready layout. Responses appear in glass containers that slowly fade in. The typing indicator should be a subtle pulsing glow in Primary Yellow. Use `monospaced` fonts for any code snippets or raw data outputs within the chat.

### Progress Bars & Transitions
Progress bars consist of a dark, recessed track with a glowing Primary Yellow fill. Fill animations must use a `cubic-bezier(0.22, 1, 0.36, 1)` easing function to simulate a high-performance "engine" feel.

### Input Fields
Inputs are dark-themed with a subtle 1px border. On focus, the border transitions to Primary Yellow with a soft outer glow (`box-shadow: 0 0 12px rgba(248, 203, 70, 0.3)`).