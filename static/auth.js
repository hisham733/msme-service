/* Shared login helper (T-047).
 * - adds X-CSRF-Token to every same-origin non-GET fetch
 * - sends a 401 back to /login
 * - shows the signed-in user and hides [data-role="admin"] for editors
 */
(function () {
  if (window.__msmeAuthLoaded) return;
  window.__msmeAuthLoaded = true;

  function cookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/[.$?*|{}()[\]\\\/+^]/g, '\\$&') + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  var csrf = cookie('msme_csrf');
  var nativeFetch = window.fetch.bind(window);
  var mePromise = null;

  window.fetch = function (input, init) {
    init = init || {};
    var method = String(init.method || (input && input.method) || 'GET').toUpperCase();
    var target = typeof input === 'string' ? input : ((input && input.url) || '');
    var sameOrigin = !/^https?:\/\//i.test(target) || target.indexOf(location.origin) === 0;
    if (sameOrigin && method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS' && csrf) {
      var headers = new Headers(init.headers || {});
      if (!headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', csrf);
      init = Object.assign({}, init, { headers: headers });
    }
    return nativeFetch(input, init).then(function (response) {
      if (response.status === 401) {
        var next = encodeURIComponent(location.pathname + location.search);
        location.href = '/login?next=' + next;
      }
      return response;
    });
  };

  function currentUser() {
    if (!mePromise) {
      mePromise = window.fetch('/api/auth/me').then(function (r) {
        return r.ok ? r.json() : null;
      }).then(function (me) {
        if (!me) return null;
        window.MSME_USER = me;
        if (me.csrf) csrf = me.csrf;
        document.documentElement.dataset.role = me.role || '';
        applyRole();
        return me;
      }).catch(function () { return null; });
    }
    return mePromise;
  }

  function applyRole() {
    var me = window.MSME_USER || {};
    document.querySelectorAll('[data-role="admin"]').forEach(function (el) {
      el.style.display = me.role === 'admin' ? '' : 'none';
    });
    var box = document.getElementById('msme-user-widget');
    if (box) drawWidget(box, me);
    window.dispatchEvent(new CustomEvent('msme:user', { detail: me }));
  }

  function drawWidget(box, me) {
    var admin = me.role === 'admin';
    box.innerHTML =
      '<div style="opacity:.75;margin-bottom:4px">Signed in as <b>' +
      escapeHtml(me.username || '') + '</b> (' + escapeHtml(me.role || '') + ')</div>' +
      '<a href="/account.html">Account</a>' +
      (admin ? ' · <a href="/users.html">Users</a>' : '') +
      ' · <a href="#" id="msme-logout">Logout</a>';
    var out = box.querySelector('#msme-logout');
    if (out) out.addEventListener('click', function (e) {
      e.preventDefault();
      window.fetch('/api/auth/logout', { method: 'POST' }).then(function () {
        location.href = '/login';
      });
    });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function installRoleStyle() {
    var style = document.createElement('style');
    style.textContent = 'html[data-role="editor"] [data-role="admin"]{display:none !important}';
    document.head.appendChild(style);
  }

  function mount() {
    installRoleStyle();
    var box = document.createElement('div');
    box.id = 'msme-user-widget';
    box.style.cssText = 'position:fixed;right:14px;bottom:14px;z-index:99999;' +
      'background:rgba(10,16,32,.94);color:#e5e9f5;border:1px solid #2a3550;' +
      'border-radius:10px;padding:8px 12px;font:12px/1.5 Inter,system-ui,sans-serif;' +
      'box-shadow:0 6px 20px rgba(0,0,0,.35)';
    box.addEventListener('mouseenter', function () { box.style.opacity = '1'; });
    document.body.appendChild(box);
    box.innerHTML = '…';
    box.style.display = 'none';
    currentUser().then(function (me) {
      if (!me) return;
      box.style.display = 'block';
      drawWidget(box, me);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
