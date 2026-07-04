# CarForge

CarForge is a Flask web app for car enthusiasts. It detects license plates in vehicle photos and anonymizes them with either pixelation or AI-assisted inpainting.

## Features

- Automatic license plate detection
- Pixelation mode
- Smart remove mode with LaMa inpainting
- Frontend progress indicator
- Temporary image processing without permanent upload storage
- Downloadable result image

## Demo Workflow

1. Upload a vehicle image.
2. Choose **Verpixeln** or **Smart Entfernen**.
3. Wait for processing to finish.
4. Download the anonymized image.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Model

CarForge expects the license plate detection model at:

```text
models/license-plate-finetune-v1l.pt
```

The model is not included in this repository. Download it from Hugging Face:

```text
https://huggingface.co/morsetechlab/yolov11-license-plate-detection/resolve/main/license-plate-finetune-v1l.pt
```

Model page:

```text
https://huggingface.co/morsetechlab/yolov11-license-plate-detection
```

## Project Structure

```text
app.py
utils.py
requirements.txt
models/
static/
templates/
```

## Production

For production, run the Flask app behind a WSGI server and reverse proxy, for example:

```bash
gunicorn -w 1 -b 127.0.0.1:8000 app:app
```

Use a reverse proxy such as Nginx or Caddy for HTTPS.

## License

This project is intended to be published under the GNU Affero General Public License v3.0.

It uses AGPL-3.0 components, including Ultralytics and the referenced license plate detection model. See the upstream projects for their respective license terms.
