/**
 * Mobile Menu Auto-Hide on Scroll
 * Closes offcanvas menu when user scrolls the page
 */
document.addEventListener("DOMContentLoaded", function() {
  const el = document.getElementById("mobileMenu");
  if (!el) return;

  // Helper to get Bootstrap Offcanvas instance
  const inst = () => bootstrap.Offcanvas.getInstance(el) || new bootstrap.Offcanvas(el, { backdrop: true, scroll: false });

  let lastScrollY = window.scrollY;

  window.addEventListener("scroll", function() {
    const oc = inst();

    // Check if offcanvas is open and scroll delta > 10px
    if (el.classList.contains("show") && Math.abs(window.scrollY - lastScrollY) > 10) {
      oc.hide();
    }

    lastScrollY = window.scrollY;
  }, { passive: true });
});
