/* Theme engine: light / dark / system — persisted in localStorage */
(function () {
  var STORAGE_KEY = "wheat-theme";
  var root = document.documentElement;
  var media = window.matchMedia("(prefers-color-scheme: dark)");

  function systemPref() {
    return media.matches ? "dark" : "light";
  }

  function apply(mode) {
    var resolved = mode === "system" ? systemPref() : mode;
    root.setAttribute("data-theme", resolved);
    document.querySelectorAll("[data-theme-btn]").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-theme-btn") === mode);
    });
    document.querySelectorAll("[data-theme-label]").forEach(function (el) {
      el.textContent = LABELS[mode] || mode;
    });
    document.querySelectorAll("[data-theme-icon]").forEach(function (el) {
      el.innerHTML = ICONS[mode] || ICONS.system;
    });
  }

  var LABELS = { light: "Light", dark: "Dark", system: "System" };
  var ICONS = {
    light: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    dark: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    system: '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>'
  };

  function setTheme(mode) {
    localStorage.setItem(STORAGE_KEY, mode);
    apply(mode);
  }

  function getStored() {
    return localStorage.getItem(STORAGE_KEY) || "system";
  }

  // Init before paint-ish
  apply(getStored());

  media.addEventListener("change", function () {
    if (getStored() === "system") apply("system");
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-theme-btn]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setTheme(btn.getAttribute("data-theme-btn"));
      });
    });

    // reveal transition only after first paint to avoid flash-animate on load
    requestAnimationFrame(function () {
      root.classList.add("theme-ready");
    });
  });

  window.WheatTheme = { set: setTheme, get: getStored };
})();
