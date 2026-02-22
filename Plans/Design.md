# ReasonFlow Frontend — Complete Design Overhaul

You are redesigning the **ReasonFlow** frontend — an autonomous inbox AI agent SaaS product built with Next.js 16, Tailwind CSS 4, shadcn/ui (new-york style), Framer Motion, Recharts, and Lucide icons. The current UI was AI-generated and looks generic. Your job is to make it look like it was designed by the team behind Gumloop, Sarvam.ai, or Linear — deliberate, polished, distinctive.

---

## SECTION 0 — DESIGN PHILOSOPHY

ReasonFlow is an **AI email agent** for professionals. The aesthetic must feel:
- **Engineered, not decorated** — every gradient, shadow, and animation earns its place
- **Calm authority** — this handles your inbox, it should feel trustworthy and composed
- **Alive but not hyper** — subtle motion that signals intelligence, not a toy

### Reference DNA (synthesize, don't clone):
- **Gumloop**: Dark, information-dense feature cards with interactive product previews inside them. Each feature section IS a mini-product demo, not just an icon + text. Workflow step animations. Coral/pink accents on near-black. Bento grid layouts.
- **Sarvam.ai**: Premium editorial spacing. Warm accent color (orange-amber). Scroll-triggered reveals. Tabbed product demos ("See it in action" section). Security badge grids. Clean deployment cards.
- **Relay.app**: Friendly but professional. Soft pastel gradients. Step-by-step wizard with numbered circles. Testimonial cards with avatars and company logos. Rounded, approachable UI.
- **Stack.ai**: Enterprise workflow builder visualization. Numbered feature cards. Integration logo marquee. Tab-based showcases. Structured CTA forms.
- **Linear**: Sublime polish. Keyboard shortcuts. Monospace accents. Understated motion.

### The Anti-Slop Rules — NEVER DO THESE:
1. **NO purple gradient on white background** — the #1 AI slop fingerprint
2. **NO Inter, Roboto, Arial, or system fonts** as the primary typeface
3. **NO generic 3-column card grids** with icon + title + description and nothing else
4. **NO excessive glassmorphism** — max 1-2 glass elements per page (nav bar is fine, don't glass everything)
5. **NO rainbow badge soup** — each color needs a semantic reason
6. **NO cookie-cutter empty states** — make them feel designed
7. **NO `opacity-[0.03]` dot patterns everywhere** — one subtle background effect is enough
8. **NO stacking 3+ background layers** (current code has bg-page + bg-dot-pattern + bg-aurora — pick ONE sophisticated background)
9. **NO "Powered by X" badges in the hero** — tacky on a product landing page

---

## SECTION 1 — EXISTING PROJECT CONTEXT

### Tech Stack (DO NOT change these — work within them):
- Next.js 16.1.6 (App Router)
- React 19.2.3
- Tailwind CSS 4 with `@tailwindcss/postcss`
- shadcn/ui (new-york style, neutral base, Lucide icons) — config at `components.json`
- Framer Motion 12.x (USE THIS for all animations)
- Recharts 3.x (for charts)
- Lucide React icons
- TanStack React Query 5.x
- Zustand 5.x (installed but stores are empty — wire if needed)
- next-themes (installed but NOT wired — you must wire it)
- Axios with JWT interceptors at `src/lib/api.ts`
- `cn()` utility at `src/lib/utils.ts` (clsx + tailwind-merge)

### REMOVE these unused dependencies:
- `gsap` and `@gsap/react` — installed but never imported in any component. Remove from `package.json`

### Installed shadcn/ui components (`src/components/ui/`):
badge, button, card, collapsible, dialog, dropdown-menu, input, label, select, separator, sheet, sonner (toaster), table, tabs, textarea

### ADD these shadcn components (install via `npx shadcn@latest add <name>`):
tooltip, avatar, progress, skeleton, switch, popover, scroll-area, alert, toggle, command

---

## SECTION 2 — TYPOGRAPHY

Replace Inter entirely. Use Google Fonts loaded via `next/font/google` in `src/app/layout.tsx`.

**Font Pairing — Pick ONE of these pairs:**

| Option | Display (headings) | Body (text) | Personality |
|--------|-------------------|-------------|-------------|
| A | **Plus Jakarta Sans** (700, 800) | **Plus Jakarta Sans** (400, 500, 600) | Clean geometric, modern SaaS |
| B | **Outfit** (600, 700, 800) | **DM Sans** (400, 500) | Friendly but professional |
| C | **Sora** (600, 700) | **DM Sans** (400, 500) | Futuristic, tech-forward |
| D | **Clash Display** (local/CDN) | **General Sans** (local/CDN) | Premium editorial, Linear-like |

**Implementation:**
```tsx
// src/app/layout.tsx
import { Plus_Jakarta_Sans } from "next/font/google";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  weight: ["400", "500", "600", "700", "800"],
});

// In <html>: className={`${jakarta.variable}`}
// In tailwind: font-family defaults to the variable
```

**Typography Scale:**
- Hero headline: `text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]`
- Page title (h1): `text-3xl font-bold tracking-tight`
- Section heading (h2): `text-2xl font-semibold tracking-tight`
- Card title (h3): `text-lg font-semibold`
- Body: `text-base font-normal leading-relaxed` (16px)
- Small/caption: `text-sm text-muted-foreground`
- Monospace accents (timestamps, IDs, JSON): Use `font-mono` with system monospace

---

## SECTION 3 — COLOR SYSTEM

Replace BOTH the HSL and OKLCH color systems in `globals.css` with ONE unified system. Use HSL for consistency with shadcn.

### Light Mode Palette:
```css
:root {
  /* Core */
  --background: 0 0% 99%;           /* #FDFDFD — not pure white, slightly warm */
  --foreground: 224 71% 4%;          /* #020617 — slate-950 */
  --card: 0 0% 100%;
  --card-foreground: 224 71% 4%;

  /* Brand — Deep indigo-blue (NOT generic blue, NOT purple) */
  --primary: 234 89% 54%;            /* #2D3FE0 — electric indigo */
  --primary-foreground: 0 0% 100%;

  /* Surfaces */
  --secondary: 220 14% 96%;          /* #F3F4F6 */
  --secondary-foreground: 220 9% 46%;
  --muted: 220 14% 96%;
  --muted-foreground: 220 9% 46%;
  --accent: 234 89% 97%;             /* Light tint of primary */
  --accent-foreground: 234 89% 40%;

  /* Feedback */
  --destructive: 0 72% 51%;
  --destructive-foreground: 0 0% 100%;

  /* Borders & inputs */
  --border: 220 13% 91%;
  --input: 220 13% 91%;
  --ring: 234 89% 54%;
  --radius: 0.625rem;

  /* Chart palette — harmonious, not random */
  --chart-1: 234 89% 54%;   /* Primary indigo */
  --chart-2: 160 84% 39%;   /* Emerald */
  --chart-3: 346 77% 50%;   /* Rose */
  --chart-4: 38 92% 50%;    /* Amber */
  --chart-5: 262 83% 58%;   /* Violet */
}
```

### Dark Mode Palette:
```css
.dark {
  --background: 224 71% 4%;          /* #020617 — slate-950 */
  --foreground: 210 20% 98%;         /* #F8FAFC */
  --card: 222 47% 8%;                /* Elevated surface */
  --card-foreground: 210 20% 98%;

  --primary: 234 89% 67%;            /* Brighter indigo for dark bg */
  --primary-foreground: 0 0% 100%;

  --secondary: 217 33% 12%;
  --secondary-foreground: 210 20% 87%;
  --muted: 217 33% 12%;
  --muted-foreground: 215 20% 65%;
  --accent: 234 50% 15%;
  --accent-foreground: 234 89% 80%;

  --destructive: 0 62% 60%;
  --destructive-foreground: 0 0% 100%;

  --border: 217 33% 15%;
  --input: 217 33% 15%;
  --ring: 234 89% 67%;
}
```

### Accent Colors for Features (use as utility classes):
```
Inbox — Blue: from-blue-500 to-blue-600
Drafts — Rose: from-rose-500 to-rose-600
Calendar — Amber: from-amber-500 to-amber-600
CRM — Indigo: from-indigo-500 to-indigo-600
Metrics — Violet: from-violet-500 to-violet-600
Traces — Emerald: from-emerald-500 to-emerald-600
```

---

## SECTION 4 — DARK MODE IMPLEMENTATION

### Wire `next-themes`:

**`src/app/layout.tsx`:**
```tsx
import { ThemeProvider } from "next-themes";

// Wrap children:
<ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
  <QueryProvider>{children}</QueryProvider>
</ThemeProvider>
```

**Add theme toggle to `src/components/layout/top-nav.tsx`:**
```tsx
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

// Inside the nav's right-side actions:
const { theme, setTheme } = useTheme();
<Button
  variant="ghost" size="icon"
  onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
  className="rounded-xl"
>
  <Sun className="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
  <Moon className="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
</Button>
```

### Dark mode rules:
- All `glass-card` classes must change: light = `bg-white/80 border-black/5`, dark = `bg-white/5 border-white/10`
- Backgrounds: light = `bg-[#FDFDFD]`, dark = `bg-slate-950`
- Text contrast minimums: body text 4.5:1, headings 7:1
- Charts: adjust fills for dark backgrounds (use lighter versions of chart colors)
- Dot patterns / gradients: invert opacity or hue for dark mode

---

## SECTION 5 — BACKGROUND SYSTEM (replace current triple-layer mess)

Delete all of these classes from `globals.css`: `bg-page`, `bg-dot-pattern`, `bg-aurora`, `bg-aurora-orange`, `bg-aurora-pink`, `bg-grid`, `bg-mesh`.

Replace with ONE sophisticated system:

**Dashboard pages** — Clean, minimal:
```css
.bg-dashboard {
  background-color: var(--background);
  background-image: radial-gradient(
    ellipse 80% 50% at 50% -20%,
    hsl(var(--primary) / 0.03),
    transparent
  );
}
.dark .bg-dashboard {
  background-image: radial-gradient(
    ellipse 80% 50% at 50% -20%,
    hsl(var(--primary) / 0.08),
    transparent
  );
}
```

**Landing page** — More expressive but still refined:
```css
.bg-landing-hero {
  background-color: var(--background);
  background-image:
    radial-gradient(ellipse 60% 40% at 40% 0%, hsl(234 89% 54% / 0.06), transparent),
    radial-gradient(ellipse 40% 60% at 80% 100%, hsl(346 77% 50% / 0.04), transparent);
}
```

---

## SECTION 6 — COMPONENT REDESIGN (file-by-file)

### 6.1 — Root Layout (`src/app/layout.tsx`)
- Replace Inter with chosen Google Font pair
- Wrap with `ThemeProvider`
- Add `<html lang="en" className={fontVar} suppressHydrationWarning>`

### 6.2 — Top Navigation (`src/components/layout/top-nav.tsx`)
**Current problem:** Overly decorative glass nav with "AI" badge that looks gimmicky.

**Redesign:**
- Remove the `<Sparkles> AI` badge — it's unnecessary chrome
- Cleaner glass effect: `bg-white/70 dark:bg-slate-900/70 backdrop-blur-2xl border-b border-border/50` — subtler than current
- Keep floating style but reduce margin: `mx-3 mt-3` with `rounded-2xl`
- Active nav item: filled background with `bg-primary/10 text-primary` — not per-item custom colors. Each nav item should have the same ACTIVE style (primary color), with unique icon colors only in the ICON itself
- Right side: theme toggle + user dropdown (no AI badge)
- Mobile: full-screen overlay nav with `AnimatePresence` slide-down, not a cramped grid
- Logo: Redesign the logo mark — a cleaner geometric shape (rounded square with abstract "R" cutout or flow lines), gradient of `from-primary to-primary/80`, not `from-blue-600 to-violet-600`

### 6.3 — Dashboard Shell (`src/components/layout/dashboard-shell.tsx`)
- Replace 3-layer background with single `bg-dashboard` class
- `PageHeader`: Keep structure, but headings use new font at `text-2xl font-bold tracking-tight`
- `StatCard`: Remove `glass-card` and `feature-card` custom classes. Use shadcn `Card` component as base. Add subtle left-border accent: `border-l-4 border-l-{color}`. Hover state: `hover:shadow-md transition-shadow`
- `SectionCard`: Use shadcn `Card` with consistent `p-6 rounded-xl` padding
- `StaggerContainer`/`StaggerItem`: Keep but ensure `staggerChildren: 0.06` (current 0.05 is fine)

### 6.4 — Landing Page Hero (`src/components/landing/hero-section.tsx`)
**Current problem:** Generic "AI inbox agent" headline, mesh + dot + aurora triple background, basic CTA buttons.

**Redesign — make it a PRODUCT DEMO, not a brochure:**
- Background: Use `bg-landing-hero` single gradient
- Kill the "Powered by LangGraph + Gemini" badge — nobody cares about your infra on a landing page. Replace with something like: `✦ Autonomous email agent` or a social proof badge `Trusted by 500+ professionals`
- Headline: Make it punchy and specific:
  ```
  Stop writing emails.
  Start approving them.
  ```
  Style: `text-5xl md:text-7xl font-extrabold tracking-tight`. Second line in `text-muted-foreground`.
- Sub-headline: Max 1 sentence. `Your AI agent classifies, drafts, and sends — you just hit approve.`
- CTAs: Primary button with gradient: `bg-primary hover:bg-primary/90` (solid, not outlined). Secondary: `variant="outline"`. No `<Play>` icon — nobody will watch a demo from a hero.
- **PRODUCT PREVIEW — the hero's centerpiece:** Below the CTAs, build an interactive/animated product mockup. NOT a static screenshot. Inspired by Gumloop's hero (which shows an actual workflow builder):
  - Show a mock inbox interface with 3-4 emails
  - Animate an email being selected → classified ("Meeting Request" badge appears) → draft generated → approved
  - Use Framer Motion to orchestrate a 4-step animation loop
  - Style it as a card with subtle shadow, rounded corners, actual UI components (not an image)
  - This is the SINGLE most impactful thing on the page — spend 40% of hero effort here

### 6.5 — Landing Stats Section (`src/components/landing/stats-section.tsx`)
- Animated counters with `whileInView` — count up from 0 to target number
- 4 stats in a row: `< 4s avg response | 95% approval rate | 7 AI pipeline steps | 500+ emails/day`
- Style: Large number (`text-4xl font-bold`), small label below, separated by subtle vertical dividers
- Background: subtle `bg-secondary/50` band to break the page

### 6.6 — Landing Features Section (`src/components/landing/features-section.tsx`)
**Current problem:** Generic 6-card grid with icon + title + description. This is the #1 AI slop pattern.

**Redesign — BENTO GRID with interactive mini-demos (Gumloop-inspired):**
- Replace the flat 3x2 grid with a bento layout:
  - 2 large cards (span 2 columns) + 4 small cards
  - OR: alternating large + small rows
- Each feature card should contain a VISUAL ELEMENT, not just text:
  - **AI Classification** (large card): Show a mini email with classification badges animating onto it — "Meeting Request" → "Inquiry" → "Complaint" cycling with Framer Motion
  - **Human-in-the-Loop** (large card): Show a mock approval UI — draft text + approve/reject buttons with a confidence ring
  - **Auto-Responses**: Show a typing animation generating a response
  - **Context Retrieval**: Show connected data sources (Gmail, CRM, Calendar icons) with connecting lines
  - **Full Observability**: Show a mini pipeline graph (7 nodes connected)
  - **Privacy First**: Show a lock icon with a shield animation
- Each card: `rounded-2xl` with `p-6 md:p-8`, `bg-card border`, subtle hover shadow
- Section heading: `text-3xl font-bold` centered, with a short tagline above it (`text-sm text-primary font-medium uppercase tracking-widest`)

### 6.7 — Landing Workflow Section (`src/components/landing/workflow-section.tsx`)
**Redesign as an animated pipeline visualization:**
- Show the 7-node pipeline: `classify → retrieve → decide → execute → generate → review → dispatch`
- Each node as a rounded card connected by animated lines/arrows
- On scroll into view, animate each node lighting up sequentially (left to right)
- Below each node: 1-line description
- Color code: each node gets a distinct accent (use the CHART_COLORS)
- This is ReasonFlow's unique differentiator — the LangGraph pipeline. SHOW it, don't just describe it. Inspired by Stack.ai's workflow builder visualization and Gumloop's "How it works" section.

### 6.8 — Landing CTA Section (`src/components/landing/cta-section.tsx`)
- Full-width section with `bg-primary` background (dark indigo)
- White text: `Ready to automate your inbox?`
- Single CTA button: white bg, primary text, `Start for free →`
- Optional: small text below `No credit card required`

### 6.9 — Landing Nav (`src/components/landing/landing-nav.tsx`)
- Transparent on top, gains `bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl` on scroll (use scroll listener + state)
- Logo on left, nav links center (`Features`, `How it Works`, `Pricing`), CTA on right (`Get Started`)
- Smooth, polished scroll-triggered transition

### 6.10 — Landing Footer (`src/components/landing/landing-footer.tsx`)
- Clean 4-column grid: Product, Resources, Company, Legal
- Logo + tagline on left
- Social links: GitHub, Twitter, LinkedIn (Lucide icons)
- Bottom bar: `© 2026 ReasonFlow. All rights reserved.`

### 6.11 — Auth Pages (`src/app/(auth)/login/page.tsx`, `register/page.tsx`)
**Current problem:** Centered card on mesh/aurora background with duplicated Google SVG.

**Redesign — Split layout:**
- Left panel (60%): Brand showcase — gradient background (`bg-primary`), large wordmark, rotating testimonial or product screenshot, subtle animated blob shapes
- Right panel (40%): Auth form — clean white/dark card, minimal fields, shadcn inputs
- Extract Google SVG into `src/components/icons/google-icon.tsx` shared component
- Mobile: Only show the right panel (form), full width

### 6.12 — Inbox Page (`src/app/inbox/page.tsx`, inbox components)
- `email-list.tsx`: Replace table rows with card-based list items. Each email card: sender avatar (first letter circle), subject bold, preview text truncated, classification badge, timestamp, status dot. Hover: subtle lift shadow.
- `email-card.tsx`: Fix hardcoded status color switch — use `STATUS_STYLES` from constants. Add `cursor-pointer`.
- `email-detail-panel.tsx`: Keep Sheet-based panel. Refine the spotlight effect — make it subtler. Add proper sections: From/To/Subject header → Classification + Confidence → Body → Draft (if exists) → Actions.
- `classification-badge.tsx`: Keep color mapping but ensure dark mode works. Use `CLASSIFICATION_COLORS` from constants (already does).

### 6.13 — Drafts Page (`src/app/drafts/page.tsx`, draft-review components)
- `confidence-indicator.tsx`: Replace progress bar with a **radial/ring gauge**. Use SVG circle with `stroke-dasharray` animated with Framer Motion. Color transitions: red < 0.7 < amber < 0.9 < green. Show percentage in center.
- `draft-editor.tsx`: Better styled textarea with line numbers or at least a `font-mono` option. Show character count.
- `approval-buttons.tsx`: Approve = solid green-ish button with checkmark icon. Reject = ghost red button. Add keyboard shortcut hints (`⌘ Enter to approve`). Spring animation on click.
- `original-email.tsx`: Styled as a subtle quote block with left border accent.

### 6.14 — Metrics Dashboard (`src/app/metrics/page.tsx`, metrics components)
- **Bento grid layout** — not a flat stack of charts
  - Top row: 4 stat summary cards (from `stats-cards.tsx`)
  - Second row: 2 large charts side by side — intent distribution (donut) + latency (bar)
  - Third row: 1 full-width accuracy chart
- Recharts theming: Create a shared Recharts theme config:
  - Use CSS variables for colors: `var(--chart-1)` through `var(--chart-5)`
  - Rounded bar corners: `radius={[6, 6, 0, 0]}`
  - Grid lines: very subtle `stroke="hsl(var(--border))"`
  - Tooltip: styled as a shadcn Card with `bg-popover border shadow-lg rounded-lg p-3`
  - Legend: horizontal, below chart, `text-sm text-muted-foreground`
- `intent-chart.tsx`: Donut chart (not full pie) — inner radius 60%, outer 80%. Show total in center.
- `latency-chart.tsx`: Grouped bar chart with subtle gradient fills.
- `accuracy-chart.tsx`: Stacked bar with success=emerald, failure=rose.

### 6.15 — Traces Page (`src/app/traces/page.tsx`, trace-viewer components)
- `trace-list.tsx`: Table with better styling. Status badge for each trace (success/failed/partial). Duration column. Hover reveals a mini pipeline preview.
- `trace-graph.tsx` — **THE SHOWCASE COMPONENT:**
  - Redesign as a proper **node graph** (horizontal pipeline):
  - Each node: rounded rectangle with icon on top, name below, duration, status color border
  - Connections: animated SVG `<path>` elements with flowing dots or dashes
  - Active/selected node: scale up slightly, glow ring
  - Failed node: red border + shake animation
  - Skipped node: gray/dashed border
  - This should look like a simplified version of Gumloop's workflow builder
- `step-detail.tsx`: Collapsible sections for each step. JSON data shown in a syntax-highlighted code block (use `font-mono`, basic keyword coloring via CSS). Input/output tabs.

### 6.16 — Calendar Page (`src/app/calendar/page.tsx`)
- Clean availability display with time slots as cards
- Event creation form using shadcn form components
- Consistent with dashboard shell styling

### 6.17 — CRM Page (`src/app/crm/page.tsx`)
- Contact list as a data table with search/filter
- Contact detail as a side panel or modal
- Avatar with initials for each contact
- Tags/labels for contact categories

---

## SECTION 7 — MOTION SYSTEM (Framer Motion)

Standardize animations across the app:

```tsx
// src/lib/motion.ts — shared animation variants

export const fadeInUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
};

export const staggerContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.06 } },
};

export const staggerItem = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.3, ease: "easeOut" },
};

export const slideInRight = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
  transition: { duration: 0.3, ease: "easeInOut" },
};
```

**Rules:**
- Page transitions: `fadeInUp` on the main content wrapper
- Cards in grids: `staggerContainer` on parent, `staggerItem` on each card
- Modals/sheets: `scaleIn` on open
- Side panels: `slideInRight`
- Hover effects: `whileHover={{ y: -2 }}` on cards (NOT `scale` — it causes layout shift)
- Button press: `whileTap={{ scale: 0.98 }}`
- Landing scroll reveals: `whileInView` with `viewport={{ once: true, margin: "-100px" }}`
- Respect `prefers-reduced-motion`: wrap in `useReducedMotion()` check

---

## SECTION 8 — NEW FILES TO CREATE

1. `src/lib/motion.ts` — shared animation variants (above)
2. `src/components/icons/google-icon.tsx` — extracted Google SVG
3. `src/components/icons/logo.tsx` — ReasonFlow logo component
4. `src/app/loading.tsx` — Root loading boundary (skeleton with logo)
5. `src/app/error.tsx` — Root error boundary (styled error card)
6. `src/app/inbox/loading.tsx` — Inbox loading skeleton
7. `src/app/drafts/loading.tsx` — Drafts loading skeleton
8. `src/app/metrics/loading.tsx` — Metrics loading skeleton
9. `src/app/traces/loading.tsx` — Traces loading skeleton

---

## SECTION 9 — GLOBALS.CSS CLEANUP

1. Remove ALL custom background classes (`bg-page`, `bg-dot-pattern`, `bg-aurora`, `bg-aurora-orange`, `bg-aurora-pink`, `bg-grid`, `bg-mesh`)
2. Remove `glass-card` class — use shadcn Card with custom variant instead
3. Remove `gradient-border-card`, `feature-card` — achieve via Tailwind utilities
4. Remove `card-pink`, `card-blue`, `card-green`, `card-amber`, `card-violet` — use left-border accent pattern instead
5. Remove `number-badge-*` classes — use Tailwind directly
6. Remove `glow-pink`, `glow-blue` — use `shadow-[0_0_20px_hsl(var(--primary)/0.15)]` inline
7. Remove `text-gradient` — if needed, use inline `bg-gradient-to-r bg-clip-text text-transparent`
8. Remove `bg-gradient-animated` + `@keyframes gradient-shift` — too distracting for dashboard use
9. Keep shadcn theme imports and `@custom-variant dark`
10. Add `bg-dashboard` and `bg-landing-hero` classes (from Section 5)
11. Unify to ONE color system (remove the OKLCH `@theme inline` block, keep HSL)

---

## SECTION 10 — QUALITY CHECKLIST (verify before done)

### Visual
- [ ] No Inter/Roboto/Arial anywhere — new font applied globally
- [ ] Color palette is cohesive — primary indigo threads through the entire app
- [ ] Dark mode works on EVERY page — no white flashes, no invisible text
- [ ] No triple-stacked backgrounds — one clean background per page
- [ ] Feature cards have visual elements inside them, not just icon+text
- [ ] Charts use consistent custom theme matching the design system

### Interaction
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states on cards: subtle shadow lift (`hover:shadow-md`), NOT scale
- [ ] Dark mode toggle works in nav, persists via `next-themes`
- [ ] Transitions are 150-300ms, never > 500ms
- [ ] Focus rings visible on all interactive elements (`focus-visible:ring-2`)

### Responsive
- [ ] Test at 375px (mobile), 768px (tablet), 1024px (laptop), 1440px (desktop)
- [ ] No horizontal scroll at any breakpoint
- [ ] Mobile nav works: hamburger → full-screen overlay menu
- [ ] Landing page hero stacks vertically on mobile
- [ ] Bento grid collapses to single column on mobile

### Performance
- [ ] No layout shift during page load
- [ ] Skeleton loaders for all async data
- [ ] Images use `next/image` with proper `width`/`height`
- [ ] `loading.tsx` boundary files exist for each route

### Accessibility
- [ ] All images have `alt` text
- [ ] Form inputs have `<label>` elements
- [ ] Color alone is not the only status indicator (add text/icon too)
- [ ] `prefers-reduced-motion` is respected (disable animations)
- [ ] Semantic HTML: `<nav>`, `<main>`, `<section>`, `<article>`

### Cleanup
- [ ] GSAP removed from `package.json`
- [ ] No duplicate Google SVG — extracted to shared component
- [ ] All status/classification colors from constants, not inline
- [ ] Old CSS classes removed from `globals.css`
- [ ] No unused imports in any file
