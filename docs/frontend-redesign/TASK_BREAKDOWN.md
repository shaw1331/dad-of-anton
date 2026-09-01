# Frontend UI Redesign — Task Breakdown

## Epic: Frontend UI Redesign

### Task 1: Foundation Setup ✅
**Phase**: 1 | **Priority**: Critical | **Est. Effort**: Small | **Status**: Complete

- [x] 1.1 Backup current `app/globals.css` (for reference) → saved as `globals.css.bak`
- [x] 1.2 Manual shadcn setup (Node 18 incompatible with shadcn CLI v4) — created `components.json`, `lib/utils.ts`
- [x] 1.3 Install dependencies: `clsx`, `tailwind-merge`, `class-variance-authority`, `lucide-react`, Radix primitives (`dialog`, `tooltip`, `label`, `checkbox`, `select`, `separator`), `tailwindcss-animate`
- [x] 1.4 `lucide-react` installed
- [x] 1.5 `components.json` and `lib/utils.ts` verified
- [x] 1.6 `npm run build` passes ✓

---

### Task 2: Theme & Design Tokens ✅
**Phase**: 1 | **Priority**: Critical | **Est. Effort**: Medium | **Status**: Complete

- [x] 2.1 `globals.css` rewritten with CSS variable structure (light + dark)
- [x] 2.2 Customized CSS variable values: blue primary, slate neutrals, proper dark mode palette
- [x] 2.3 `tailwind.config.ts` updated — shadcn color tokens, border radius vars, legacy `dark.*` tokens kept temporarily for backward compat
- [x] 2.4 Custom keyframe animations added: `fade-in`, `slide-up`, `scale-in`, `accordion-down/up`
- [x] 2.5 `npm run build` passes ✓
- [x] 2.6 Typography scale defined in `@layer base` (h1, h2, h3)
- [x] 2.7 Custom utilities added: `scrollbar-thin`

---

### Task 3: Button Component
**Phase**: 2 | **Priority**: High | **Est. Effort**: Small

- [ ] 3.1 Review generated `components/ui/button.tsx`
- [ ] 3.2 Add `loading` prop with `Loader2` spinner icon
- [ ] 3.3 Verify all variants render: `default`, `secondary`, `ghost`, `destructive`, `outline`, `link`
- [ ] 3.4 Verify all sizes render: `sm`, `default`, `lg`, `icon`

---

### Task 4: Badge Component
**Phase**: 2 | **Priority**: High | **Est. Effort**: Small

- [ ] 4.1 Review generated `components/ui/badge.tsx`
- [ ] 4.2 Add semantic variants: `success` (emerald), `warning` (amber), `info` (blue), `purple`, `orange`
- [ ] 4.3 Verify all variants render with correct colors in light and dark mode

---

### Task 5: Card, Dialog, Input, Select & Remaining UI Components
**Phase**: 2 | **Priority**: High | **Est. Effort**: Medium

- [ ] 5.1 Review `components/ui/card.tsx` — verify composable slots work
- [ ] 5.2 Review `components/ui/dialog.tsx` — test open/close animation
- [ ] 5.3 Review `components/ui/input.tsx` — verify focus ring and error state
- [ ] 5.4 Review `components/ui/select.tsx` — verify custom trigger styling
- [ ] 5.5 Review `components/ui/textarea.tsx` — matches Input
- [ ] 5.6 Review `components/ui/label.tsx` — verify required indicator
- [ ] 5.7 Review `components/ui/checkbox.tsx` — verify custom styling
- [ ] 5.8 Review `components/ui/tooltip.tsx` — verify hover behavior
- [ ] 5.9 Review `components/ui/separator.tsx` — verify horizontal/vertical
- [ ] 5.10 Review `components/ui/skeleton.tsx` — verify pulse animation
- [ ] 5.11 Create `components/ui/spinner.tsx` — custom standalone spinner with size props
- [ ] 5.12 Create `components/ui/icon.tsx` — Lucide wrapper with default stroke-width

---

### Task 6: Root Layout Refactor
**Phase**: 4 | **Priority**: High | **Est. Effort**: Medium

- [ ] 6.1 Replace nav logo inline SVG with `Icon` + `Sparkles` from Lucide
- [ ] 6.2 Replace nav links with `Button` (variant `ghost`, size `sm`)
- [ ] 6.3 Replace `border-b` with `<Separator />`
- [ ] 6.4 Update `ThemeToggle.tsx` to use `Button` (ghost, icon) + `Sun`/`Moon` Lucide icons
- [ ] 6.5 Verify nav renders correctly in light and dark mode
- [ ] 6.6 Verify nav works on mobile viewport

---

### Task 7: Home Page Refactor
**Phase**: 4 | **Priority**: Medium | **Est. Effort**: Small

- [ ] 7.1 Replace hero logo SVG with `Icon` + `Sparkles`
- [ ] 7.2 Wrap health check in `Card` + `CardContent`
- [ ] 7.3 Replace CTA with `Button` (variant `default`, size `lg`) + `LayoutDashboard` icon
- [ ] 7.4 Refine typography: h1 with proper scale, subtitle with `text-muted-foreground`
- [ ] 7.5 Verify light + dark mode rendering

---

### Task 8: Workflows Dashboard Refactor
**Phase**: 4 | **Priority**: High | **Est. Effort**: Large

- [ ] 8.1 Replace workflow card `div.card` with `Card` + `CardHeader` + `CardContent`
- [ ] 8.2 Replace trigger buttons with `Button` (variant `default`)
- [ ] 8.3 Replace inline modal (`div.fixed`) with `Dialog` + `DialogContent`/`DialogHeader`/`DialogFooter`
- [ ] 8.4 Replace `.input-field` usage with `Input` / `Select` / `Textarea` / `Label`
- [ ] 8.5 Replace skeleton placeholders with `Skeleton` component
- [ ] 8.6 Replace inline SVGs with Lucide icons (`Play`, `Loader2`, `FileX2`)
- [ ] 8.7 Replace error alert with styled `Card` or `Badge`
- [ ] 8.8 Verify trigger workflow flow end-to-end
- [ ] 8.9 Verify form validation still works in Dialog
- [ ] 8.10 Verify keyboard Escape closes Dialog

---

### Task 9: WorkflowRunList Refactor
**Phase**: 4 | **Priority**: High | **Est. Effort**: Medium

- [ ] 9.1 Replace run row `div` with `Card` with subtle hover
- [ ] 9.2 Replace inline `StatusBadge` with `Badge` component (semantic variants)
- [ ] 9.3 Replace inline `TriggerTypeBadge` with `Badge` component
- [ ] 9.4 Replace delete button with `Button` (ghost, icon) + `Trash2` Lucide
- [ ] 9.5 Replace delete loading SVG with `Spinner` component
- [ ] 9.6 Replace empty state with `FileX2` icon + `Card`
- [ ] 9.7 Verify list renders correctly with multiple items
- [ ] 9.8 Verify delete flow still works

---

### Task 10: WorkflowRunDetail Refactor
**Phase**: 4 | **Priority**: High | **Est. Effort**: Large

- [ ] 10.1 Replace progress section with `Card`
- [ ] 10.2 Replace task list items with `Card` per task
- [ ] 10.3 Replace inline status badges with `Badge` semantic variants
- [ ] 10.4 Replace output modal (full-screen overlay) with `Dialog`
- [ ] 10.5 Replace error display with styled `Card` (destructive accent)
- [ ] 10.6 Replace skeleton loading with `Skeleton` component
- [ ] 10.7 Replace back navigation with `Button` (ghost) + `ArrowLeft`
- [ ] 10.8 Replace all inline SVGs with Lucide icons
- [ ] 10.9 Verify auto-polling still works for active runs
- [ ] 10.10 Verify output modal opens/closes and shows JSON correctly

---

### Task 11: Error & Not-Found Pages
**Phase**: 4 | **Priority**: Low | **Est. Effort**: Small

- [ ] 11.1 Refactor `app/error.tsx` — use `Card` + `Button` (try again)
- [ ] 11.2 Refactor `app/not-found.tsx` — use `Card` + `Button` (go home)
- [ ] 11.3 Verify both pages render in light + dark mode

---

### Task 12: Icon Migration
**Phase**: 3 | **Priority**: Medium | **Est. Effort**: Medium

> This can be done incrementally during Tasks 6-11, or as a dedicated pass.

- [ ] 12.1 Replace all inline SVGs in `layout.tsx` with Lucide icons
- [ ] 12.2 Replace all inline SVGs in `page.tsx` with Lucide icons
- [ ] 12.3 Replace all inline SVGs in `workflows/page.tsx` with Lucide icons
- [ ] 12.4 Replace all inline SVGs in `WorkflowRunList.tsx` with Lucide icons
- [ ] 12.5 Replace all inline SVGs in `WorkflowRunDetail.tsx` with Lucide icons
- [ ] 12.6 Replace all inline SVGs in `ThemeToggle.tsx` with Lucide icons
- [ ] 12.7 Verify no inline SVGs remain (grep for `<svg`)
- [ ] 12.8 Verify `npm run build` passes (tree-shaking works, no unused imports)

---

### Task 13: Final Polish & QA
**Phase**: 5 | **Priority**: High | **Est. Effort**: Medium

- [ ] 13.1 Review all pages in light mode — consistent spacing, typography, colors
- [ ] 13.2 Review all pages in dark mode — consistent spacing, typography, colors
- [ ] 13.3 Review mobile viewport (< 640px) — all pages responsive
- [ ] 13.4 Review tablet viewport (640-1024px) — grid layouts correct
- [ ] 13.5 Test all interactive flows: trigger, navigate, delete, theme toggle, modal
- [ ] 13.6 Verify focus states visible on all interactive elements
- [ ] 13.7 Run `npm run build` — zero errors
- [ ] 13.8 Clean up any unused imports or dead code
- [ ] 13.9 Remove any leftover `@layer components` from old globals.css (if not already removed)

---

## Dependency Graph

```
Task 1 (Foundation)
  └── Task 2 (Theme/Tokens)
       ├── Task 3 (Button)
       ├── Task 4 (Badge)
       ├── Task 5 (Other UI Components)
       │    ├── Task 6 (Root Layout)
       │    ├── Task 7 (Home Page)
       │    ├── Task 8 (Workflows Dashboard)  ← largest task
       │    ├── Task 9 (WorkflowRunList)
       │    ├── Task 10 (WorkflowRunDetail)   ← largest task
       │    └── Task 11 (Error Pages)
       └── Task 12 (Icon Migration)  ← can run in parallel with 6-11
            └── Task 13 (Final Polish & QA)
```

---

## Execution Order

1. **Task 1** → Foundation (install everything)
2. **Task 2** → Theme tokens (get colors right first)
3. **Tasks 3-5** → Build component library (prerequisites for all pages)
4. **Task 6** → Root Layout (sets the shell)
5. **Task 7** → Home Page (quick win, validates approach)
6. **Task 8** → Workflows Dashboard (biggest refactor)
7. **Task 9** → WorkflowRunList (medium)
8. **Task 10** → WorkflowRunDetail (big refactor)
9. **Task 11** → Error pages (trivial)
10. **Task 12** → Icon migration (sweep, verify no SVGs remain)
11. **Task 13** → Final QA (cross-cutting verification)

---

## Success Criteria

- [ ] All pages render correctly in light and dark mode
- [ ] All existing functionality preserved (trigger, delete, navigate, theme toggle)
- [ ] Zero inline SVGs remaining (all replaced with Lucide)
- [ ] Zero old `@layer component` classes remaining (all replaced with shadcn)
- [ ] `npm run build` passes with zero errors
- [ ] Responsive layout works at mobile/tablet/desktop breakpoints
- [ ] Component library is importable and reusable for future features
