#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auswertung der Messreihe aus hydroponik_log.csv
===============================================

Erzeugt druckfertige Diagramme fuer die Arbeit:

  1  pH-Verlauf und Wassertemperatur ueber der Zeit
     Zwei Diagramme untereinander mit gemeinsamer Zeitachse - bewusst
     KEINE zweite y-Achse: die Zuordnung zweier Skalen in einem Bild ist
     willkuerlich und suggeriert Zusammenhaenge, die nicht in den Daten
     stehen.

  2  Sensorspannung ueber pH-Wert
     Muss eine Gerade ergeben. Die Ausgleichsgerade liefert die Steilheit
     in mV/pH; sie gehoert zwischen 50 und 59 mV/pH (Nernst). Das ist der
     Nachweis, dass die Zweipunktkalibrierung traegt.

  3  Titrationskurve (optional, aus eigener Datei)
     Dosis-Wirkungs-Beziehung der pH-Minus-Loesung samt Empfindlichkeit.

Aufruf
------
    python tools/plot_messreihe.py hydroponik_log.csv
    python tools/plot_messreihe.py hydroponik_log.csv --titration titration.csv
    python tools/plot_messreihe.py hydroponik_log.csv --von "2026-08-05 14:00:00"

Die Titrationsdatei schreibst du von Hand mit zwei Spalten:

    volumen_ml_pro_l,ph
    0.0,6.85
    0.5,6.51
    1.0,6.22
"""

import argparse
import csv
import sys
from datetime import datetime

try:
    import matplotlib
    matplotlib.use("Agg")            # kein Fenster noetig, schreibt nur Dateien
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    from matplotlib.dates import DateFormatter
    import numpy as np
except ImportError:
    print("Fehlende Pakete. Installieren mit:\n"
          "    pip install -r tools/requirements.txt")
    sys.exit(1)


# ==================================================================
#   Darstellung
# ==================================================================
# Eine Messgroesse je Diagramm, daher keine Legende - die Achsenbe-
# schriftung benennt sie bereits. Duenne Linien, zurueckhaltendes Raster.

SERIE      = "#2a78d6"      # Datenlinie
ZIELBAND   = "#0ca30c"      # Zielbereich, stark aufgehellt
RASTER     = "#e1e0d9"
ACHSE      = "#c3c2b7"
TEXT       = "#0b0b0b"
TEXT_LEISE = "#52514e"

plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.size":        9,
    "axes.edgecolor":   ACHSE,
    "axes.labelcolor":  TEXT,
    "axes.linewidth":   0.8,
    "axes.grid":        True,
    "grid.color":       RASTER,
    "grid.linewidth":   0.8,
    "grid.linestyle":   "-",         # durchgezogen, nie gestrichelt
    "xtick.color":      TEXT_LEISE,
    "ytick.color":      TEXT_LEISE,
    "figure.dpi":       300,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
})


def aufraeumen(ax):
    """Nimmt den Rahmen oben und rechts weg - weniger Linien, die keine Daten sind."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_axisbelow(True)


# ==================================================================
#   Einlesen
# ==================================================================

def zahl(wert):
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


def lies_log(pfad, von=None, bis=None):
    """Liest hydroponik_log.csv. Ungueltige Messungen werden verworfen."""
    zeit, ph, spannung, wasser_temp = [], [], [], []

    with open(pfad, "r", encoding="utf-8", newline="") as datei:
        for zeile in csv.DictReader(datei):
            stempel = zeile.get("timestamp")
            if not stempel:
                continue
            try:
                zeitpunkt = datetime.strptime(stempel, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            if von and zeitpunkt < von:
                continue
            if bis and zeitpunkt > bis:
                continue

            zeit.append(zeitpunkt)
            ph.append(zahl(zeile.get("ph")))
            spannung.append(zahl(zeile.get("ph_spannung")))
            wasser_temp.append(zahl(zeile.get("wasser_temp")))

    if not zeit:
        print("Keine verwertbaren Zeilen gefunden. Stimmt der Zeitraum?")
        sys.exit(1)

    return zeit, ph, spannung, wasser_temp


def lies_titration(pfad):
    volumen, ph = [], []
    with open(pfad, "r", encoding="utf-8", newline="") as datei:
        for zeile in csv.DictReader(datei):
            v = zahl(zeile.get("volumen_ml_pro_l"))
            p = zahl(zeile.get("ph"))
            if v is not None and p is not None:
                volumen.append(v)
                ph.append(p)
    if not volumen:
        print(f"{pfad}: keine verwertbaren Zeilen.")
        sys.exit(1)
    return volumen, ph


def nur_gueltige(x, y):
    """Paare, bei denen beide Werte vorliegen."""
    paare = [(a, b) for a, b in zip(x, y) if b is not None]
    if not paare:
        return [], []
    return [a for a, _ in paare], [b for _, b in paare]


def mit_luecken(zeit, werte, faktor=3.0):
    """Bricht die Linie auf, wo Messungen fehlen.

    Ohne diesen Schritt wuerde matplotlib ueber einen Sensorausfall
    hinweg eine durchgehende Linie ziehen - das saehe aus wie gemessene
    Daten. Ein Abstand deutlich ueber dem ueblichen Messintervall
    (Median * faktor) gilt als Luecke und bekommt einen NaN-Punkt.
    """
    if len(zeit) < 3:
        return zeit, werte

    abstaende = sorted((b - a).total_seconds() for a, b in zip(zeit, zeit[1:]))
    median = abstaende[len(abstaende) // 2]
    grenze = max(median * faktor, median + 1.0)

    z2, w2 = [zeit[0]], [werte[0]]
    for vorher, nachher, wert in zip(zeit, zeit[1:], werte[1:]):
        if (nachher - vorher).total_seconds() > grenze:
            z2.append(vorher + (nachher - vorher) / 2)
            w2.append(float("nan"))
        z2.append(nachher)
        w2.append(wert)
    return z2, w2


# ==================================================================
#   1  Zeitverlauf
# ==================================================================

def plot_zeitverlauf(zeit, ph, wasser_temp, sollwert, toleranz, datei):
    fig, (oben, unten) = plt.subplots(
        2, 1, figsize=(7.0, 5.2), sharex=True,
        gridspec_kw={"height_ratios": [2, 1], "hspace": 0.12},
    )

    # --- pH ---
    t, werte = mit_luecken(*nur_gueltige(zeit, ph))
    if sollwert is not None and toleranz is not None:
        oben.axhspan(sollwert - toleranz, sollwert + toleranz,
                     color=ZIELBAND, alpha=0.10, linewidth=0, zorder=0)
        # Saum in Weiss, damit der Text lesbar bleibt, wo die Linie ihn kreuzt
        oben.text(0.012, sollwert - toleranz, "  Zielbereich",
                  transform=oben.get_yaxis_transform(),
                  va="bottom", ha="left", fontsize=8, color=TEXT_LEISE,
                  path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    oben.plot(t, werte, color=SERIE, linewidth=1.6,
              solid_joinstyle="round", solid_capstyle="round")
    oben.set_ylabel("pH-Wert")          # dimensionslos, daher ohne Einheit
    aufraeumen(oben)

    # --- Wassertemperatur ---
    t2, temps = nur_gueltige(zeit, wasser_temp)
    if temps:
        t2, temps = mit_luecken(t2, temps)
        unten.plot(t2, temps, color=SERIE, linewidth=1.6,
                   solid_joinstyle="round", solid_capstyle="round")
    else:
        unten.text(0.5, 0.5, "keine Temperaturwerte im Log",
                   transform=unten.transAxes, ha="center", va="center",
                   color=TEXT_LEISE, fontsize=8)
    unten.set_ylabel("Wassertemperatur in °C")
    unten.set_xlabel("Uhrzeit")
    aufraeumen(unten)

    # Nur die Uhrzeit anzeigen - das Datum gehoert in die Bildunterschrift.
    unten.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    fig.savefig(datei)
    plt.close(fig)
    print(f"  {datei}   pH-Verlauf und Wassertemperatur ({len(werte)} Punkte)")


# ==================================================================
#   2  Kalibriergerade
# ==================================================================

def plot_kennlinie(ph, spannung, datei):
    paare = [(p, u) for p, u in zip(ph, spannung) if p is not None and u is not None]
    if len(paare) < 3:
        print("  Zu wenige Wertepaare fuer die Kennlinie - uebersprungen.")
        return

    x = np.array([p for p, _ in paare])
    y = np.array([u for _, u in paare])

    steigung, achsenabschnitt = np.polyfit(x, y, 1)     # U = m * pH + b
    modell = steigung * x + achsenabschnitt
    streuung = y - modell
    r2 = 1 - streuung.var() / y.var() if y.var() > 0 else float("nan")
    steilheit_mv = abs(steigung) * 1000.0

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.plot(x, y, "o", color=SERIE, markersize=4,
            markeredgecolor="white", markeredgewidth=0.8, alpha=0.75)

    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, steigung * xs + achsenabschnitt,
            color=TEXT_LEISE, linewidth=1.2, zorder=3)

    ax.set_xlabel("pH-Wert")
    ax.set_ylabel("Sensorspannung in V")

    bewertung = "im Nernst-Bereich" if 50 <= steilheit_mv <= 59 else "AUSSERHALB 50-59 mV/pH"
    ax.text(0.98, 0.96,
            f"Steilheit  {steilheit_mv:.1f} mV/pH\n"
            f"{bewertung}\n"
            f"R²  {r2:.4f}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=8, color=TEXT_LEISE, linespacing=1.5)
    aufraeumen(ax)

    fig.savefig(datei)
    plt.close(fig)
    print(f"  {datei}   Kennlinie: {steilheit_mv:.1f} mV/pH, R² = {r2:.4f}")

    if not 50 <= steilheit_mv <= 59:
        print(f"     ACHTUNG: {steilheit_mv:.1f} mV/pH liegt ausserhalb des "
              "plausiblen Bereichs. Elektrode oder Kalibrierung pruefen.")


# ==================================================================
#   3  Titrationskurve und Empfindlichkeit
# ==================================================================

def plot_titration(volumen, ph, datei):
    paare = sorted(zip(volumen, ph))
    v = np.array([a for a, _ in paare])
    p = np.array([b for _, b in paare])

    fig, (oben, unten) = plt.subplots(
        2, 1, figsize=(7.0, 5.6),
        gridspec_kw={"height_ratios": [3, 2], "hspace": 0.35},
    )

    # --- Dosis-Wirkung ---
    oben.plot(v, p, "-o", color=SERIE, linewidth=1.6, markersize=4,
              markeredgecolor="white", markeredgewidth=0.8)
    oben.set_xlabel("Zugegebene Menge pH-Minus in ml/l")
    oben.set_ylabel("pH-Wert")
    aufraeumen(oben)

    # --- Empfindlichkeit: die Nichtlinearitaet als Zahl ---
    if len(v) >= 2:
        d_ph = np.diff(p)
        d_v = np.diff(v)
        gueltig = d_v != 0
        empfindlichkeit = np.abs(d_ph[gueltig] / d_v[gueltig])
        ph_mitte = ((p[:-1] + p[1:]) / 2)[gueltig]

        unten.plot(ph_mitte, empfindlichkeit, "-o", color=SERIE,
                   linewidth=1.6, markersize=4,
                   markeredgecolor="white", markeredgewidth=0.8)
        unten.set_xlabel("pH-Wert")
        unten.set_ylabel("Empfindlichkeit\nin ΔpH je ml/l")
    aufraeumen(unten)

    fig.savefig(datei)
    plt.close(fig)
    print(f"  {datei}   Titrationskurve und Empfindlichkeit ({len(v)} Punkte)")


# ==================================================================
#   Einstieg
# ==================================================================

def zeitpunkt(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(
        description="Erzeugt die Diagramme zur Messreihe.")
    parser.add_argument("logdatei", nargs="?", default="hydroponik_log.csv")
    parser.add_argument("--titration", metavar="DATEI",
                        help="zusaetzlich die Titrationskurve zeichnen")
    parser.add_argument("--von", type=zeitpunkt, metavar='"YYYY-MM-TT HH:MM:SS"',
                        help="nur Messungen ab diesem Zeitpunkt")
    parser.add_argument("--bis", type=zeitpunkt, metavar='"YYYY-MM-TT HH:MM:SS"',
                        help="nur Messungen bis zu diesem Zeitpunkt")
    parser.add_argument("--sollwert", type=float, default=5.8)
    parser.add_argument("--toleranz", type=float, default=0.2)
    parser.add_argument("--praefix", default="diagramm",
                        help="Namensanfang der erzeugten Dateien")
    argumente = parser.parse_args()

    try:
        zeit, ph, spannung, wasser_temp = lies_log(
            argumente.logdatei, argumente.von, argumente.bis)
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {argumente.logdatei}")
        sys.exit(1)

    print(f"{len(zeit)} Zeilen aus {argumente.logdatei}\n")

    plot_zeitverlauf(zeit, ph, wasser_temp,
                     argumente.sollwert, argumente.toleranz,
                     f"{argumente.praefix}_verlauf.png")
    plot_kennlinie(ph, spannung, f"{argumente.praefix}_kennlinie.png")

    if argumente.titration:
        try:
            volumen, titration_ph = lies_titration(argumente.titration)
        except FileNotFoundError:
            print(f"Datei nicht gefunden: {argumente.titration}")
            sys.exit(1)
        plot_titration(volumen, titration_ph, f"{argumente.praefix}_titration.png")

    print("\nFertig. Die PNG-Dateien haben 300 dpi und sind druckfertig.")


if __name__ == "__main__":
    main()
