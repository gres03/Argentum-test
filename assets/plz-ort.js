/* ─────────────────────────────────────────────────────────────
   ARGENTUM – PLZ ↔ Ort verknüpfen
   Füllt das Ort-Feld automatisch, sobald eine 4-stellige
   österreichische PLZ eingegeben wurde. Der Wert bleibt manuell
   überschreibbar; eine eigene Eingabe wird nicht überschrieben.

   Verknüpft:
     • <input data-plz-for="ID_DES_ORT_FELDS">
     • sonst automatisch je Formular die Felder name="plz" und name="ort"
   ───────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  var DATA = window.ARGENTUM_PLZ || {};

  function wire(plzEl, ortEl) {
    if (!plzEl || !ortEl) return;
    var autofilled = '';

    plzEl.addEventListener('input', function () {
      var digits = plzEl.value.replace(/\D/g, '').slice(0, 4);
      if (digits !== plzEl.value) plzEl.value = digits;

      var ort = DATA[digits];
      if (digits.length === 4 && ort) {
        if (ortEl.value.trim() === '' || ortEl.value === autofilled) {
          ortEl.value = ort;
          autofilled = ort;
          ortEl.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
    });
  }

  document.querySelectorAll('input[data-plz-for]').forEach(function (plzEl) {
    wire(plzEl, document.getElementById(plzEl.getAttribute('data-plz-for')));
  });

  document.querySelectorAll('form').forEach(function (form) {
    if (form.querySelector('input[data-plz-for]')) return;
    wire(form.querySelector('input[name="plz"]'), form.querySelector('input[name="ort"]'));
  });
})();
