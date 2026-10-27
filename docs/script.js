(function () {
  "use strict";

  /* ---------- 导航滚动态 ---------- */
  var nav = document.getElementById("nav");
  function onScroll() {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 12);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* ---------- 移动端菜单 ---------- */
  var toggle = document.getElementById("navToggle");
  var links = document.getElementById("navLinks");

  function closeMenu() {
    if (!links || !toggle) return;
    links.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    links.addEventListener("click", function (e) {
      if (e.target instanceof HTMLAnchorElement) closeMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });
  }

  /* ---------- 滚动入场 ---------- */
  var items = document.querySelectorAll(".reveal");

  if (!("IntersectionObserver" in window)) {
    items.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var siblings = Array.prototype.filter.call(
          el.parentNode.children,
          function (n) { return n.classList && n.classList.contains("reveal"); }
        );
        var idx = Math.max(0, siblings.indexOf(el));
        el.style.transitionDelay = Math.min(idx, 6) * 70 + "ms";
        el.classList.add("is-in");
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------- 安装方式切换 ---------- */
  var tabs = document.querySelectorAll(".tab");
  var panels = document.querySelectorAll(".code[data-panel]");

  function activate(name) {
    tabs.forEach(function (t) {
      var on = t.dataset.tab === name;
      t.classList.toggle("is-active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach(function (p) {
      var on = p.dataset.panel === name;
      p.hidden = !on;
    });
  }

  tabs.forEach(function (t) {
    t.addEventListener("click", function () { activate(t.dataset.tab); });
  });

  /* ---------- 复制命令 ---------- */
  var copyBtn = document.getElementById("copyBtn");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var panel = document.querySelector('.code[data-panel]:not([hidden])');
      if (!panel) return;
      var text = panel.innerText.replace(/\u00a0/g, " ").trim();
      var label = copyBtn.querySelector("span");
      var done = function () {
        copyBtn.classList.add("is-done");
        if (label) label.textContent = "已复制";
        window.setTimeout(function () {
          copyBtn.classList.remove("is-done");
          if (label) label.textContent = "复制";
        }, 1800);
      };

      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }

      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (err) { /* 忽略 */ }
        document.body.removeChild(ta);
      }
    });
  }

  /* ---------- 页脚年份 ---------- */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
