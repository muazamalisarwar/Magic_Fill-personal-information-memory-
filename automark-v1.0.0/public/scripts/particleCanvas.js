"use strict";

/**
 * Magic Fill — Ambient Dynamic Particle System
 * Supports Light & Dark themes with theme-reactive palettes,
 * soft constellation filaments, visibility throttling, and zero-jank 60fps performance.
 */

function isLightTheme() {
  return (
    document.documentElement.getAttribute("data-theme") === "light" ||
    document.documentElement.classList.contains("light-theme")
  );
}

function getThemePalette() {
  if (isLightTheme()) {
    // Light Mode: Atmospheric pastel orbs with soft lilac, sky blue, indigo, and emerald shimmer
    return {
      particleColors: [
        "rgba(132, 80, 255, 0.50)", // Violet
        "rgba(14, 165, 233, 0.45)",  // Sky
        "rgba(99, 102, 241, 0.45)",  // Indigo
        "rgba(16, 185, 129, 0.38)",  // Emerald
        "rgba(244, 63, 94, 0.32)",   // Soft Rose
      ],
      lineColor: "rgba(132, 80, 255, 0.08)",
      glowColor: "rgba(132, 80, 255, 0.25)",
      maxDist: 110,
    };
  } else {
    // Dark Mode: Deep cosmic starlight, nebula violet, electric cyan, and aurora emerald
    return {
      particleColors: [
        "rgba(255, 255, 255, 0.70)", // Starlight
        "rgba(168, 85, 247, 0.55)", // Nebula Violet
        "rgba(56, 189, 248, 0.50)",  // Electric Cyan
        "rgba(52, 211, 153, 0.45)",  // Emerald Spark
        "rgba(192, 132, 252, 0.45)", // Amethyst
      ],
      lineColor: "rgba(168, 85, 247, 0.09)",
      glowColor: "rgba(168, 85, 247, 0.30)",
      maxDist: 120,
    };
  }
}

export function initGlobalAmbientParticles(canvasId = "globalAmbientParticles") {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Check prefers-reduced-motion
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  let palette = getThemePalette();

  // Low particle counts for lightweight 60fps performance without taxing GPU/CPU
  const isMobile = window.innerWidth < 768;
  const particleCount = isMobile ? 18 : 38;

  class AmbientParticle {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = initial ? Math.random() * width : Math.random() * width;
      this.y = initial ? Math.random() * height : (Math.random() > 0.5 ? -10 : height + 10);
      this.baseRadius = Math.random() * 1.8 + 1.1; // 1.1px to 2.9px
      this.radius = this.baseRadius;
      this.vx = (Math.random() - 0.5) * 0.35;
      this.vy = (Math.random() - 0.5) * 0.35;
      this.pulseSpeed = Math.random() * 0.02 + 0.01;
      this.pulsePhase = Math.random() * Math.PI * 2;
      this.color = palette.particleColors[Math.floor(Math.random() * palette.particleColors.length)];
    }

    update() {
      if (prefersReducedMotion) return;

      this.x += this.vx;
      this.y += this.vy;

      // Subtle breathing pulse
      this.pulsePhase += this.pulseSpeed;
      this.radius = this.baseRadius + Math.sin(this.pulsePhase) * 0.5;

      // Wrap-around screen bounds
      if (this.x < -15) this.x = width + 15;
      else if (this.x > width + 15) this.x = -15;

      if (this.y < -15) this.y = height + 15;
      else if (this.y > height + 15) this.y = -15;
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, Math.max(0.6, this.radius), 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    }
  }

  const particles = [];
  for (let i = 0; i < particleCount; i++) {
    particles.push(new AmbientParticle());
  }

  let animationFrameId = null;
  let isRunning = true;

  function render() {
    if (!isRunning) return;

    ctx.clearRect(0, 0, width, height);

    // Draw delicate constellation filaments between particles within proximity
    const len = particles.length;
    const maxD = palette.maxDist;

    for (let i = 0; i < len; i++) {
      const p1 = particles[i];
      p1.update();
      p1.draw();

      for (let j = i + 1; j < len; j++) {
        const p2 = particles[j];
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < maxD) {
          const alpha = (1 - dist / maxD) * (isLightTheme() ? 0.08 : 0.09);
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = isLightTheme()
            ? `rgba(132, 80, 255, ${alpha.toFixed(3)})`
            : `rgba(168, 85, 247, ${alpha.toFixed(3)})`;
          ctx.lineWidth = 0.85;
          ctx.stroke();
        }
      }
    }

    animationFrameId = requestAnimationFrame(render);
  }

  render();

  // Debounced Window Resize Handler
  let resizeTimeout = null;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }, 150);
  });

  // Theme Change Event Listener
  window.addEventListener("themechange", () => {
    palette = getThemePalette();
    particles.forEach((p) => {
      p.color = palette.particleColors[Math.floor(Math.random() * palette.particleColors.length)];
    });
  });

  // Visibility Throttling (Pause animation when tab is inactive to preserve 0% CPU)
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      isRunning = false;
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    } else {
      isRunning = true;
      render();
    }
  });
}

/**
 * Legacy sporeCanvas export for existing inline sections
 */
export function sporeCanvas(
  targetElementClassName,
  particleCount = 100,
  particleMinSize = 0.5,
  particleMaxSize = 2.0,
  particleMinSpeed = 0.05,
  particleMaxSpeed = 0.5,
  canvasSize = 800,
) {
  const canvasElements = document.querySelectorAll(targetElementClassName);
  if (!canvasElements.length) return;

  function getThemeColors() {
    return isLightTheme()
      ? [
          "rgba(132, 80, 255, 0.65)",
          "rgba(99, 102, 241, 0.60)",
          "rgba(14, 165, 233, 0.55)",
          "rgba(16, 185, 129, 0.50)",
        ]
      : [
          "rgba(255, 255, 255, 0.75)",
          "rgba(192, 132, 252, 0.65)",
          "rgba(129, 140, 248, 0.65)",
          "rgba(56, 189, 248, 0.55)",
        ];
  }

  if (window.innerWidth < 768) {
    particleCount = Math.min(particleCount, 25);
    canvasSize = Math.min(canvasSize, 600);
  }

  canvasElements.forEach((canvas) => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvasSize;
    canvas.height = canvasSize;
    const particles = [];

    class Particle {
      constructor() {
        this.reset(true);
      }

      reset(initial = false) {
        this.x = Math.random() * canvas.width;
        this.y = initial ? Math.random() * canvas.height : canvas.height + Math.random() * 20;
        this.size = Math.random() * (particleMaxSize - particleMinSize) + particleMinSize;
        this.speedY = Math.random() * (particleMaxSpeed - particleMinSpeed) - particleMaxSpeed;
        const colors = getThemeColors();
        this.color = colors[Math.floor(Math.random() * colors.length)];
      }

      update() {
        this.y += this.speedY;
        if (this.y < -20) {
          this.reset(false);
        }
      }

      draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }
    canvas._particles = particles;

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((particle) => {
        particle.update();
        particle.draw();
      });
      requestAnimationFrame(animate);
    }

    animate();
  });
}
