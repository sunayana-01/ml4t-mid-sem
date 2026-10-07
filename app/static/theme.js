// Dark mode toggle, shared by index.html and practice.html.
//
// Persisted in localStorage so the choice survives navigation between the
// selection page and the (server-rendered, one-per-question) practice pages.
// The actual flash-of-wrong-theme prevention happens via a tiny inline
// snippet in each page's <head> (must run before first paint, so it can't
// live in this externally-loaded file) - see THEME_INIT_SNIPPET below for
// the shared source of truth those inline copies are kept in sync with.
const ML4T_THEME_KEY = 'ml4t-theme';

function ml4tApplyTheme(isDark) {
  document.documentElement.classList.toggle('dark', isDark);
}

function ml4tToggleTheme() {
  const isDark = !document.documentElement.classList.contains('dark');
  localStorage.setItem(ML4T_THEME_KEY, isDark ? 'dark' : 'light');
  ml4tApplyTheme(isDark);
  ml4tUpdateToggleButton();
}

function ml4tUpdateToggleButton() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const isDark = document.documentElement.classList.contains('dark');
  btn.textContent = isDark ? '\u2600\ufe0f Light' : '\ud83c\udf19 Dark';
  btn.setAttribute('aria-pressed', String(isDark));
}

ml4tUpdateToggleButton();
