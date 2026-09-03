/* ─────────────────────────────────────────────────────────────
   ARGENTUM – gemeinsames Skript für Navigation und Formulare
   (Kontakt, Versicherungs-Check, Schadenmeldung).
   ───────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  /* ===========================================================
     FORMULAR-VERSAND – ZENTRALE KONFIGURATION
     -----------------------------------------------------------
     Solange "endpoint" leer ist, läuft alles im DEMO-MODUS:
     Es wird NICHTS verschickt, es erscheint nur die Bestätigung
     (die Daten werden zur Kontrolle in die Browser-Konsole
     geschrieben).

     Zum Aktivieren des echten Versands genau EINEN Weg wählen:

     A) Web3Forms (kein eigener Server nötig)
        endpoint  : 'https://api.web3forms.com/submit'
        accessKey : '<dein Access Key von web3forms.com>'
        Ziel-Postfach wird bei Web3Forms im Account hinterlegt.

     B) Eigene Serverfunktion (z. B. Vercel /api/submit)
        endpoint  : '/api/submit'
        accessKey : ''  (nicht nötig)
        Die Funktion kümmert sich um Mailversand + Kundenbestätigung.

     "targetEmail" ist nur zur Doku/als Reply-To gedacht.
     =========================================================== */
  var FORM_CONFIG = {
    endpoint: '',
    accessKey: '',
    targetEmail: 'office@argentum.co.at',
    // Kundenbestätigung: greift nur bei einer eigenen Serverfunktion,
    // die das umsetzt (Web3Forms Free kann das nicht).
    sendCustomerConfirmation: true
  };

  // ── HAMBURGER-MENÜ ────────────────────────────────────────
  var hamburger = document.getElementById('hamburger');
  var mobileMenu = document.getElementById('mobile-menu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', function () {
      var isOpen = mobileMenu.classList.toggle('open');
      hamburger.classList.toggle('open', isOpen);
      hamburger.setAttribute('aria-label', isOpen ? 'Menü schließen' : 'Menü öffnen');
    });

    document.addEventListener('click', function (e) {
      if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
        window.closeMobileMenu();
      }
    });
  }

  window.closeMobileMenu = function () {
    if (!mobileMenu || !hamburger) return;
    mobileMenu.classList.remove('open');
    hamburger.classList.remove('open');
    hamburger.setAttribute('aria-label', 'Menü öffnen');
  };

  // ── BEDINGTE FELDER ───────────────────────────────────────
  // Element mit .ff-conditional, data-when="feldname",
  // data-equals="Wert" (mehrere Werte mit "|" trennen).
  function fieldValue(name) {
    var nodes = document.querySelectorAll('[name="' + name + '"]');
    if (!nodes.length) return null;
    if (nodes[0].type === 'radio') {
      for (var i = 0; i < nodes.length; i++) if (nodes[i].checked) return nodes[i].value;
      return '';
    }
    return nodes[0].value;
  }

  document.querySelectorAll('.ff-conditional').forEach(function (el) {
    var whenName = el.getAttribute('data-when');
    var equals = (el.getAttribute('data-equals') || '').split('|');
    if (!whenName) return;
    var sources = document.querySelectorAll('[name="' + whenName + '"]');
    if (!sources.length) return;

    function sync() {
      var match = equals.indexOf(fieldValue(whenName)) !== -1;
      el.classList.toggle('is-visible', match);
      el.querySelectorAll('[data-required-when-visible]').forEach(function (f) {
        if (match) { f.setAttribute('required', ''); }
        else { f.removeAttribute('required'); }
      });
    }
    sources.forEach(function (s) {
      s.addEventListener('change', sync);
      s.addEventListener('input', sync);
    });
    sync();
  });

  // ── FORMULAR ──────────────────────────────────────────────
  // Greift für jedes <form> mit der Klasse .js-form
  // (Kontaktformular, Anfrageformulare, Schadenmeldung).
  document.querySelectorAll('form.js-form').forEach(initForm);

  function initForm(form) {
    var success = form.parentElement.querySelector('.js-form-success')
      || document.getElementById(form.getAttribute('data-success'));

    function clearInvalid(el) {
      el.classList.remove('ff-invalid');
      var box = el.closest('.ff-radio-group') || el.closest('.ff-field') || el.closest('.form-group');
      if (box) box.classList.remove('ff-invalid');
    }

    form.querySelectorAll('input, select, textarea').forEach(function (el) {
      el.addEventListener('input', function () { clearInvalid(el); });
      el.addEventListener('change', function () { clearInvalid(el); });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // Honeypot: stiller Abbruch bei Bot-Verdacht
      var hp = form.querySelector('[name="_hp"]');
      if (hp && hp.value) return;

      var firstInvalid = null;
      var seenRadio = {};
      form.querySelectorAll('[required]').forEach(function (el) {
        if (el.closest('.ff-conditional:not(.is-visible)')) return;

        var ok;
        if (el.type === 'radio') {
          if (seenRadio[el.name]) return;
          seenRadio[el.name] = true;
          var group = form.querySelectorAll('input[name="' + el.name + '"]');
          ok = Array.prototype.some.call(group, function (r) { return r.checked; });
          var rbox = el.closest('.ff-radio-group') || el.closest('.ff-field') || el;
          rbox.classList.toggle('ff-invalid', !ok);
          if (!ok && !firstInvalid) firstInvalid = group[0];
          return;
        }

        ok = el.type === 'checkbox' ? el.checked : String(el.value).trim() !== '';
        el.classList.toggle('ff-invalid', !ok);
        var box = el.closest('.ff-field') || el.closest('.form-group');
        if (box) box.classList.toggle('ff-invalid', !ok);
        if (!ok && !firstInvalid) firstInvalid = el;
      });

      if (firstInvalid) {
        firstInvalid.focus({ preventScroll: true });
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }

      submit(form, success);
    });
  }

  function readableSubject(form, data) {
    if (data._betreff) return data._betreff;
    return 'Website-Formular: ' + (data._typ || form.id || 'Anfrage');
  }

  function submit(form, success) {
    var data = {};
    new FormData(form).forEach(function (v, k) {
      if (!(v instanceof File)) data[k] = v;
    });

    function showSuccess() {
      form.style.display = 'none';
      if (success) {
        success.classList.add('is-visible');
        success.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    // ── DEMO-MODUS ──────────────────────────────────────────
    if (!FORM_CONFIG.endpoint) {
      console.log('[ARGENTUM – Demo-Modus] Es wurde nichts verschickt. Daten:', data);
      showSuccess();
      return;
    }

    // ── ECHTER VERSAND ──────────────────────────────────────
    var payload = Object.assign({}, data);
    payload.subject = readableSubject(form, data);
    if (data.email) payload.replyto = data.email;
    if (data.name || (data.vorname && data.nachname)) {
      payload.from_name = data.name || (data.vorname + ' ' + data.nachname);
    }
    if (FORM_CONFIG.accessKey) payload.access_key = FORM_CONFIG.accessKey;
    if (FORM_CONFIG.sendCustomerConfirmation) payload.send_confirmation = '1';

    var btn = form.querySelector('button[type="submit"]');
    var btnLabel = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = 'Wird gesendet …'; }

    fetch(FORM_CONFIG.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        showSuccess();
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = btnLabel; }
        alert('Die Übermittlung hat nicht funktioniert. Bitte versuchen Sie es später erneut oder rufen Sie uns unter +43 7242 219990 an.');
      });
  }
})();
