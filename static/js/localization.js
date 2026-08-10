/* Localization engine: swaps data-i18n text using JSON dictionaries in /static/locales/ */
(function () {
  var STORAGE_KEY = "wheat-lang";
  var RTL_LANGS = ["ar", "ur"];
  var LANGS = {
    en: "English",
    ar: "العربية",
    fr: "Français",
    es: "Español",
    de: "Deutsch",
    pt: "Português",
    ru: "Русский",
    zh: "中文",
    hi: "हिन्दी",
    ur: "اردو",
    tr: "Türkçe",
    id: "Bahasa Indonesia"
  };
  var cache = {};

  function getStored() {
    return localStorage.getItem(STORAGE_KEY) || "en";
  }

  function fetchDict(lang) {
    if (cache[lang]) return Promise.resolve(cache[lang]);
    return fetch("/static/locales/" + lang + ".json")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        cache[lang] = data;
        return data;
      })
      .catch(function () { return {}; });
  }

  function applyDict(dict, lang) {
    document.documentElement.lang = lang;
    document.documentElement.dir = RTL_LANGS.indexOf(lang) > -1 ? "rtl" : "ltr";

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (dict[key] != null) el.textContent = dict[key];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-placeholder");
      if (dict[key] != null) el.setAttribute("placeholder", dict[key]);
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-html");
      if (dict[key] != null) el.innerHTML = dict[key];
    });

    document.querySelectorAll("[data-lang-label]").forEach(function (el) {
      el.textContent = LANGS[lang] || lang.toUpperCase();
    });
    document.querySelectorAll("[data-lang-btn]").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-lang-btn") === lang);
    });
  }

  function setLang(lang) {
    localStorage.setItem(STORAGE_KEY, lang);
    fetchDict(lang).then(function (dict) {
      applyDict(dict, lang);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setLang(getStored());

    document.querySelectorAll("[data-lang-btn]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setLang(btn.getAttribute("data-lang-btn"));
        var menu = btn.closest(".lang-menu");
        if (menu) menu.classList.remove("open");
      });
    });

    var langToggle = document.querySelector("[data-lang-toggle]");
    var langMenu = document.querySelector(".lang-menu");
    if (langToggle && langMenu) {
      langToggle.addEventListener("click", function (e) {
        e.stopPropagation();
        langMenu.classList.toggle("open");
        var themeMenu = document.querySelector(".theme-menu");
        if (themeMenu) themeMenu.classList.remove("open");
      });
      document.addEventListener("click", function () {
        langMenu.classList.remove("open");
      });
    }
  });

  window.WheatI18n = { set: setLang, get: getStored, langs: LANGS };
})();
