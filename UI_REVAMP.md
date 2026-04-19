# UI Revamp: The Scrollytelling Evolution

This document outlines the strategy for transforming the Smart-Grid UI from a traditional dashboard into an immersive **scrollytelling experience**. We are moving away from modular cards toward a continuous narrative where data and story are inextricably linked.

## 1. Vision: "The Energy Narrative"

**The Story:** "Energy isn't just a number on a screen; it's the lifeblood of your home and industry. We're not just showing you data; we're telling the story of how your choices—and our intelligence—create a more sustainable and prosperous future."

- **Core Principle:** The user's scroll progress drives the narrative. 
- **No More Cards:** Traditional UI "containers" (Cards, StatCards) are removed. Data is presented as part of the environment or as floating narrative elements.
- **Content Integrity:** Every word of existing text is preserved but re-contextualized into "chapters" of the energy story.

---

## 2. The "Stage & Story" Architecture

The UI will be restructured into a two-layer system:

### 🎬 The Stage (Background / Sticky)
A full-screen, sticky container that serves as the visual anchor.
- **Dynamic Visuals:** High-quality "Energy Portraits" (images), SVG animations of power flows, and interactive charts.
- **Reactive State:** The Stage morphs as the user scrolls. For example, as you scroll past "Solar Impact," the background image shifts from a general facility view to a sun-drenched rooftop.

### 📖 The Story (Foreground / Scrolling)
A scrolling layer of narrative text and data points that floats over the Stage.
- **Chapters:** Each section of the current UI (e.g., "Latest Values," "Historical Context") becomes a narrative chapter.
- **Narrative Flow:** Text is presented in large, readable typography, often center-aligned or side-aligned to complement the Stage visuals.
- **Data Integration:** Key metrics (formerly in StatCards) are integrated directly into the sentences or appear as elegant, borderless overlays.

---

## 3. Narrative Arcs by Feature

### ⚡ Telemetry: "The Pulse of Power"
- **Intro:** A macro view of the site (Home or Factory).
- **The Heartbeat:** Scrolling reveals real-time metrics (Power, SoC) appearing as "vitals" over an image of the battery system.
- **The Memory:** As the user scrolls further, the "Stage" transitions into a large-scale history chart, showing the ebb and flow of energy over the last 24 hours.

### 💰 Financial Impact: "The Journey of a Dollar"
- **The Baseline:** "You could have spent $X..." — The Stage shows a representation of "Wasteful" grid reliance.
- **The Intervention:** "...but then we stepped in." — Visuals shift to show the Battery Policy in action.
- **The Result:** The final "Money Kept" figure is presented as a hero metric over a serene image of the saved environment (forests or clear skies).

### 🧠 Optimization: "The Silent Intelligence"
- **The Logic:** Scrollytelling through the decision-tree. Each scroll "tick" shows the AI weighing grid price vs. battery health.
- **The Action:** Visualizing the dispatcher sending commands to the edge gateway in real-time.

---

## 4. Technical Strategy

### 🛠 Tools
- **Framer Motion:** Utilizing `useScroll` and `useTransform` to map scroll position to Stage animations (opacity, scale, path-drawing).
- **CSS Sticky:** Ensuring the Stage remains fixed while the Story progresses.
- **Vanilla CSS:** To maintain the "Warm Grid" palette with sophisticated transitions without the clutter of card-based frameworks.

### 🎨 Visual Assets
- **Energy Portraits:** Implementation of high-resolution, thematic images that represent energy states (Sunlight, Wind, Battery cells, Industrial machinery).
- **Typography:** Shifting to a more editorial feel with variable font weights to distinguish between "Story" and "Data."

---

## 5. Implementation Roadmap

1.  **Refactor Layout:** Replace `PageHeader` and `Card` containers with a `ScrollyContainer` and `StorySection` components.
2.  **Stage Animation:** Implement the sticky "Stage" in `TelemetryPage` and `SavingsPage`.
3.  **Text Migration:** Map all existing text blocks to their new "Story" positions.
4.  **Polish:** Add "Scroll-to-Discover" cues and smooth transition interpolation.
