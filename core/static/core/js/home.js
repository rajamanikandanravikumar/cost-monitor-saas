// core/static/core/js/home.js
// Scroll-triggered reveal for feature cards using IntersectionObserver.

document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".feature-card");

  if (!("IntersectionObserver" in window) || cards.length === 0) {
    cards.forEach((card) => card.classList.add("visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add("visible"), index * 100);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );

  cards.forEach((card) => observer.observe(card));
});