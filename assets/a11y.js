/** Small accessibility layer: accordion semantics + Escape to close menus.
 *  The nav panels open on hover via CSS; this gives them keyboard/screen-reader
 *  state without changing the visual behaviour. */
(function () {
  'use strict';
  var groups = Array.prototype.slice.call(document.querySelectorAll('.menu'));
  if (!groups.length) return;

  groups.forEach(function (g) {
    var trigger = g.querySelector(':scope > a');
    var panel = g.querySelector('.menu-panel');
    if (!trigger || !panel) return;
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', panel.id || (panel.id = 'menu-' + Math.random().toString(36).slice(2, 8)));

    function set(open) {
      trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    g.addEventListener('mouseenter', function () { set(true); });
    g.addEventListener('mouseleave', function () { set(false); });
    g.addEventListener('focusin', function () { set(true); });
    g.addEventListener('focusout', function (e) {
      if (!g.contains(e.relatedTarget)) set(false);
    });
    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault();
        panel.classList.add('kb-open');
        set(true);
        var first = panel.querySelector('a');
        if (first) first.focus();
      }
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    groups.forEach(function (g) {
      g.querySelectorAll('.kb-open').forEach(function (p) { p.classList.remove('kb-open'); });
      var t = g.querySelector(':scope > a');
      if (t && g.contains(document.activeElement)) {
        t.setAttribute('aria-expanded', 'false');
        t.focus();
      }
    });
  });

  var style = document.createElement('style');
  style.textContent = '.kb-open{display:block!important;visibility:visible!important;opacity:1!important}';
  document.head.appendChild(style);
})();
