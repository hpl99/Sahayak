---
name: Voice for Livelihood
colors:
  surface: '#fbf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae8e7'
  surface-container-highest: '#e4e2e1'
  on-surface: '#1b1c1c'
  on-surface-variant: '#454652'
  inverse-surface: '#303030'
  inverse-on-surface: '#f3f0f0'
  outline: '#767683'
  outline-variant: '#c6c5d4'
  surface-tint: '#4c56af'
  primary: '#000666'
  on-primary: '#ffffff'
  primary-container: '#1a237e'
  on-primary-container: '#8690ee'
  inverse-primary: '#bdc2ff'
  secondary: '#5c5f61'
  on-secondary: '#ffffff'
  secondary-container: '#e0e3e5'
  on-secondary-container: '#626567'
  tertiary: '#2d1500'
  on-tertiary: '#ffffff'
  tertiary-container: '#4c2600'
  on-tertiary-container: '#df8017'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e0e0ff'
  primary-fixed-dim: '#bdc2ff'
  on-primary-fixed: '#000767'
  on-primary-fixed-variant: '#343d96'
  secondary-fixed: '#e0e3e5'
  secondary-fixed-dim: '#c4c7c9'
  on-secondary-fixed: '#191c1e'
  on-secondary-fixed-variant: '#444749'
  tertiary-fixed: '#ffdcc2'
  tertiary-fixed-dim: '#ffb77a'
  on-tertiary-fixed: '#2e1500'
  on-tertiary-fixed-variant: '#6d3a00'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e1'
typography:
  display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '400'
    lineHeight: 30px
  body-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  label-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style
The design system is rooted in the principles of **Institutional Professionalism** and **Radical Accessibility**. It is designed for "Voice for Livelihood," a public-service platform connecting citizens to skills and opportunities. The brand personality is dependable, authoritative, and inclusive, aiming to evoke a sense of security and civic duty.

The aesthetic follows a **Modern Corporate** approach with a focus on high-legibility and functional clarity. It deliberately avoids decorative trends like gradients, blurs, or heavy shadows to ensure performance on low-end devices and clarity for users with varying digital literacy. Visual hierarchy is established through clear information architecture and high-contrast color pairings rather than stylistic flourishes.

## Colors
The palette is built on a foundation of trust and visibility. 

- **Primary Navy (#1A237E):** Used for headers, primary actions, and institutional branding. It provides the "government" feel.
- **Secondary Light Gray (#F5F7F9):** The primary background color to reduce eye strain and provide a soft canvas for content.
- **Accent Saffron (#FF9933):** Used sparingly for highlighting key calls-to-action or status indicators that require attention without the alarm of red.
- **Semantic Colors:** Success Green and Error Red are strictly reserved for feedback loops to maintain their psychological impact.

All text-to-background combinations must meet WCAG AA standards at a minimum, with a preference for AAA in all body copy.

## Typography
This design system utilizes **Inter** for its exceptional legibility and neutral, systematic tone. The type scale is intentionally oversized to accommodate elderly users and those with visual impairments.

- **Headlines:** Use Bold (700) or Semi-Bold (600) to create clear section breaks.
- **Body Text:** Never drop below 18px for primary content. The line height is generous (1.5x) to prevent "crowding" of text, which aids users with lower literacy levels.
- **Captions:** Use sparingly. If the information is important, it should be in the `body-md` size.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy on desktop (max-width 1200px) to ensure reading lines do not become too long, and a **Fluid Grid** on mobile devices.

- **Grid:** A 12-column system is used for desktop, collapsing to 4 columns on mobile.
- **Rhythm:** An 8px linear scale governs all padding and margins. 
- **Vertical Rhythm:** Large "Stack" spacings (32px+) are encouraged between unrelated content blocks to provide visual breathing room and reduce cognitive load.
- **Touch Targets:** All interactive elements must have a minimum touch target size of 48x48px, regardless of their visual size.

## Elevation & Depth
In line with the serious, government-style aesthetic, this design system uses **Tonal Layering** rather than traditional shadows.

- **Level 0:** Background Surface (#F5F7F9).
- **Level 1:** Content Cards and Sections (#FFFFFF). These are defined by a subtle 1px border (#DDE3EA) rather than a shadow.
- **Level 2:** Active/Hover states. Use a very soft, diffused 10% opacity Navy shadow only when an element is interactive and hovered to provide tactile feedback.
- **Overlays:** Modals use a 40% Navy backdrop tint to focus the user's attention completely on the task at hand.

## Shapes
The shape language is **Soft** but structured. A 0.25rem (4px) base radius is used for most UI components (inputs, cards, small buttons). This provides a professional appearance that is modern without feeling overly "playful" or "childish," which might undermine the platform's authority.

- **Action Elements:** Primary buttons may use slightly more rounded corners (8px) to distinguish them from structural layout elements.
- **Icons:** Use thick-stroke (2px), unfilled icons to maintain high contrast and clarity.

## Components
Consistent component styling ensures the platform remains predictable for all users.

- **Buttons:** Large (minimum 56px height for primary). Primary buttons use Navy background with White text. Secondary buttons use a Navy outline. Action labels must be verbs (e.g., "Submit Application").
- **Voice Controls:** The microphone interface is a central component. It should be a large, circular Primary Navy button when inactive, and pulse with a Saffron (#FF9933) outer ring when active/listening.
- **Input Fields:** Use thick 2px borders for the default state. The label must always be visible above the field (no floating labels or placeholder-only labels).
- **Cards:** Cards are flat white with a 1px border. They should be used to group related information like job listings or skill modules. 
- **Feedback Indicators:** Success and Error messages appear as full-width bars (banners) at the top of content areas to ensure they are seen immediately by users with limited digital experience.
- **Breadcrumbs:** Essential for navigation in deep service structures, located directly below the main header.