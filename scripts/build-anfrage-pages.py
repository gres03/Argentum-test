#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generiert die Anfrage-Seiten für den ARGENTUM Versicherungs-Check.

Alle Seiten teilen sich  assets/styles.css , assets/form.css  und
assets/anfrage.js . Struktur (Navigation / Breadcrumb / Formular / Footer)
kommt komplett aus diesem Skript – so bleiben die ~10 Seiten konsistent.

Aufruf:   python3 scripts/build-anfrage-pages.py
"""

import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INTRO = ("Bitte nennen Sie uns Ihre wichtigsten Eckdaten, damit wir das für "
         "Sie beste Absicherungs-Konzept erarbeiten können.")

JA_NEIN = ["Ja", "Nein"]
GESCHLECHT = ["Männlich", "Weiblich", "Divers"]
ZAHLWEISE = ["Monatlich", "Vierteljährlich", "Halbjährlich", "Jährlich"]

# Feld-Kurzschreibweise:
#   (name, label, type, required, placeholder, options, conditional)
def f(name, label, typ="text", req=False, ph="", options=None, cond=None, hint=""):
    return dict(name=name, label=label, type=typ, required=req, placeholder=ph,
                options=options or [], cond=cond, hint=hint)

PERSON_BASE = [
    f("titel", "Titel", ph="Dr."),
    f("vorname", "Vorname", req=True),
    f("nachname", "Nachname", req=True),
    f("strasse", "Straße und Hausnummer", req=True, ph="Musterstraße 1"),
    f("plz-ort", "Postleitzahl und Ort", req=True, ph="1010 Wien"),
    f("email", "E-Mail", "email", req=True, ph="name@beispiel.at"),
    f("telefon", "Telefon", "tel", req=True, ph="+43 ..."),
    f("geburtsdatum", "Geburtsdatum", "date", req=True),
]

def person(*extra):
    return dict(legend="Persönliche Daten", fields=PERSON_BASE + list(extra))

BANK = [
    f("iban", "IBAN", ph="AT00 0000 0000 0000 0000"),
    f("bic", "BIC – nur bei ausländischem IBAN erforderlich"),
]

CATEGORIES = [
    {
        "slug": "krankenversicherung",
        "title": "Krankenversicherung",
        "sections": [
            person(),
            dict(legend="Beruf & Krankenkasse", fields=[
                f("beruf", "Beruf", req=True),
                f("arbeitgeber", "Arbeitgeber", hint="optional"),
                f("krankenkasse", "Gesetzliche Krankenkasse", "select", req=True,
                  options=["ÖGK", "SVA", "SVS", "BVA", "BVAEB", "KFL", "KFG", "LKUF", "Sonstige"]),
                f("krankenkasse-sonstige", "Wenn „Sonstige“: bitte angeben",
                  cond=("krankenkasse", "Sonstige")),
            ]),
        ],
    },
    {
        "slug": "unfallversicherung",
        "title": "Unfallversicherung",
        "sections": [
            person(f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT)),
            dict(legend="Berufliche Angaben", fields=[
                f("hauptberuf", "Hauptberuf", req=True),
                f("nebenberuf", "Nebenberuf – falls vorhanden"),
            ]),
            dict(legend="Versicherung & Zahlung", fields=[
                f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
                f("vorversicherung", "Bereits eine Vorversicherung vorhanden?", "select", options=JA_NEIN),
            ] + BANK),
            dict(legend="Weitere zu versichernde Personen", fields=[
                f("weitere-personen", "Sollen weitere Personen mitversichert werden?", "select", req=True, options=JA_NEIN),
            ]),
        ],
    },
    {
        "slug": "altersvorsorge",
        "title": "Altersvorsorge",
        "sections": [
            person(
                f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT),
                f("land", "Land", req=True),
                f("nationalitaet", "Nationalität", req=True),
            ),
            dict(legend="Steuer & Sparbetrag", fields=[
                f("us-person", "US-Person?", "select", req=True, options=JA_NEIN),
                f("steuerliche-ansaessigkeit", "Steuerliche Ansässigkeit", req=True),
                f("sparbetrag", "Gewünschter monatlicher Sparbetrag (€)", "number", req=True),
            ]),
            dict(legend="Bankverbindung", fields=list(BANK)),
        ],
    },
    {
        "slug": "risikolebensversicherung",
        "title": "Risikolebensversicherung",
        "consent_extra": " – einschließlich der Gesundheitsdaten –",
        "sections": [
            person(
                f("geburtsort", "Geburtsort", req=True),
                f("staatsangehoerigkeit", "Staatsangehörigkeit", req=True),
            ),
            dict(legend="Beruf", fields=[
                f("beruf", "Beruf", req=True),
                f("berufsstatus", "Berufsstatus", "select", req=True,
                  options=["Angestellt", "Selbstständig", "Beamter/Beamtin", "Arbeiter/in", "Sonstige"]),
            ]),
            dict(legend="Gesundheit & Risiko", fields=[
                f("koerpergroesse", "Körpergröße (cm)", "number", req=True),
                f("koerpergewicht", "Körpergewicht (kg)", "number", req=True),
                f("raucherstatus", "Raucherstatus", "select", req=True, options=[
                    "Nichtraucher/in – nie geraucht",
                    "Nichtraucher/in – seit mind. 10 Jahren",
                    "Nichtraucher/in – seit weniger als 10 Jahren",
                    "Raucher/in bzw. in den letzten 12 Monaten geraucht",
                ]),
                f("zweirad", "Fahren Sie ein motorisiertes Zweirad, Trike oder Quad?", "select", req=True, options=JA_NEIN),
            ]),
            dict(legend="Zahlung", fields=[
                f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
            ]),
        ],
    },
    {
        "slug": "haushaltsversicherung",
        "title": "Haushaltsversicherung",
        "sections": [
            person(f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT)),
            dict(legend="Wertgegenstände", fields=[
                f("sportausruestung", "Sind Fahrräder, Jagd-, Sport- oder Tauchausrüstung vorhanden?", "select", req=True, options=JA_NEIN),
            ]),
            dict(legend="Zahlung & Bankverbindung", fields=[
                f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
            ] + BANK),
        ],
    },
    {
        "slug": "eigenheim-haushaltsversicherung",
        "title": "Eigenheim- & Haushaltsversicherung",
        "sections": [
            person(f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT)),
            dict(legend="Objekt & Anlagen", fields=[
                f("nebengebaeude", "Nebengebäude vorhanden?", "select", req=True, options=JA_NEIN),
                f("pv-anlage", "PV-/Solaranlage oder Glashaus vorhanden?", "select", req=True, options=JA_NEIN),
                f("pool", "Pool vorhanden?", "select", req=True, options=JA_NEIN),
            ]),
            dict(legend="Lage & Gewässer", fields=[
                f("bach", "Fließt ein Bach in der Nähe des Hauses?", "select", options=JA_NEIN),
            ]),
            dict(legend="Wertgegenstände", fields=[
                f("sportausruestung", "Sind Fahrräder, Jagd-, Sport- oder Tauchausrüstung vorhanden?", "select", req=True, options=JA_NEIN),
            ]),
            dict(legend="Zahlung & Bankverbindung", fields=[
                f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
            ] + BANK),
        ],
    },
    {
        "slug": "kfz-haftpflicht",
        "title": "KFZ-Haftpflicht",
        "sections": None,   # unten gesetzt
    },
    {
        "slug": "kfz-haftpflicht-mit-kasko",
        "title": "KFZ-Haftpflicht mit Kasko",
        "sections": None,
    },
    {
        "slug": "mopedversicherung",
        "title": "Mopedversicherung",
        "sections": [
            person(f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT)),
            dict(legend="Fahrzeugdaten", fields=[
                f("fahrzeugart", "Fahrzeugart", "select", req=True, options=["Moped", "Motorrad", "Kleinmotorrad"]),
                f("fahrzeugmarke", "Fahrzeugmarke", req=True),
                f("erstzulassung", "Erstzulassung", "date", req=True),
                f("sitzplaetze", "Anzahl Plätze", "number", req=True),
                f("co2", "CO₂-Wert (g/km)", req=True),
                f("kw", "Leistung (kW)", req=True),
                f("antriebsart", "Antriebsart", req=True),
                f("hubraum", "Hubraum (ccm)", "number", req=True),
                f("eigengewicht", "Eigengewicht (kg)", "number", req=True),
                f("kennzeichen", "Kennzeichen – falls vorhanden"),
                f("fahrgestellnummer", "Fahrgestellnummer", req=True),
            ]),
            dict(legend="Zahlung & Bankverbindung", fields=[
                f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
            ] + BANK),
        ],
    },
    {
        "slug": "anhaengerversicherung",
        "title": "Anhängerversicherung",
        "sections": [
            person(f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT)),
            dict(legend="Anhängerdaten", fields=[
                f("verwendung", "Verwendungsbestimmung des Anhängers", req=True),
                f("fahrzeugmarke", "Fahrzeugmarke", req=True),
                f("erstzulassung", "Erstzulassung", "date", req=True),
                f("kennzeichen", "Kennzeichen – falls vorhanden"),
                f("fahrgestellnummer", "Fahrgestellnummer", req=True),
            ]),
            dict(legend="Zahlung & Bankverbindung", fields=[
                f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
            ] + BANK),
        ],
    },
]

# ── KFZ-Formulare (Haftpflicht bzw. Haftpflicht + Kasko) ──────────────
def kfz_sections(with_kasko):
    fahrzeug = [
        f("kennzeichen", "Kennzeichen – falls vorhanden"),
        f("kfz-typ", "KFZ-Typ", req=True),
        f("kfz-marke", "KFZ-Marke", req=True),
        f("fin", "Fahrzeug-Identifikationsnummer (FIN)", req=True),
        f("erstzulassung", "Datum der Erstzulassung", "date", req=True),
        f("antriebsart", "Antriebsart", req=True),
        f("leistung", "Leistung (kW bzw. PS)", req=True),
        f("hubraum", "Hubraum (ccm)", "number", req=True),
        f("co2", "CO₂-Ausstoß (g/km) nach WLTP", req=True),
        f("eigengewicht", "Fahrzeug-Eigengewicht (kg)", "number", req=True),
        f("gesamtgewicht", "Gesamtgewicht (kg)", "number", req=True),
        f("sitzplaetze", "Sitzplätze", "number", req=True),
        f("katalysator", "Katalysator", "select", req=True, options=JA_NEIN),
        f("leasing", "Leasing", "select", req=True, options=JA_NEIN),
    ]
    if with_kasko:
        fahrzeug += [
            f("listenneupreis", "Listen-Neupreis", req=True),
            f("sonderausstattung-wert", "Wert der Sonderausstattung – falls vorhanden"),
        ]
    return [
        person(
            f("geschlecht", "Geschlecht", "select", req=True, options=GESCHLECHT),
            f("nationalitaet", "Nationalität", req=True),
            f("zulassungsbezirk", "Zulassungsbezirk", req=True),
        ),
        dict(legend="Fahrzeugdaten", fields=fahrzeug),
        dict(legend="Zulassung & Optionen", fields=[
            f("l17", "L-17-Führerschein?", "select", options=JA_NEIN),
            f("variante", "Variante A oder B?", "select", options=["A", "B"]),
            f("zweitfahrzeug", "Zweitfahrzeug?", "select", options=JA_NEIN),
            f("wechselkennzeichen", "Wechselkennzeichen?", "select", req=True, options=JA_NEIN),
        ]),
        dict(legend="Vorversicherung & Steuer", fields=[
            f("vorversicherung", "Besteht eine Vorversicherung?", "select", req=True, options=JA_NEIN),
            f("einschraenkung", "Besteht bei Ihnen eine Einschränkung (bzgl. Befreiung der "
              "motorbezogenen Versicherungssteuer)?", "select", req=True, options=JA_NEIN),
        ]),
        dict(legend="Zahlung & Bankverbindung", fields=[
            f("zahlweise", "Zahlungsweise", "select", req=True, options=ZAHLWEISE),
        ] + BANK),
    ]

for c in CATEGORIES:
    if c["slug"] == "kfz-haftpflicht":
        c["sections"] = kfz_sections(False)
    elif c["slug"] == "kfz-haftpflicht-mit-kasko":
        c["sections"] = kfz_sections(True)

# ─────────────────────────────────────────────────────────────────────
NAV = """  <nav id="top">
    <a href="index.html#top" class="nav-logo">
      <svg class="logo-tree" viewBox="0 0 54 54" fill="none" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="27" cy="14" rx="11" ry="9" fill="#6a9b3a"/>
        <ellipse cx="20" cy="20" rx="9" ry="8" fill="#5a8a2d"/>
        <ellipse cx="34" cy="20" rx="9" ry="8" fill="#5a8a2d"/>
        <ellipse cx="27" cy="24" rx="12" ry="9" fill="#6a9b3a"/>
        <ellipse cx="19" cy="28" rx="8" ry="7" fill="#4d7a25"/>
        <ellipse cx="35" cy="28" rx="8" ry="7" fill="#4d7a25"/>
        <ellipse cx="27" cy="30" rx="10" ry="8" fill="#6a9b3a"/>
        <rect x="24" y="36" width="6" height="12" rx="2" fill="#4d7a25"/>
        <ellipse cx="27" cy="48" rx="7" ry="2" fill="#4d7a25" opacity="0.4"/>
      </svg>
      <div class="logo-wordmark">
        <span class="logo-name">ARGENTUM</span>
        <span class="logo-tagline">Absichern&reg; &middot; Finanzieren &middot; Veranlagen</span>
      </div>
    </a>

    <ul class="nav-links">
      <li><a href="index.html#top">Home</a></li>
      <li><a href="index.html#ueber-uns">&Uuml;ber uns</a></li>
      <li><a href="index.html#leistungen">Finanzberatung</a></li>
      <li class="has-sub">
        <a href="index.html#versicherungscheck">Versicherungs-Check</a>
        <ul class="nav-sub">
          <li><a href="index.html#versicherungscheck">Alle Versicherungs-Checks</a></li>
          <li><a href="schadenmeldung.html">Schaden melden</a></li>
        </ul>
      </li>
      <li><a href="index.html#kooperationen">Kooperationen</a></li>
      <li><a href="index.html#kontakt">Kontakt</a></li>
    </ul>

    <a href="index.html#kontakt" class="btn-primary nav-btn">Beratungsgespr&auml;ch</a>
    <button class="hamburger" id="hamburger" aria-label="Men&uuml; &ouml;ffnen">
      <span></span><span></span><span></span>
    </button>
  </nav>
  <div class="mobile-menu" id="mobile-menu">
    <a href="index.html#top" onclick="closeMobileMenu()">Home</a>
    <a href="index.html#ueber-uns" onclick="closeMobileMenu()">&Uuml;ber uns</a>
    <a href="index.html#leistungen" onclick="closeMobileMenu()">Finanzberatung</a>
    <a href="index.html#versicherungscheck" onclick="closeMobileMenu()">Versicherungs-Check</a>
    <a href="schadenmeldung.html" class="mobile-sub" onclick="closeMobileMenu()">&#8627; Schaden melden</a>
    <a href="index.html#kooperationen" onclick="closeMobileMenu()">Kooperationen</a>
    <a href="index.html#kontakt" onclick="closeMobileMenu()">Kontakt</a>
    <a href="index.html#kontakt" class="mobile-cta" onclick="closeMobileMenu()">Kostenloses Erstgespr&auml;ch</a>
  </div>
"""

FOOTER = """  <footer>
    <div class="footer-top">
      <div class="footer-brand">
        <div class="footer-logo-wrap" style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
          <svg width="40" height="40" viewBox="0 0 54 54" fill="none">
            <ellipse cx="27" cy="14" rx="11" ry="9" fill="#8ab954"/>
            <ellipse cx="20" cy="20" rx="9" ry="8" fill="#6a9b3a"/>
            <ellipse cx="34" cy="20" rx="9" ry="8" fill="#6a9b3a"/>
            <ellipse cx="27" cy="24" rx="12" ry="9" fill="#8ab954"/>
            <ellipse cx="19" cy="28" rx="8" ry="7" fill="#5a8a2d"/>
            <ellipse cx="35" cy="28" rx="8" ry="7" fill="#5a8a2d"/>
            <ellipse cx="27" cy="30" rx="10" ry="8" fill="#8ab954"/>
            <rect x="24" y="36" width="6" height="12" rx="2" fill="#5a8a2d"/>
          </svg>
          <div>
            <div class="footer-logo-name">ARGENTUM</div>
            <div class="footer-logo-tag">Absichern &middot; Finanzieren &middot; Veranlagen</div>
          </div>
        </div>
        <p>ARGENTUM GmbH &ndash; Ihr unabh&auml;ngiger Finanz- und Versicherungsberater in Wels, &Ouml;sterreich.</p>
        <a href="index.html#kontakt" class="btn-primary" style="font-size:13px;padding:9px 18px;">Jetzt Kontakt aufnehmen</a>
      </div>
      <div class="footer-col">
        <h4>Leistungen</h4>
        <ul>
          <li><a href="index.html#leistungen">Versicherungsberatung</a></li>
          <li><a href="index.html#leistungen">Finanzierungsberatung</a></li>
          <li><a href="index.html#leistungen">Verm&ouml;gensaufbau</a></li>
          <li><a href="index.html#leistungen">Altersvorsorge</a></li>
          <li><a href="index.html#leistungen">Gesundheitsvorsorge</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Service</h4>
        <ul>
          <li><a href="index.html#versicherungscheck">Versicherungs-Check</a></li>
          <li><a href="schadenmeldung.html">Schaden melden</a></li>
          <li><a href="index.html#ueber-uns">&Uuml;ber uns</a></li>
          <li><a href="index.html#team">Team</a></li>
          <li><a href="index.html#kooperationen">Kooperationen</a></li>
          <li><a href="index.html#kontakt">Kontakt</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Kontakt</h4>
        <ul>
          <li><a href="tel:+437242219990">+43 7242 219990</a></li>
          <li><a href="mailto:office@argentum.co.at">office@argentum.co.at</a></li>
          <li><a style="pointer-events:none;cursor:default">Maria-Theresia-Str. 41</a></li>
          <li><a style="pointer-events:none;cursor:default">4600 Wels, &Ouml;sterreich</a></li>
        </ul>
      </div>
    </div>

    <div class="impressum-section" id="impressum">
      <div class="impressum-title">Impressum &amp; Pflichtangaben</div>
      <p class="impressum-text">
        <strong style="color:rgba(255,255,255,0.5)">ARGENTUM GmbH</strong> &middot; Maria-Theresia-Str. 41 &middot; 4600 Wels &middot; &Ouml;sterreich &middot;
        Tel.: +43 7242 219990 &middot; E-Mail: office@argentum.co.at &middot; Web: www.argentum.co.at &middot;
        Firmenbuchnummer: FN 440241p &middot; Firmenbuchgericht: Landesgericht Wels &middot;
        Gesch&auml;ftsf&uuml;hrer: Franz Lebelhuber, Klaus Weidinger &middot;
        Branche: Finanz- und Verm&ouml;gensberatung, Versicherungsmakler &middot;
        GISA-Zahlen: 28144618 (Versicherungsvermittlung) und 28132387 (Gewerbliche Verm&ouml;gensberatung) &middot;
        Konzessionierter WAG-2018-Partner: FinanzAdmin Wertpapierdienstleistungen GmbH &middot;
        Zust&auml;ndige Beh&ouml;rde: Bezirkshauptmannschaft Wels-Land &middot; Aufsichtsbeh&ouml;rde: FMA (Finanzmarktaufsicht) &middot;
        Mitglied der Wirtschaftskammer &Ouml;sterreich (WKO)
      </p>
    </div>

    <div class="footer-bottom">
      <p>&copy; 2026 ARGENTUM GmbH. Alle Rechte vorbehalten.</p>
      <div class="footer-bottom-links">
        <a href="impressum.html">Impressum</a>
        <a href="datenschutz.html">Datenschutz</a>
        <a href="esg.html">ESG-Erkl&auml;rung</a>
      </div>
    </div>
  </footer>
"""

ASIDE = """      <aside class="anfrage-aside">
        <div class="aside-card aside-card--accent">
          <h4>Ihre Vorteile mit ARGENTUM</h4>
          <ul class="aside-list">
            <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> 100 % unabh&auml;ngige Beratung</li>
            <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Vergleich von &uuml;ber 50 Gesellschaften</li>
            <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Kostenlos &amp; unverbindlich</li>
            <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Pers&ouml;nliche Betreuung in Wels</li>
          </ul>
        </div>
        <div class="aside-card aside-contact">
          <h4>Lieber pers&ouml;nlich?</h4>
          <p>
            Rufen Sie uns an oder schreiben Sie uns:<br>
            <a href="tel:+437242219990">+43 7242 219990</a><br>
            <a href="mailto:office@argentum.co.at">office@argentum.co.at</a>
          </p>
        </div>
      </aside>
"""

def esc(s):
    return html.escape(s, quote=True)

def render_field(fld):
    fid = fld["name"]
    req = fld["required"]
    lab = esc(fld["label"])
    star = ' <span class="ff-req">*</span>' if req else ""
    hint = f' <span class="ff-hint">{esc(fld["hint"])}</span>' if fld["hint"] else ""
    reqattr = " required" if req else ""
    wrap_cls = "ff-field"
    wrap_attr = ""
    if fld["cond"]:
        wrap_cls += " ff-col-full ff-conditional"
        wrap_attr = f' data-when="{esc(fld["cond"][0])}" data-equals="{esc(fld["cond"][1])}"'

    if fld["type"] == "select":
        opts = ['<option value="">&ndash; Bitte ausw&auml;hlen &ndash;</option>']
        for o in fld["options"]:
            opts.append(f'<option value="{esc(o)}">{esc(o)}</option>')
        control = ('<select id="{0}" name="{0}"{1}>\n'.format(fid, reqattr)
                   + "".join(f'                {o}\n' for o in opts)
                   + '              </select>')
    else:
        ph = f' placeholder="{esc(fld["placeholder"])}"' if fld["placeholder"] else ""
        maxlen = ' maxlength="254"' if fld["type"] == "email" else (' maxlength="200"' if fld["type"] == "text" else "")
        control = f'<input type="{fld["type"]}" id="{fid}" name="{fid}"{reqattr}{ph}{maxlen}>'

    return (f'              <div class="{wrap_cls}"{wrap_attr}>\n'
            f'                <label for="{fid}">{lab}{star}{hint}</label>\n'
            f'                {control}\n'
            f'              </div>')

def render_section(sec):
    fields = "\n".join(render_field(x) for x in sec["fields"])
    return ('          <fieldset class="ff-section">\n'
            f'            <legend>{esc(sec["legend"])}</legend>\n'
            '            <div class="ff-grid">\n'
            f'{fields}\n'
            '            </div>\n'
            '          </fieldset>')

PAGE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} &ndash; Anfrage | ARGENTUM GmbH</title>
  <meta name="description" content="{title} &ndash; Versicherungs-Check von ARGENTUM GmbH. Unverbindlich und kostenlos anfragen.">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="assets/styles.css">
  <link rel="stylesheet" href="assets/form.css">
</head>
<body>

  <!-- ── NAVBAR ─────────────────────────────────────────── -->
{nav}
  <!-- ── ANFRAGE ───────────────────────────────────────── -->
  <div class="anfrage-wrap">
    <div class="anfrage-grid">

      <div class="anfrage-main">
        <p class="section-label">Versicherungs-Check</p>
        <h1 class="anfrage-title">{title}</h1>
        <p class="anfrage-intro">{intro}</p>
        <p class="ff-required-note">Mit <span class="ff-req">*</span> markierte Felder sind Pflichtfelder.</p>

        <!--
          FORMULAR-VERSAND: zentral in assets/anfrage.js (FORM_CONFIG).
          Solange dort kein "endpoint" gesetzt ist, laeuft alles im
          Demo-Modus (es wird nichts verschickt, nur die Bestaetigung
          erscheint).
        -->
        <form id="anfrage-form" class="ff-form js-form" novalidate>
          <input type="hidden" name="_betreff" value="Versicherungs-Check: {title}">
          <input type="hidden" name="_sparte" value="{slug}">
          <div style="position:absolute;left:-9999px" aria-hidden="true">
            <label>Bitte leer lassen <input type="text" name="_hp" tabindex="-1" autocomplete="off"></label>
          </div>

{sections}

          <fieldset class="ff-section">
            <legend>Einwilligung &amp; Absenden</legend>
            <div class="ff-field ff-col-full">
              <label class="ff-consent">
                <input type="checkbox" id="datenschutz" name="datenschutz" value="1" required>
                <span>Ich habe die <a href="datenschutz.html" target="_blank" rel="noopener">Datenschutzerkl&auml;rung</a> gelesen und willige in die Verarbeitung meiner Daten{consent_extra} zur Bearbeitung dieser Anfrage ein. <span class="ff-req">*</span></span>
              </label>
            </div>
            <div class="ff-field ff-col-full">
              <button type="submit" class="btn-primary ff-submit">Anfrage absenden</button>
              <p class="ff-note">Ihre Anfrage ist unverbindlich und kostenlos. ARGENTUM ber&auml;t Sie unabh&auml;ngig und vergleicht die Angebote f&uuml;hrender Versicherungsgesellschaften.</p>
            </div>
          </fieldset>
        </form>

        <div class="ff-success js-form-success" id="anfrage-success">
          <h3>Vielen Dank f&uuml;r Ihre Anfrage!</h3>
          <p>Wir haben Ihre Daten erhalten und melden uns in der Regel innerhalb von ein bis zwei Werktagen bei Ihnen. Bei dringenden Fragen erreichen Sie uns unter <a href="tel:+437242219990">+43 7242 219990</a>.</p>
        </div>
      </div>

{aside}
    </div>
  </div>

  <!-- ── FOOTER ─────────────────────────────────────────── -->
{footer}
  <script src="assets/anfrage.js"></script>
</body>
</html>
"""

def build():
    written = []
    for c in CATEGORIES:
        sections_html = "\n\n".join(render_section(s) for s in c["sections"])
        page = PAGE.format(
            title=esc(c["title"]),
            slug=c["slug"],
            intro=esc(INTRO),
            nav=NAV,
            footer=FOOTER,
            aside=ASIDE,
            sections=sections_html,
            consent_extra=c.get("consent_extra", ""),
        )
        path = os.path.join(ROOT, c["slug"] + ".html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
        written.append(c["slug"] + ".html")
    print("geschrieben:")
    for w in written:
        print("  " + w)

if __name__ == "__main__":
    build()
