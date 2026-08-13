/* Generic dropdown manager — handles the nav's Connect, Language, and Preferences menus.
   Each trigger is `[data-dropdown-toggle]` with a sibling `.dropdown-menu`. */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    var toggles = document.querySelectorAll("[data-dropdown-toggle]");

    function closeAll(except) {
      document.querySelectorAll(".dropdown-menu.open").forEach(function (m) {
        if (m !== except) m.classList.remove("open");
      });
    }

    toggles.forEach(function (toggle) {
      var menu = toggle.parentElement.querySelector(".dropdown-menu");
      if (!menu) return;

      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        var willOpen = !menu.classList.contains("open");
        closeAll();
        if (willOpen) menu.classList.add("open");
      });
      menu.addEventListener("click", function (e) {
        e.stopPropagation();
      });
    });

    document.addEventListener("click", function () { closeAll(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAll();
    });
  });
})();
