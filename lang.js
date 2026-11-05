/* coffeejev.space — language boundary layer.
 *
 * The site publishes English trees for /spec/ (all pages) and /method/ (partial).
 * Everything else is Chinese only. This layer makes the boundary explicit
 * instead of letting a click silently drop you into Chinese:
 *
 *   - ?lang= is honoured once, then removed from the address bar
 *   - in English mode, a translated page redirects to its English twin
 *   - a page without an English version shows a one-line notice with a way back
 *   - English pages carry a floating 中文 switch
 *   - clicking any language control updates the stored preference
 */
(function () {
  'use strict';
  var KEY = 'cjv-lang';

  // which pages have an English twin
  var EN_READY = {
    spec: '*',
    method: '*',
    carbon: '*',
    commercial: '*',
    napell: ['index.html']   // app.html is the device mock, language-neutral
  };

  var p = location.pathname;
  var m = p.match(/\/(spec|method|carbon|commercial|napell)\/(en\/)?([^\/]*\.html)?$/);
  var tree = m ? m[1] : null;
  var inEnTree = !!m && !!m[2];

  function hasEnglish(file) {
    if (!tree) return false;
    var v = EN_READY[tree];
    return v === '*' || (v && v.indexOf(file) >= 0);
  }

  // ---- ?lang= once, then gone
  try {
    var q = new URLSearchParams(location.search).get('lang');
    if (q === 'en' || q === 'zh') {
      localStorage.setItem(KEY, q);
      var u = new URL(location.href);
      u.searchParams.delete('lang');
      history.replaceState(null, '', u.pathname + (u.search || '') + u.hash);
    }
  } catch (e) { /* private mode */ }

  if (inEnTree) { try { localStorage.setItem(KEY, 'en'); } catch (e) {} }

  var lang = 'zh';
  try { lang = localStorage.getItem(KEY) || 'zh'; } catch (e) {}

  // ---- language controls win over everything below
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-lang], a');
    if (!el) return;
    var chosen = el.getAttribute && el.getAttribute('data-lang');
    if (!chosen && (el.textContent || '').trim() === '中文') chosen = 'zh';
    if (!chosen) return;
    try { localStorage.setItem(KEY, chosen); } catch (err) {}
    var file = p.split('/').pop() || 'index.html';
    if (chosen === 'zh' && inEnTree) {
      e.preventDefault();
      location.href = '../' + file;
    } else if (chosen === 'en' && !inEnTree && hasEnglish(file)) {
      e.preventDefault();
      location.href = 'en/' + file;
    }
  }, true);

  // ---- English page: offer the way back to Chinese
  function backToChinese() {
    if (document.getElementById('cjv-zhpill')) return;
    var file = p.split('/').pop() || 'index.html';
    var a = document.createElement('a');
    a.id = 'cjv-zhpill';
    a.href = '../' + file;
    a.textContent = '中文';
    a.title = '这一页的中文版 / Chinese version';
    document.body.appendChild(a);
    var css = document.createElement('style');
    css.textContent =
      '#cjv-zhpill{position:fixed;right:20px;bottom:20px;z-index:2147483000;padding:8px 16px;border-radius:999px;' +
      'font:700 12.5px/1 -apple-system,"Segoe UI","PingFang SC",sans-serif;text-decoration:none;' +
      'color:#c9ffe9;background:rgba(10,14,18,.9);border:1px solid rgba(63,224,176,.45);' +
      'backdrop-filter:blur(8px);box-shadow:0 6px 20px rgba(0,0,0,.3)}' +
      '#cjv-zhpill:hover{background:rgba(0,196,140,.2)}';
    document.head.appendChild(css);

    // some pages carry a fixed call-to-action in the same corner; lift the pill
    // above whatever is already sitting there rather than covering it
    setTimeout(function () {
      var r = a.getBoundingClientRect();
      var bump = 0;
      var all = document.body.querySelectorAll('a, button, div');
      for (var i = 0; i < all.length; i++) {
        var el = all[i];
        if (el === a) continue;
        var cs = getComputedStyle(el);
        if (cs.position !== 'fixed' || cs.visibility === 'hidden' || cs.display === 'none') continue;
        var b = el.getBoundingClientRect();
        if (b.width === 0 || b.bottom < window.innerHeight - 120) continue;
        var overlaps = !(b.right < r.left - 4 || b.left > r.right + 4 ||
                         b.bottom < r.top - 4 || b.top > r.bottom + 4);
        if (overlaps) bump = Math.max(bump, r.bottom - b.top + 8);
      }
      if (bump) a.style.bottom = (20 + bump) + 'px';
    }, 120);
  }

  if (inEnTree) {
    if (document.body) backToChinese();
    else document.addEventListener('DOMContentLoaded', backToChinese);
    return;
  }

  if (lang !== 'en') return;

  // ---- English mode: go to the twin when it exists
  var file = p.split('/').pop() || 'index.html';
  if (tree && hasEnglish(file)) {
    location.replace('en/' + file);
    return;
  }
  // the single-page specification sits at the root, outside the /spec/ tree
  if (p.indexOf('/spec.html') === p.length - '/spec.html'.length) {
    location.replace('spec/en/spec.html');
    return;
  }

  // ---- otherwise say so, once
  function notice() {
    if (document.getElementById('cjv-langbar')) return;
    var bar = document.createElement('div');
    bar.id = 'cjv-langbar';
    bar.innerHTML =
      '<span>This section is not published in English yet · 本节暂无英文版</span>' +
      '<a href="/spec/en/index.html">English pages</a>' +
      '<button type="button" id="cjv-langbar-zh">中文</button>';
    document.body.appendChild(bar);
    var css = document.createElement('style');
    css.textContent =
      '#cjv-langbar{position:fixed;top:0;left:0;right:0;z-index:2147483000;display:flex;align-items:center;' +
      'gap:14px;padding:9px 16px;background:rgba(9,13,18,.96);color:#cfe6df;border-bottom:1px solid rgba(63,224,176,.35);' +
      'font:600 12.5px/1.4 -apple-system,"Segoe UI","PingFang SC",sans-serif;backdrop-filter:blur(8px)}' +
      '#cjv-langbar span{flex:1}#cjv-langbar a{color:#8ff0cf;text-decoration:none;white-space:nowrap}' +
      '#cjv-langbar button{font:inherit;padding:4px 11px;border-radius:999px;cursor:pointer;' +
      'border:1px solid rgba(63,224,176,.4);background:rgba(0,196,140,.14);color:#c9ffe9}' +
      'body{padding-top:38px !important}';
    document.head.appendChild(css);
    document.getElementById('cjv-langbar-zh').addEventListener('click', function () {
      try { localStorage.setItem(KEY, 'zh'); } catch (e) {}
      location.reload();
    });
  }
  if (document.body) notice();
  else document.addEventListener('DOMContentLoaded', notice);
})();
