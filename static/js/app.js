(() => {
  const toggles = [...document.querySelectorAll('[data-mobile-menu]')];
  const sidebar = document.querySelector('#sidebar');
  const overlay = document.querySelector('#overlay');
  let previousFocus = null;

  function setOpen(open) {
    if (!sidebar) return;
    sidebar.classList.toggle('mobile-open', open);
    overlay?.classList.toggle('visible', open);
    toggles.forEach((button) => button.setAttribute('aria-expanded', String(open)));
    document.body.classList.toggle('menu-is-open', open);
    if (open) {
      previousFocus = document.activeElement;
      sidebar.querySelector('.side-nav a')?.focus({ preventScroll: true });
    } else if (previousFocus && sidebar.contains(document.activeElement)) {
      previousFocus.focus?.({ preventScroll: true });
    }
  }

  toggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
      setOpen(!sidebar?.classList.contains('mobile-open'));
    });
  });
  overlay?.addEventListener('click', () => setOpen(false));

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(false);
    if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
      event.preventDefault();
      document.querySelector('.search input')?.focus();
    }
  });

  sidebar?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setOpen(false));
  });

  // Keep native scrolling and navigation. Reversible CSS transitions honour reduced motion.
  const motion = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  if (!motion?.matches) {
    document.querySelectorAll('.stat-card,.article-card,.member-card,.task-card').forEach((card) => {
      card.addEventListener('pointerdown', () => card.classList.add('is-pressing'));
      for (const event of ['pointerup', 'pointercancel', 'pointerleave']) {
        card.addEventListener(event, () => card.classList.remove('is-pressing'));
      }
    });
  }
})();
document.querySelectorAll("[data-copy-code]").forEach((button) => {
  button.addEventListener("click", async () => {
    const code = button.closest(".code-panel")?.querySelector("pre code")?.textContent || "";
    try {
      await navigator.clipboard.writeText(code);
      button.textContent = "Скопировано ✓";
    } catch (_) {
      button.textContent = "Не удалось скопировать";
    }
    window.setTimeout(() => { button.textContent = "Копировать код"; }, 2000);
  });
});
