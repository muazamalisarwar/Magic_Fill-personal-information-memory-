/* global gsap, ScrollTrigger, Lenis */
import { sporeCanvas, initGlobalAmbientParticles } from "./particleCanvas.js";

(function () {
  "use strict";

  // Hero Video Showcase: GSAP 3D scroll tilt
  // On XL: starts scaled 0.8, rotationX 10, top -250 → scrolls to normal
  // On < XL: starts scaled 0.8, rotationX 15 → scrolls to normal
  function heroVideo() {
    const mm = gsap.matchMedia();
    const gsapVideoShowcase = document.querySelectorAll(
      "[data-gsap-video-showcase]",
    );
    if (!gsapVideoShowcase.length) return;

    gsapVideoShowcase.forEach((el) => {
      mm.add("(min-width: 1280px)", () => {
        gsap.set(el, { scale: 0.8, rotationX: 10, top: -250 });
        gsap.to(el, {
          scrollTrigger: {
            trigger: el,
            start: "20% 95%",
            end: "0% 30%",
            scrub: true,
            markers: false,
          },
          scale: 1,
          rotationX: 0,
          top: 0,
          ease: "none",
        });
      });

      mm.add("(max-width: 1279px)", () => {
        gsap.set(el, { scale: 0.8, rotationX: 15 });
        gsap.to(el, {
          scrollTrigger: {
            trigger: el,
            start: "20% 95%",
            end: "0% 40%",
            scrub: true,
          },
          scale: 1,
          rotationX: 0,
          ease: "none",
        });
      });
    });
  }

  // Trusted Partners: animated cycling brand logos
  function updateTrustedPartners() {
    const partners = document.querySelector("[data-trusted-brands-images]");
    if (!partners) return;

    const images = JSON.parse(partners.dataset.trustedBrandsImages);
    const MAX = 7;

    function getRandomImages(list) {
      return [...list].sort(() => 0.5 - Math.random()).slice(0, MAX);
    }

    function render(list) {
      partners.textContent = "";
      const frag = document.createDocumentFragment();
      list.forEach((src) => {
        const img = document.createElement("img");
        img.src = src;
        img.alt = "Trusted Brand";
        img.draggable = false;
        frag.appendChild(img);
      });
      partners.appendChild(frag);
    }

    function animate() {
      const selected = getRandomImages(images);
      render(selected);
      const imgs = partners.children;

      gsap.fromTo(
        imgs,
        { opacity: 0, filter: "blur(10px)", y: -30 },
        { opacity: 1, filter: "blur(0px)", y: 0, duration: 0.9, stagger: 0.15 },
      );

      gsap.to(imgs, {
        opacity: 0,
        filter: "blur(10px)",
        y: 20,
        duration: 0.9,
        delay: 3,
        stagger: 0.15,
        onComplete: animate,
      });
    }

    animate();
  }

  // Particle spore canvas effect
  function sporesEffect() {
    const targetElementClassName = ".heroSporeCanvas";
    sporeCanvas(
      targetElementClassName,
      140, // particle count
      0.2, // min size
      1.6, // max size
      0.0, // min speed
      0.1, // max speed
      800, // canvas size
    );
  }

  // Pricing toggle: Monthly ↔ Yearly with animated transitions
  // Uses a hidden checkbox input with data-pricing-toggle
  // Labels with .price-toggler-btn get .active class
  // Price spans with data-price-tag-monthly / data-price-tag-yearly get .active / .inactive
  function pricingToggle() {
    const toggle = document.querySelector("[data-pricing-toggle]");
    const labels = document.querySelectorAll(".price-toggler-btn");
    if (!toggle) return;

    toggle.addEventListener("change", (e) => {
      const isYearly = e.target.checked;

      // Toggle label active states
      if (isYearly) {
        labels[0]?.classList.remove("active");
        labels[1]?.classList.add("active");
      } else {
        labels[0]?.classList.add("active");
        labels[1]?.classList.remove("active");
      }

      const monthlyElements = document.querySelectorAll(
        "[data-price-tag-monthly]",
      );
      const yearlyElements = document.querySelectorAll(
        "[data-price-tag-yearly]",
      );
      const elementsToHide = isYearly ? monthlyElements : yearlyElements;
      const elementsToShow = isYearly ? yearlyElements : monthlyElements;

      elementsToHide.forEach((el, index) => {
        setTimeout(() => {
          el.classList.remove("active");
          el.classList.add("inactive");
        }, index * 150);
      });

      elementsToShow.forEach((el, index) => {
        setTimeout(() => {
          el.classList.add("active");
          el.classList.remove("inactive");
        }, index * 150);
      });
    });
  }

  // 1. Reading Scroll Progress Bar & Floating Back-To-Top Pill
  function initScrollProgressAndBackToTop() {
    const progressBar = document.getElementById("scrollProgressBar");
    const topBtn = document.getElementById("scrollToTopBtn");
    const progressRing = document.getElementById("scrollRingProgress");
    const circumference = 2 * Math.PI * 18; // approx 113.097

    function updateProgress() {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const currentScroll = window.scrollY;
      const progress = scrollHeight > 0 ? Math.min(Math.max(currentScroll / scrollHeight, 0), 1) : 0;
      const pct = (progress * 100).toFixed(1);

      if (progressBar) {
        progressBar.style.width = `${pct}%`;
      }

      if (progressRing) {
        const offset = circumference - (progress * circumference);
        progressRing.style.strokeDashoffset = `${offset}`;
      }

      if (topBtn) {
        if (currentScroll > 280) {
          topBtn.classList.remove("opacity-0", "translate-y-4", "pointer-events-none");
          topBtn.classList.add("opacity-100", "translate-y-0");
        } else {
          topBtn.classList.add("opacity-0", "translate-y-4", "pointer-events-none");
          topBtn.classList.remove("opacity-100", "translate-y-0");
        }
      }
    }

    window.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();

    if (topBtn) {
      topBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }
  }

  // 2. Interactive Card Spotlight Glow & Spatial 3D Tilt
  function initCardSpotlightAndTilt() {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const cards = document.querySelectorAll("[data-card-spotlight], [data-tilt], .card-interactive, .spotlight-card");

    cards.forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        card.style.setProperty("--mouse-x", `${x}px`);
        card.style.setProperty("--mouse-y", `${y}px`);

        if (!prefersReducedMotion && (card.hasAttribute("data-tilt") || card.classList.contains("tilt-card"))) {
          const xPct = (x / rect.width) - 0.5;
          const yPct = (y / rect.height) - 0.5;
          card.style.transform = `perspective(1000px) rotateX(${-yPct * 6}deg) rotateY(${xPct * 6}deg) translateY(-3px)`;
        }
      });

      card.addEventListener("mouseleave", () => {
        if (!prefersReducedMotion && (card.hasAttribute("data-tilt") || card.classList.contains("tilt-card"))) {
          card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)";
        }
      });
    });
  }

  // 3. Staggered Entrance Reveal on Scroll
  function initScrollReveal() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.querySelectorAll(".reveal-on-scroll, [data-reveal]").forEach((el) => {
        el.classList.add("is-revealed");
      });
      return;
    }

    const revealElements = document.querySelectorAll(".reveal-on-scroll, [data-reveal]");
    if (!revealElements.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -60px 0px", threshold: 0.1 }
    );

    revealElements.forEach((el) => observer.observe(el));
  }

  function init() {
    gsap.registerPlugin(ScrollTrigger);
    // Init Lenis smooth scroll
    new Lenis({ autoRaf: true });

    heroVideo();
    updateTrustedPartners();
    // Ambient dots and AI-pattern canvases removed for clean production look
    pricingToggle();
    initScrollProgressAndBackToTop();
    initCardSpotlightAndTilt();
    initScrollReveal();
  }

  // Run immediately — module scripts are deferred, DOM is already ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Refresh ScrollTrigger on resize (debounced)
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (typeof ScrollTrigger !== "undefined") {
        ScrollTrigger.refresh();
      }
    }, 250);
  });
})();
