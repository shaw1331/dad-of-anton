# Frontend UI Redesign — Implementation Plan

## Overview

Transform the existing functional-but-generic frontend into a polished, modern design system with reusable components, consistent design tokens, and a refined aesthetic. The approach: adopt **shadcn/ui** for accessible primitives, add **Lucide React** for icons, and create a coherent design token system.

**Design Direction**: Minimal & Confident — clean whitespace, subtle depth with layered surfaces, refined typography scale, smooth micro-interactions. Vercel/Linear aesthetic. Natural evolution of the existing slate-blue palette.

**Scope**: ~20 files modified/created, no backend changes, no functional changes — visual and structural only.

---

## Phase 1: Foundation Layer

> Install dependencies, configure theming, establish design tokens.

### 1a. Install shadcn/ui + Lucide

```bash
cd frontend
npx shadcn@latest init
# Select: New York style, Slate base color, CSS variables: yes
npx shadcn@latest add button badge dialog input label select textarea card separator tooltip checkbox skeleton
npm install lucide-react
```

**Generated artifacts**:
- `components.json` — shadcn config (tailwind path, alias config)
- `lib/utils.ts` — `cn()` helper (clsx + tailwind-merge)
- `app/globals.css` — overwritten with CSS variable theme system
- `components/ui/*` — each `add` command generates a component file

### 1b. Tailwind Config

**File**: `tailwind.config.ts`

- Keep `darkMode: "class"`
- Remove manual `dark.*` color tokens (replaced by CSS variables)
- Add shadcn-compatible `borderRadius` config
- Add custom keyframe animations: `fade-in`, `slide-up`, `scale-in`
- Add `font-sans` mapping to Inter, add `font-mono` for code blocks

### 1c. Global CSS

**File**: `app/globals.css`

Replace the entire file with shadcn's CSS variable system:

- `:root` — light mode tokens: `--background`, `--foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--destructive-foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--border`, `--input`, `--ring`, `--radius`
- `.dark` — dark mode overrides for all tokens
- `@layer base` — body defaults, antialiased rendering
- `@layer utilities` — custom scrollbar styles, animation utilities
- Remove old `@layer components` block (`.card`, `.badge-*`, `.btn-*`, `.input-field`)

**Design tokens**:

| Token (Light) | Value | Token (Dark) | Value |
|---|---|---|---|
| `--background` | `0 0% 98%` (slate-50) | `--background` | `222 47% 11%` (slate-950) |
| `--foreground` | `222 47% 11%` | `--foreground` | `210 40% 98%` |
| `--primary` | `221 83% 53%` (blue-600) | `--primary` | `217 91% 60%` (blue-500) |
| `--secondary` | `210 40% 96%` (slate-100) | `--secondary` | `217 33% 17%` (slate-800) |
| `--muted` | `210 40% 96%` | `--muted` | `217 33% 17%` |
| `--accent` | `210 40% 96%` | `--accent` | `217 33% 17%` |
| `--destructive` | `0 84% 60%` (red-500) | `--destructive` | `0 63% 31%` (red-900) |
| `--card` | `0 0% 100%` | `--card` | `222 47% 15%` |
| `--border` | `214 32% 91%` | `--border` | `217 33% 25%` |
| `--ring` | `221 83% 53%` | `--ring` | `217 91% 60%` |
| `--radius` | `0.625rem` | — | — |

### 1d. Typography Scale

Define via Tailwind `@theme` or CSS variables:

| Element | Font Size | Line Height | Font Weight |
|---|---|---|---|
| `h1` | `2rem` (32px) | `1.2` | `700` |
| `h2` | `1.5rem` (24px) | `1.3` | `600` |
| `h3` | `1.125rem` (18px) | `1.4` | `600` |
| `body` | `0.875rem` (14px) | `1.6` | `400` |
| `small` | `0.75rem` (12px) | `1.5` | `400` |

---

## Phase 2: Reusable Component Library

> All components live in `components/ui/`. Built by shadcn `add` commands, then customized.

| Component | File | Source | Customization |
|---|---|---|---|
| **Button** | `components/ui/button.tsx` | shadcn | Variants: `default`, `secondary`, `ghost`, `destructive`, `outline`, `link`. Sizes: `sm`, `default`, `lg`, `icon`. Add `loading` prop with spinner. |
| **Badge** | `components/ui/badge.tsx` | shadcn | Add semantic variants: `success` (emerald), `warning` (amber), `info` (blue), `purple`, `orange` — matching current status badge system. |
| **Card** | `components/ui/card.tsx` | shadcn | Composable: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`. |
| **Dialog** | `components/ui/dialog.tsx` | shadcn (Radix) | Fade+scale animation on open. `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`. |
| **Input** | `components/ui/input.tsx` | shadcn | Error state via `aria-invalid` prop. |
| **Select** | `components/ui/select.tsx` | shadcn (Radix) | Custom trigger styling to match Input. |
| **Textarea** | `components/ui/textarea.tsx` | shadcn | Matches Input styling. |
| **Label** | `components/ui/label.tsx` | shadcn (Radix) | Required indicator support via prop. |
| **Checkbox** | `components/ui/checkbox.tsx` | shadcn (Radix) | Custom styling. |
| **Tooltip** | `components/ui/tooltip.tsx` | shadcn (Radix) | For icon buttons and truncated text. |
| **Separator** | `components/ui/separator.tsx` | shadcn (Radix) | Horizontal/vertical. |
| **Skeleton** | `components/ui/skeleton.tsx` | shadcn | Pulse animation loading placeholders. |
| **Spinner** | `components/ui/spinner.tsx` | **Custom** | Standalone spinner extracted from inline SVGs. Accepts `size` prop (`sm`/`default`/`lg`). |

---

## Phase 3: Icon System

> Replace ~15+ inline SVG blocks with Lucide React icons.

### Icon Mapping

| Current Usage | Lucide Icon | Files Affected |
|---|---|---|
| Sparkles/logo icon | `Sparkles` | `layout.tsx`, `page.tsx` |
| Play/trigger | `Play` | `workflows/page.tsx` |
| Loading spinner | `Loader2` | `workflows/page.tsx`, `WorkflowRunList.tsx` |
| Sun (light mode) | `Sun` | `ThemeToggle.tsx` |
| Moon (dark mode) | `Moon` | `ThemeToggle.tsx` |
| Dashboard/workflows nav | `LayoutDashboard` | `layout.tsx` |
| Home nav | `Home` | `layout.tsx` |
| Trash/delete | `Trash2` | `WorkflowRunList.tsx`, `WorkflowRunDetail.tsx` |
| Check/success | `CheckCircle2` | `WorkflowRunList.tsx`, `WorkflowRunDetail.tsx` |
| X/error | `XCircle` | `WorkflowRunList.tsx`, `WorkflowRunDetail.tsx` |
| Warning/running | `Clock` | `WorkflowRunList.tsx`, `WorkflowRunDetail.tsx` |
| Alert/skipped | `AlertTriangle` | `WorkflowRunDetail.tsx` |
| Document/output | `FileText` | `WorkflowRunDetail.tsx` |
| Back arrow | `ArrowLeft` | `WorkflowRunDetail.tsx` |
| Chevron (select) | `ChevronDown` | (handled by shadcn Select) |
| Empty state | `FileX2` | `workflows/page.tsx` |

### Icon Wrapper

Create `components/ui/icon.tsx`:
```tsx
// Thin wrapper around Lucide for consistent defaults
// stroke-width: 1.5 (slightly thinner than default 2 for refined look)
// Prop-based sizing: sm (14px), default (16px), lg (20px)
```

---

## Phase 4: Refactor Existing Components

> Replace all raw Tailwind classes and inline SVGs with the new component library.

### 4a. Root Layout (`app/layout.tsx`)

- **Nav links**: Replace raw `<Link>` classes with `Button` (variant `ghost`, size `sm`)
- **Nav logo**: Use `Icon` wrapper with `Sparkles` icon
- **Nav border**: Replace `border-b` class with `<Separator />`
- **Theme toggle**: `Button` (variant `ghost`, size `icon`) with `Sun`/`Moon`
- **Mobile nav**: Add responsive hamburger menu or keep simple with `sm:` breakpoints
- Keep: ThemeProvider wrapping, dark mode flash-prevention script

### 4b. ThemeToggle (`components/ThemeToggle.tsx`)

- Use `Button` (variant `ghost`, size `icon`)
- Use `Sun` and `Moon` from Lucide
- Keep rotation/scale animation via Tailwind classes on the icons

### 4c. Home Page (`app/page.tsx`)

- Hero section: keep centered layout, refine spacing
- Logo: `Icon` + `Sparkles` with gradient background
- Title: use `<h1>` with proper typography token
- CTA: `Button` (variant `default`, size `lg`) with `LayoutDashboard` icon
- Health check: wrap in `Card` + `CardHeader`/`CardContent`

### 4d. Workflows Dashboard (`app/workflows/page.tsx`)

**Current → New mapping**:

| Current | New |
|---|---|
| `.card` on workflow items | `Card` > `CardHeader` + `CardContent` |
| `.btn-primary` trigger buttons | `Button` (variant `default`) |
| `.btn-secondary` cancel | `Button` (variant `secondary")` |
| `.input-field` text/select | `Input`, `Select`, `Textarea` |
| Inline modal (`div.fixed`) | `Dialog` + `DialogContent`/`DialogHeader`/`DialogFooter` |
| Inline error alert | `Card` with `destructive` border |
| Skeleton placeholders | `Skeleton` component |
| Inline SVG in trigger button | `Play` + `Loader2` Lucide icons |
| Status `div` in workflow cards | `Badge` with semantic variant |

### 4e. WorkflowRunList (`app/components/WorkflowRunList.tsx`)

- Each run row: `Card` with subtle hover state
- Status badges: `Badge` with `success`/`warning`/`danger`/`info`/`muted` variants
- Trigger type badges: `Badge` with `default`/`purple`/`orange` variants
- Delete button: `Button` (variant `ghost`, size `icon`) with `Trash2`
- Loading spinner on delete: `Spinner` component
- Empty state: `FileX2` icon + `Card`

### 4f. WorkflowRunDetail (`app/components/WorkflowRunDetail.tsx`)

- Progress section: `Card` with progress bar
- Task list: `Card` per task, colored left border via utility classes
- Task status circles: `Badge` semantic variants
- Output modal: replace full-screen overlay with `Dialog`
- Error display: `Card` with destructive accent
- Skeleton loading: `Skeleton` component
- Back navigation: `Button` (variant `ghost`) with `ArrowLeft`
- All icons: Lucide replacements

### 4g. Error/Not-Found Pages

- `app/error.tsx`: `Card` + `Button` (try again)
- `app/not-found.tsx`: `Card` + `Button` (go home)

---

## Phase 5: Polish & Consistency

### Transition & Animation

- All interactive elements: `transition-all duration-200`
- Dialog: `data-[state=open]:animate-in data-[state=closed]:animate-out` (shadcn default)
- Button hover: subtle shadow lift
- Card hover: subtle shadow increase (existing pattern, keep)

### Focus & Accessibility

- All buttons/inputs: visible `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
- Dialog: focus trap (built into Radix)
- Keyboard: Escape closes dialogs (existing, keep)

### Spacing & Layout

- Page sections: `space-y-6` consistently
- Grid gaps: `gap-4` for cards
- Card internal: `p-6` (keep existing)
- Section headers: `mb-4` with `h2` typography

### Error States

- Error callouts: `Card` with `border-destructive` + red-tinted background
- Inline validation: `Label` with error text below `Input`

---

## New File Tree

```
frontend/
├── app/
│   ├── globals.css                    # [MODIFIED] shadcn CSS vars + tokens
│   ├── layout.tsx                     # [MODIFIED] Lucide icons, Button nav
│   ├── page.tsx                       # [MODIFIED] Card, Button, refined
│   ├── error.tsx                      # [MODIFIED] Card, Button
│   ├── not-found.tsx                  # [MODIFIED] Card, Button
│   ├── components/
│   │   ├── HealthCheck.tsx            # [MODIFIED] Card, Badge
│   │   ├── WorkflowRunList.tsx        # [MODIFIED] Card, Badge, Button
│   │   └── WorkflowRunDetail.tsx      # [MODIFIED] Card, Badge, Dialog
│   └── workflows/
│       ├── page.tsx                   # [MODIFIED] full shadcn usage
│       └── [runId]/
│           └── page.tsx               # [MODIFIED] Card, Skeleton
├── components/
│   ├── ThemeProvider.tsx              # [UNCHANGED]
│   ├── ThemeToggle.tsx                # [MODIFIED] Button + Lucide
│   └── ui/                            # [NEW] Component library
│       ├── badge.tsx                  # shadcn + semantic variants
│       ├── button.tsx                 # shadcn + loading prop
│       ├── card.tsx                   # shadcn composables
│       ├── checkbox.tsx               # shadcn (Radix)
│       ├── dialog.tsx                 # shadcn (Radix)
│       ├── icon.tsx                   # Custom Lucide wrapper
│       ├── input.tsx                  # shadcn
│       ├── label.tsx                  # shadcn (Radix)
│       ├── select.tsx                 # shadcn (Radix)
│       ├── separator.tsx              # shadcn (Radix)
│       ├── skeleton.tsx               # shadcn
│       ├── spinner.tsx                # Custom
│       ├── textarea.tsx               # shadcn
│       ├── tooltip.tsx                # shadcn (Radix)
│       └── utils.ts                   # cn() helper (shadcn generated)
├── components.json                    # [NEW] shadcn config
├── tailwind.config.ts                 # [MODIFIED] shadcn theme
├── package.json                       # [MODIFIED] +lucide-react
└── lib/
    ├── types.ts                       # [UNCHANGED]
    ├── utils.ts                       # [GENERATED by shadcn] (or in lib/utils.ts)
    └── api/                           # [UNCHANGED]
```

---

## Verification

After each phase, verify:

1. **Import check**: `npm run build` passes without errors
2. **Dev server**: `npm run dev` runs, pages load at localhost:3000
3. **Visual check**: Light mode + dark mode both render correctly
4. **Functionality**: All existing features still work (trigger, delete, navigate, theme toggle)
5. **Responsive**: Mobile (< 640px) and desktop (> 1024px) layouts look correct

```bash
cd frontend
npm run build          # Type check + production build
npm run dev            # Dev server for visual verification
curl -s localhost:3000 # Quick smoke test
```

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| shadcn init overwrites globals.css | Backup current file first. The old `@layer components` classes are fully replaced by shadcn components. |
| Radix Dialog breaks existing modal logic | Port the `onSubmit`/`onCancel` handlers into Dialog's `onOpenChange` prop. Test keyboard escape. |
| Tailwind v3 → shadcn CSS variable conflict | shadcn uses `@theme inline` for CSS vars. Ensure Tailwind config doesn't duplicate. |
| `window.location.href` navigation causes flash | Keep as-is for now. Future: refactor to `router.push()` (out of scope). |
| Component import paths break | Use `@/components/ui/*` alias (already configured in tsconfig). |
