# CarForge

CarForge ist eine kleine Flask-Webapp fuer Auto-Liebhaber. Bilder koennen hochgeladen werden, Kennzeichen werden erkannt und anschliessend anonymisiert.

## Features

- Kennzeichen automatisch erkennen
- Methode **Verpixeln**
- Methode **Smart Entfernen** mit LaMa-Inpainting
- Fortschritt im Frontend und in der Konsole
- Keine dauerhafte Speicherung von Uploads oder Ergebnissen
- Impressum und Datenschutzerklaerung enthalten

## Datenschutz-Konzept

Uploads werden nur temporaer verarbeitet:

1. Das hochgeladene Bild wird in den Arbeitsspeicher gelesen.
2. Waehrend der Verarbeitung wird ein temporaeres Verzeichnis mit `tempfile.TemporaryDirectory()` erstellt.
3. Input- und Output-Dateien liegen nur in diesem temporaeren Verzeichnis.
4. Nach Abschluss wird das temporaere Verzeichnis automatisch geloescht.
5. Das Ergebnis wird als Base64 in die Ergebnis-Seite eingebettet.
6. Nach Abruf der Ergebnis-Seite wird der Job aus dem Server-RAM entfernt.

## Projektstruktur

```text
app.py
utils.py
requirements.txt
models/
  license-plate-finetune-v1l.pt
static/
templates/
```

## Installation lokal

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Danach im Browser oeffnen:

```text
http://127.0.0.1:5000
```

## Produktion

Die App sollte online nicht mit `debug=True` betrieben werden. Fuer Linux-Server ist z.B. Gunicorn geeignet:

```bash
cd backend
gunicorn -w 1 -b 127.0.0.1:8000 app:app
```

Davor sollte ein Reverse Proxy wie Nginx oder Caddy fuer HTTPS laufen.

## Modell

Das verwendete Modell stammt von Hugging Face:

```text
morsetechlab/yolov11-license-plate-detection
```

Modelldatei:

```text
models/license-plate-finetune-v1l.pt
```

Modellseite:

```text
https://huggingface.co/morsetechlab/yolov11-license-plate-detection
```

Die Modellseite nennt als Lizenz **AGPL-3.0**.

Die Modelldatei wird nicht ins Git-Repository committed. Lade sie vor dem Start
von Hugging Face herunter und lege sie hier ab:

```text
models/license-plate-finetune-v1l.pt
```

Direkter Download:

```text
https://huggingface.co/morsetechlab/yolov11-license-plate-detection/resolve/main/license-plate-finetune-v1l.pt
```

## Lizenzen und Hinweise

Dieses Projekt nutzt unter anderem:

- Flask
- Gunicorn
- Ultralytics
- OpenCV
- NumPy
- Pillow
- simple-lama-inpainting
- morsetechlab/yolov11-license-plate-detection

Da Ultralytics und das verwendete Modell AGPL-3.0-lizenziert sind, sollte der Quellcode dieses Webdienstes fuer Nutzer verfuegbar gemacht werden.

Empfohlene Repo-Lizenz:

```text
GNU Affero General Public License v3.0
```

## Betriebshinweise

- Hetzner-AVV abschliessen
- Impressum und Datenschutz erreichbar halten
- Keine Testbilder oder fremde Bilder ins Repo hochladen
- `__pycache__`, `.venv`, lokale Ausgaben und `.pt`-Modelldateien nicht committen
- Serverlogs bewusst konfigurieren
