"use strict";

/**
 * Magic Fill — Background Ambient Canvas Controller
 * Note: Floating dot grids and random particle animations have been permanently retired
 * in favor of a clean, high-contrast, production UI design system.
 */

export function isLightTheme() {
  return (
    document.documentElement.getAttribute("data-theme") === "light" ||
    document.documentElement.classList.contains("light-theme")
  );
}

export function initGlobalAmbientParticles() {
  return;
}

export function sporeCanvas() {
  return;
}
