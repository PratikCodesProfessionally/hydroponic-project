# Archivierte Programmstände

Diese Dateien laufen nicht mehr, werden aber für die Nachvollziehbarkeit der
Messreihen und der Dokumentation aufbewahrt.

| Datei | Was es ist | Wo es eine Rolle spielt |
| --- | --- | --- |
| `ganzerCode.py` | Übernommener Code aus dem Vorprojekt. Lief auf dem Pi bei **allen Messreihen bis zum 11.08.2026** (Herstellerformel mit Korrekturkonstante 8,23; 30 Messungen à 10 s je Durchlauf; Dosierung 2–5 s bei pH > 6,0; Endpunkte `/api/sensors`, `/api/pump/on`, `/api/pump/off`). | Projektdokumentation Abschnitt 4.3 (Analyse des übernommenen Codes), Anhang B, Messreihen in Anhang D |
| `hydroponik_entwurf_2026-08.py` | Neuentwurf vom 06.08.2026 mit Betriebsarten, Lock, Mengenbegrenzung. **Wurde nie an der Anlage betrieben**, alle Messreihen stammen aus `ganzerCode.py`. Konzepte daraus (zeitbegrenzter Pumpenlauf, Not-Aus ohne Lock, Sperrzeit) sind in das aktuelle `iot/hydroponik.py` eingeflossen. | nur Entwicklungsgeschichte |

Das aktuell auf dem Pi laufende Programm ist `iot/hydroponik.py` (überarbeitete
Fassung von `ganzerCode.py`, Kalibrierung über `iot/kalibrieren.py`).
