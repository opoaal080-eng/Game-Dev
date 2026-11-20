(() => {
  const toggle = document.querySelector('#menuToggle');
  const sidebar = document.querySelector('#sidebar');
  const overlay = document.querySelector('#overlay');
  function closeMenu() {
    sidebar?.classList.remove('mobile-open');
    overlay?.classList.remove('visible');
    toggle?.setAttribute('aria-expanded', 'false');
  }
  toggle?.addEventListener('click', () => {
    const opened = sidebar.classList.toggle('mobile-open');
    overlay?.classList.toggle('visible', opened);
    toggle.setAttribute('aria-expanded', String(opened));
  });
  overlay?.addEventListener('click', closeMenu);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
    if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault();
      document.querySelector('.search input')?.focus();
    }
  });
})();
