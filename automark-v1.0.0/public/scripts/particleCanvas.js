"use strict";

/**
 * Magic Fill — Ambient Dynamic Particle & Spatial Aurora System
 * Features:
 * - Theme-reactive palettes (Midnight Dark with Lime #B7F34A & Light with Crisp Emerald #4D7C0F)
 * - Interactive mouse attraction & constellation filaments
 * - Subtle scroll-linked parallax motion
 * - Reduced motion accessibility & tab-visibility CPU throttling (0% background CPU)
 */

function isLightTheme() {
  return (
    document.documentElement.getAttribute("data-theme") === "light" ||
    document.documentElement.classList.contains("light-theme")
  );
}

function getThemePalette() {
  if (isLightTheme()) {
    // Light Mode: Fresh sage, emerald #4D7C0F, sky blue, and slate constellation
    return {
      particleColors: [
        "rgba(77, 124, 15, 0.65)",   // Crisp Forest Emerald
        "rgba(14, 165, 233, 0.50)",  // Sky
        "rgba(99, 102, 241, 0.45)",  // Soft Indigo
        "rgba(16, 185, 129, 0.45)",  // Mint Spark
        "rgba(100, 116, 139, 0.35)", // Subtle Slate
      ],
      lineColor: "rgba(77, 124, 15, 0.08)",
      cursorLineColor: "rgba(77, 124, 15, 0.18)",
      maxDist: 110,
    };
  } else {
    // Dark Mode: Deep cosmic starlight, signature Lime #B7F34A, aurora emerald, and electric cyan
    return {
      particleColors: [
        "rgba(183, 243, 74, 0.75)",  // Signature Lime Accent
        "rgba(255, 255, 255, 0.70)", // Crisp Starlight
        "rgba(52, 211, 153, 0.55)",  // Aurora Emerald
        "rgba(56, 189, 248, 0.50)",  // Electric Cyan
        "rgba(192, 132, 252, 0.40)", // Amethyst Glow
      ],
      lineColor: "rgba(183, 243, 74, 0.08)",
      cursorLineColor: "rgba(183, 243, 74, 0.22)",
      maxDist: 125,
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

  // Mouse interactivity tracking
  const mouse = {
    x: -1000,
    y: -1000,
    active: false,
    radius: 120,
  };

  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.active = true;
  });

  window.addEventListener("mouseleave", () => {
    mouse.active = false;
  });

  // Scroll parallax tracking
  let lastScrollY = window.scrollY;
  let scrollDeltaY = 0;
  window.addEventListener("scroll", () => {
    const currentY = window.scrollY;
    scrollDeltaY = (currentY - lastScrollY) * 0.12;
    lastScrollY = currentY;
  }, { passive: true });

  // Low particle counts for lightweight 60fps performance without taxing GPU/CPU
  const isMobile = window.innerWidth < 768;
  const particleCount = isMobile ? 18 : 36;

  class AmbientParticle {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = initial ? Math.random() * width : Math.random() * width;
      this.y = initial ? Math.random() * height : (Math.random() > 0.5 ? -10 : height + 10);
      this.baseRadius = Math.random() * 1.6 + 1.1; // 1.1px to 2.7px
      this.radius = this.baseRadius;
      this.vx = (Math.random() - 0.5) * 0.32;
      this.vy = (Math.random() - 0.5) * 0.32;
      this.pulseSpeed = Math.random() * 0.02 + 0.01;
      this.pulsePhase = Math.random() * Math.PI * 2;
      this.color = palette.particleColors[Math.floor(Math.random() * palette.particleColors.length)];
    }

    update() {
      if (prefersReducedMotion) return;

      this.x += this.vx;
      this.y += this.vy;

      // Apply subtle scroll parallax drift
      if (Math.abs(scrollDeltaY) > 0.01) {
        this.y -= scrollDeltaY;
      }

      // Interactive mouse attraction / repulsion
      if (mouse.active) {
        const dx = this.x - mouse.x;
        const dy = this.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < mouse.radius && dist > 1) {
          const force = (mouse.radius - dist) / mouse.radius;
          // Soft elastic deflection away from cursor
          this.x += (dx / dist) * force * 1.6;
          this.y += (dy / dist) * force * 1.6;
        }
      }

      // Breathing radius pulse
      this.pulsePhase += this.pulseSpeed;
      this.radius = this.baseRadius + Math.sin(this.pulsePhase) * 0.45;

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

    // Fade scroll delta smoothly back to zero
    scrollDeltaY *= 0.88;

    const len = particles.length;
    const maxD = palette.maxDist;

    for (let i = 0; i < len; i++) {
      const p1 = particles[i];
      p1.update();
      p1.draw();

      // Connect filaments between neighboring particles
      for (let j = i + 1; j < len; j++) {
        const p2 = particles[j];
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < maxD) {
          const alpha = (1 - dist / maxD) * 0.12;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = isLightTheme()
            ? `rgba(77, 124, 15, ${alpha.toFixed(3)})`
            : `rgba(183, 243, 74, ${alpha.toFixed(3)})`;
          ctx.lineWidth = 0.85;
          ctx.stroke();
        }
      }

      // Interactive filament connect to mouse cursor
      if (mouse.active) {
        const mdx = p1.x - mouse.x;
        const mdy = p1.y - mouse.y;
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist < 100) {
          const mAlpha = (1 - mdist / 100) * 0.22;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.strokeStyle = isLightTheme()
            ? `rgba(77, 124, 15, ${mAlpha.toFixed(3)})`
            : `rgba(183, 243, 74, ${mAlpha.toFixed(3)})`;
          ctx.lineWidth = 1;
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

  // Reactive Theme Change Handler
  function updatePalette() {
    palette = getThemePalette();
    particles.forEach((p) => {
      p.color = palette.particleColors[Math.floor(Math.random() * palette.particleColors.length)];
    });
  }

  window.addEventListener("themechange", updatePalette);
  window.addEventListener("magic-fill-theme-change", updatePalette);

  // Tab Visibility CPU Throttling
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
 * Legacy sporeCanvas export for existing sections
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
          "rgba(77, 124, 15, 0.65)",
          "rgba(99, 102, 241, 0.60)",
          "rgba(14, 165, 233, 0.55)",
          "rgba(16, 185, 129, 0.50)",
        ]
      : [
          "rgba(183, 243, 74, 0.75)",
          "rgba(255, 255, 255, 0.70)",
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
