/* coffeejev.space — language boundary layer.
 *
 * The site publishes an English tree for the design spec only (/spec/en/…).
 * Carbon, commercial, method and the app page exist in Chinese only. That is a
 * content gap, not something a script can translate, so this file makes the
 * boundary explicit instead of letting a click silently drop you into Chinese:
 *
 *   - ?lang=en is honoured once and then removed from the address bar
 *   - in English mode, a Chinese spec page redirects to its English twin
 *   - any other Chinese-only page shows a one-line notice with a way back
 *   - clicking the 中文 switch clears the stored preference
 */
(function () {
  'use strict';
  var KEY = 'cjv-lang';
  var p = location.pathname;
  var inEnTree = /\/spec\/en\//.test(p);
  var inSpecZh = /\/spec\/(?:index\.html|[a-z]+\.html)$/.test(p) || /\/spec\/$/.test(p);

  // ---- read ?lang=, then strip it so it cannot outvote the switch
  try {
    var q = new URLSearchParams(location.search).get('lang');
    if (q === 'en' || q === 'zh') {
      localStorage.setItem(KEY, q);
      var u = new URL(location.href);
      u.searchParams.delete('lang');
      history.replaceState(null, '', u.pathname + (u.search || '') + u.hash);
    }
  } catch (e) { /* private mode */ }

  // ---- the English tree sets the preference by existing
  if (inEnTree) {
    try { localStorage.setItem(KEY, 'en'); } catch (e) {}
    return;
  }

  var lang = 'zh';
  try { lang = localStorage.getItem(KEY) || 'zh'; } catch (e) {}
  if (lang !== 'en') return;

  // ---- English mode, Chinese spec page: send to the English twin
  if (inSpecZh) {
    var file = p.split('/').pop() || 'index.html';
    location.replace('en/' + file);
    return;
  }

  // ---- English mode, page that has no English version: say so, once
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

  // ---- clicking any 中文 switch clears the preference
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a');
    if (!a) return;
    if ((a.textContent || '').trim() === '中文') {
      try { localStorage.setItem(KEY, 'zh'); } catch (err) {}
    }
  }, true);
})();
