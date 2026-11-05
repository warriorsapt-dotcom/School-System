(() => {
  const key = 'school.appearance';
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let preference;
  try { preference = localStorage.getItem(key); } catch { /* Storage can be disabled. */ }

  function apply() {
    const theme = ['light', 'dark'].includes(preference) ? preference : (system.matches ? 'dark' : 'light');
    document.documentElement.dataset.bsTheme = theme;
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.themeChoice === theme));
    });
    if (window.Chart) {
      Chart.defaults.color = theme === 'dark' ? '#c4bfd0' : '#666';
      Chart.defaults.borderColor = theme === 'dark' ? '#393640' : 'rgba(0,0,0,.1)';
      Object.values(Chart.instances).forEach(chart => chart.update('none'));
    }
  }

  apply();
  system.addEventListener('change', apply);
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) { preference = event.newValue; apply(); }
  });
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
      button.addEventListener('click', () => {
        preference = button.dataset.themeChoice;
        try { localStorage.setItem(key, preference); } catch { /* Use the choice for this page. */ }
        apply();
      });
    });
  });
})();
