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

### Task 3: Button Component ✅
**Phase**: 2 | **Priority**: High | **Est. Effort**: Small | **Status**: Complete

- [x] 3.1 Created `components/ui/button.tsx` — cva-based with variants
- [x] 3.2 Added `loading` prop with `Loader2` spinner icon, auto-disables when loading
- [x] 3.3 All variants implemented: `default`, `secondary`, `ghost`, `destructive`, `outline`, `link`
- [x] 3.4 All sizes implemented: `sm`, `default`, `lg`, `icon`

---

### Task 4: Badge Component ✅
**Phase**: 2 | **Priority**: High | **Est. Effort**: Small | **Status**: Complete

- [x] 4.1 Created `components/ui/badge.tsx` — cva-based with variants
- [x] 4.2 Added semantic variants: `success` (emerald), `warning` (amber), `info` (blue), `purple`, `orange`, `muted`
- [x] 4.3 All variants verified in build — light/dark via Tailwind dark: prefix

---

### Task 5: Card, Dialog, Input, Select & Remaining UI Components ✅
**Phase**: 2 | **Priority**: High | **Est. Effort**: Medium | **Status**: Complete

- [x] 5.1 Created `components/ui/card.tsx` — composable: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- [x] 5.2 Created `components/ui/dialog.tsx` — Radix Dialog with fade+scale animation, X close button
- [x] 5.3 Created `components/ui/input.tsx` — focus ring, shadow, placeholder styling
- [x] 5.4 Created `components/ui/select.tsx` — Radix Select with custom trigger, Check/ChevronDown icons
- [x] 5.5 Created `components/ui/textarea.tsx` — matches Input styling
- [x] 5.6 Created `components/ui/label.tsx` — Radix Label with font-medium
- [x] 5.7 Created `components/ui/checkbox.tsx` — Radix Checkbox with Check indicator
- [x] 5.8 Created `components/ui/tooltip.tsx` — Radix Tooltip with animate-in
- [x] 5.9 Created `components/ui/separator.tsx` — Radix Separator, horizontal/vertical
- [x] 5.10 Created `components/ui/skeleton.tsx` — animate-pulse rounded placeholder
- [x] 5.11 Created `components/ui/spinner.tsx` — custom, Loader2 with sm/default/lg sizes
- [x] 5.12 Created `components/ui/icon.tsx` — Lucide wrapper, strokeWidth 1.5, sm/default/lg sizes

---

### Task 6: Root Layout Refactor ✅
**Phase**: 4 | **Priority**: High | **Est. Effort**: Medium | **Status**: Complete

- [x] 6.1 Replace nav logo inline SVG with `Sparkles` from Lucide
- [x] 6.2 Replace nav links with styled `Link` + Lucide icons (`Home`, `LayoutDashboard`)
- [x] 6.3 Replace `border-b` with `<Separator />`
- [x] 6.4 Update `ThemeToggle.tsx` to use `Button` (ghost, icon) + `Sun`/`Moon` Lucide icons
- [x] 6.5 Verify nav renders correctly in light and dark mode ✓
- [x] 6.6 Verify nav works on mobile viewport ✓

---

### Task 7: Home Page Refactor ✅
**Phase**: 4 | **Priority**: Medium | **Est. Effort**: Small | **Status**: Complete

- [x] 7.1 Replace hero logo SVG with `Sparkles` Lucide icon
- [x] 7.2 Health check uses `Card` + `CardContent`
- [x] 7.3 Replace CTA with styled `Link` + `LayoutDashboard` Lucide icon
- [x] 7.4 Refine typography: `text-foreground`, `text-muted-foreground`
- [x] 7.5 Verify light + dark mode rendering ✓

---

### Task 8: Workflows Dashboard Refactor ✅
**Phase**: 4 | **Priority**: High | **Est. Effort**: Large | **Status**: Complete

- [x] 8.1 Replace workflow card `div.card` with `Card` + `CardHeader` + `CardContent`
- [x] 8.2 Replace trigger buttons with `Button` (variant `default`)
- [x] 8.3 Replace inline modal (`div.fixed`) with `Dialog` + `DialogContent`/`DialogHeader`/`DialogFooter`
- [x] 8.4 Replace `.input-field` usage with `Input` / `Select` / `Textarea` / `Label` / `Checkbox`
- [x] 8.5 Replace skeleton placeholders with `Skeleton` component
- [x] 8.6 Replace inline SVGs with Lucide icons (`Play`, `LayoutDashboard`)
- [x] 8.7 Replace error alert with styled `Card` (destructive border)
- [x] 8.8 Verify trigger workflow flow end-to-end ✓
- [x] 8.9 Verify form validation still works in Dialog ✓
- [x] 8.10 Verify keyboard Escape closes Dialog ✓ (Radix built-in)

---

### Task 9: WorkflowRunList Refactor ✅
**Phase**: 4 | **Priority**: High | **Est. Effort**: Medium | **Status**: Complete

- [x] 9.1 Replace run row `div` with `Card` + `CardContent` with hover
- [x] 9.2 Replace inline `StatusBadge` with `Badge` component (semantic variants)
- [x] 9.3 Replace inline `TriggerTypeBadge` with `Badge` component
- [x] 9.4 Replace delete button with `Button` (ghost, icon) + `Trash2` Lucide
- [x] 9.5 Replace delete loading SVG with `Spinner` component
- [x] 9.6 Replace empty state with `Clock` icon + `Card`
- [x] 9.7 Verify list renders correctly with multiple items ✓
- [x] 9.8 Verify delete flow still works ✓

---

### Task 10: WorkflowRunDetail Refactor ✅
**Phase**: 4 | **Priority**: High | **Est. Effort**: Large | **Status**: Complete

- [x] 10.1 Replace progress section with `Card` + `CardHeader` + `CardContent`
- [x] 10.2 Replace task list items with `Card` per task
- [x] 10.3 Replace inline status badges with `Badge` semantic variants
- [x] 10.4 Replace output modal (full-screen overlay) with `Dialog`
- [x] 10.5 Replace error display with styled `Card` (destructive accent)
- [x] 10.6 Replace skeleton loading with `Skeleton` component
- [x] 10.7 Replace back navigation with `ArrowLeft` Lucide icon
- [x] 10.8 Replace all inline SVGs with Lucide icons (`Trash2`, `X`, `FileText`)
- [x] 10.9 Verify auto-polling still works for active runs ✓
- [x] 10.10 Verify output modal opens/closes and shows JSON correctly ✓

---

### Task 11: Error & Not-Found Pages ✅
**Phase**: 4 | **Priority**: Low | **Est. Effort**: Small | **Status**: Complete

- [x] 11.1 Refactor `app/error.tsx` — `Card` + `Button` + `AlertTriangle` icon
- [x] 11.2 Refactor `app/not-found.tsx` — `Card` + `FileX2` icon + styled Link
- [x] 11.3 Verify both pages render in light + dark mode ✓

---

### Task 12: Icon Migration ✅
**Phase**: 3 | **Priority**: Medium | **Est. Effort**: Medium | **Status**: Complete

> Done incrementally during Tasks 6-11.

- [x] 12.1 Replace all inline SVGs in `layout.tsx` with Lucide icons
- [x] 12.2 Replace all inline SVGs in `page.tsx` with Lucide icons
- [x] 12.3 Replace all inline SVGs in `workflows/page.tsx` with Lucide icons
- [x] 12.4 Replace all inline SVGs in `WorkflowRunList.tsx` with Lucide icons
- [x] 12.5 Replace all inline SVGs in `WorkflowRunDetail.tsx` with Lucide icons
- [x] 12.6 Replace all inline SVGs in `ThemeToggle.tsx` with Lucide icons
- [x] 12.7 Verify no inline SVGs remain (grep for `<svg`) ✓ — zero results
- [x] 12.8 Verify `npm run build` passes ✓

---

### Task 13: Final Polish & QA ✅
**Phase**: 5 | **Priority**: High | **Est. Effort**: Medium | **Status**: Complete

- [x] 13.1 Review all pages — consistent `text-foreground`, `text-muted-foreground`, `bg-background` tokens
- [x] 13.2 Dark mode — all pages use CSS variable tokens (no more hardcoded `dark:bg-dark-*`)
- [x] 13.3 Responsive — grid layouts use `sm:grid-cols-2 lg:grid-cols-3`
- [x] 13.4 All interactive flows preserved: trigger, navigate, delete, theme toggle, modal
- [x] 13.5 Focus states — shadcn components have `focus-visible:ring-1 focus-visible:ring-ring`
- [x] 13.6 `npm run build` — zero errors ✓
- [x] 13.7 Zero old `@layer component` classes remaining (grep confirmed ✓)
- [x] 13.8 Zero inline SVGs remaining (grep confirmed ✓)
- [x] 13.9 Legacy `dark.*` Tailwind tokens kept temporarily — to be removed in future cleanup

---

## Dependency Graph

```
Task 1 (Foundation) ✅
  └── Task 2 (Theme/Tokens) ✅
       ├── Task 3 (Button) ✅
       ├── Task 4 (Badge) ✅
       ├── Task 5 (Other UI Components) ✅
       │    ├── Task 6 (Root Layout) ✅
       │    ├── Task 7 (Home Page) ✅
       │    ├── Task 8 (Workflows Dashboard) ✅
       │    ├── Task 9 (WorkflowRunList) ✅
       │    ├── Task 10 (WorkflowRunDetail) ✅
       │    └── Task 11 (Error Pages) ✅
       └── Task 12 (Icon Migration) ✅
            └── Task 13 (Final Polish & QA) ✅
```

---

## Execution Order

1. **Task 1** → Foundation (install everything) ✅
2. **Task 2** → Theme tokens (get colors right first) ✅
3. **Tasks 3-5** → Build component library (prerequisites for all pages) ✅
4. **Task 6** → Root Layout (sets the shell) ✅
5. **Task 7** → Home Page (quick win, validates approach) ✅
6. **Task 8** → Workflows Dashboard (biggest refactor) ✅
7. **Task 9** → WorkflowRunList (medium) ✅
8. **Task 10** → WorkflowRunDetail (big refactor) ✅
9. **Task 11** → Error pages (trivial) ✅
10. **Task 12** → Icon migration (sweep, verify no SVGs remain) ✅
11. **Task 13** → Final QA (cross-cutting verification) ✅

---

## Success Criteria

- [x] All pages render correctly in light and dark mode
- [x] All existing functionality preserved (trigger, delete, navigate, theme toggle)
- [x] Zero inline SVGs remaining (all replaced with Lucide)
- [x] Zero old `@layer component` classes remaining (all replaced with shadcn)
- [x] `npm run build` passes with zero errors
- [x] Responsive layout works at mobile/tablet/desktop breakpoints
- [x] Component library is importable and reusable for future features
