# Design Guidelines: WhatsApp Bulk Messaging System

## Design Approach

**Selected System:** Material Design 3 (Material You) adapted for web dashboard
**Rationale:** This is a data-heavy, productivity-focused application requiring clear information hierarchy, efficient CRUD operations, and table-heavy interfaces. Material Design provides robust patterns for forms, tables, data displays, and role-based dashboards while maintaining professional consistency.

**Design Principles:**
- **Clarity over decoration** - Information must be immediately scannable
- **Efficient workflows** - Minimize clicks for common operations
- **Role distinction** - Clear visual separation between admin and user experiences
- **Data density balance** - Pack information without overwhelming users

---

## Typography System

**Font Family:** Roboto (primary), Inter (alternative via Google Fonts)

**Hierarchy:**
- **Page Headers:** 32px/2rem, font-weight 500, tight letter-spacing
- **Section Headers:** 24px/1.5rem, font-weight 500
- **Card Titles:** 20px/1.25rem, font-weight 500
- **Body Text:** 16px/1rem, font-weight 400
- **Table Headers:** 14px/0.875rem, font-weight 600, uppercase with tracking
- **Table Content:** 14px/0.875rem, font-weight 400
- **Labels:** 14px/0.875rem, font-weight 500
- **Helper Text:** 12px/0.75rem, font-weight 400

---

## Layout & Spacing System

**Tailwind Spacing Units:** Consistent use of 2, 4, 6, 8, 12, 16, 20, 24 (i.e., p-2, p-4, m-6, gap-8, etc.)

**Primary spacing patterns:**
- Component padding: p-6 or p-8
- Section gaps: gap-6 or gap-8
- Card spacing: p-6
- Form field gaps: gap-4
- Table cell padding: px-4 py-3

**Dashboard Layout Structure:**
```
┌─────────────────────────────────────┐
│ Top Navigation Bar (h-16)          │
├──────┬──────────────────────────────┤
│ Side │ Main Content Area           │
│ bar  │ (Tables, Forms, Cards)      │
│(w-64)│ max-w-7xl mx-auto px-6      │
│      │                              │
└──────┴──────────────────────────────┘
```

**Desktop:** Fixed sidebar (w-64), main content max-w-7xl centered
**Tablet/Mobile:** Collapsible hamburger menu, full-width content with px-4

---

## Component Library

### Navigation
**Top Bar:**
- Height: h-16
- Logo left, user profile/logout right
- Greeting message centered (desktop) or below logo (mobile)
- Elevated shadow (shadow-md)

**Sidebar (Admin/User):**
- Width: w-64 on desktop, full-screen overlay on mobile
- Navigation items: px-4 py-3 with rounded-lg on hover
- Active state: distinct background treatment
- Icons: 20px/24px from Material Icons or Heroicons

### Dashboard Cards (Admin 4-card grid)
- Grid: `grid grid-cols-1 md:grid-cols-2 gap-6`
- Each card: rounded-xl, p-6, shadow-lg on hover
- Icon: 48px positioned top-left or centered
- Title: text-xl font-semibold mb-2
- Description: text-sm leading-relaxed
- Click target: entire card is interactive

### Tables (CRUD Interfaces)
**Structure:**
- Container: rounded-lg shadow with overflow-x-auto
- Table: w-full with divide-y
- Header row: sticky top-0, uppercase text-xs font-semibold tracking-wide
- Body rows: hover state, px-4 py-3
- Actions column: right-aligned with icon buttons (edit/delete)
- Pagination: bottom with results count and page controls

**Empty States:** Centered icon + message when no data

### Forms (Create/Edit Modals & Pages)
**Layout:**
- Single column for simple forms
- Two-column grid (grid-cols-1 md:grid-cols-2 gap-6) for complex forms
- Labels: above inputs, font-medium text-sm mb-2
- Input fields: h-11, rounded-lg, px-4, full border
- Validation errors: text-red-600 text-sm mt-1
- Required indicators: red asterisk after label
- Submit buttons: right-aligned or full-width on mobile

**Field Types:**
- Text/Email: Standard input with focus states
- Select dropdowns: Styled native select or custom dropdown
- File upload: Drag-drop zone with file preview list
- Textarea: min-h-32 for message bodies

### Bulk Message Sender Interface
**Layout (User Dashboard):**
```
┌─────────────────────────────────────┐
│ Section: Upload Recipients          │
│ - File drop zone (border-dashed)    │
│ - CSV template download link        │
│ - Preview table (first 10 rows)     │
├─────────────────────────────────────┤
│ Section: Message Content            │
│ - Image URL input with preview      │
│ - Title input                       │
│ - Message body textarea             │
├─────────────────────────────────────┤
│ Section: Progress (during send)     │
│ - Progress bar                      │
│ - Status counts (grid-cols-4)       │
│   Queued | Sent | Delivered | Failed│
└─────────────────────────────────────┘
```

**File Upload Zone:**
- min-h-48, border-2 border-dashed, rounded-lg
- Center-aligned icon + text
- Drag-over state with visual feedback

**Progress Display:**
- Horizontal progress bar (h-2 rounded-full)
- Status grid: 4 columns with large numbers and labels
- Real-time updates via polling

### Reports Interface
**Filter Section:**
- Horizontal form: flex gap-4, inputs inline
- Task ID/Title search inputs side-by-side
- Export CSV button (right-aligned)

**Report Display:**
- Summary cards at top: grid-cols-3 gap-6
  - Total Delivered | Total Seen | Total Replies
  - Large number display with icon
- Detailed table below with recipient-level data
- Expandable rows for reply text (if applicable)

### Modals
- Overlay: backdrop with backdrop-blur-sm
- Modal container: max-w-2xl, rounded-xl, p-8
- Header: text-2xl font-semibold mb-6
- Close button: top-right absolute
- Footer: flex justify-end gap-3

### Buttons
**Variants:**
- Primary: px-6 py-2.5 rounded-lg font-medium
- Secondary: px-6 py-2.5 rounded-lg border-2
- Icon buttons: p-2 rounded-lg (for table actions)
- Danger: for delete actions

---

## Specific Page Layouts

### Login Page
- Centered card: max-w-md mx-auto mt-20
- Logo/Title centered at top
- Two prominent buttons: "Login as Admin" | "Login as User"
- Selected role shows email/password form below
- Form: single column, gap-4

### Admin Dashboard
- Greeting: text-2xl mb-8 (e.g., "Good Morning, Admin Name")
- 4-card grid: Manage Businesses, Manage Users, Manage Tasks, View Reports

### User Dashboard  
- Greeting: similar to admin
- 3-section layout: Assigned Tasks (table), Send Message (form), History (table with tabs)

### CRUD Pages (Businesses, Users, Tasks)
- Page header with title + "Add New" button (right)
- Search/filter bar below header
- Table with action columns
- Create/Edit in modal overlays

---

## Responsive Behavior

**Breakpoints:**
- Mobile: base (< 768px)
- Tablet: md (768px+)
- Desktop: lg (1024px+)

**Mobile Adaptations:**
- Sidebar becomes hamburger menu
- Tables scroll horizontally or stack vertically (for simple data)
- Dashboard cards: single column
- Forms: full-width inputs
- Reduce padding/margins by 50%

---

## Accessibility

- All interactive elements have visible focus states (ring-2)
- Form labels always present and associated
- Error messages announced and visible
- Sufficient color contrast for all text
- Skip navigation link for keyboard users
- ARIA labels for icon-only buttons

---

## Animations

**Minimal approach:**
- Hover states: subtle scale (scale-105) or shadow changes
- Modal entry: fade-in (200ms)
- Loading spinners: simple rotation for async operations
- No decorative animations

---

## Images

**No hero images** - This is a dashboard application, not a marketing site.

**Image usage:**
- Logo in top navigation (h-8 to h-10)
- Empty state illustrations (centered, max-w-sm)
- User avatars in profile areas (rounded-full, w-10 h-10)
- Preview thumbnails for uploaded media in message composer (max-w-xs, rounded-lg)