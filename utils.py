from ultralytics import YOLO
import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image

# Modelle nur einmal laden
BASE_DIR = Path(__file__).resolve().parent
plate_model = YOLO(BASE_DIR / "models" / "license-plate-finetune-v1l.pt")
lama = None


def get_lama():
    global lama

    if lama is None:
        from simple_lama_inpainting import SimpleLama
        lama = SimpleLama()

    return lama


class ProgressBar:
    def __init__(self, total_steps, width=32, enabled=False, callback=None):
        self.total_steps = total_steps
        self.width = width
        self.enabled = enabled
        self.callback = callback
        self.current_step = 0
        self.started_at = time.monotonic()

    def update(self, label):
        self.current_step += 1
        percent = min(100, round(self.current_step / self.total_steps * 100))

        if self.callback:
            self.callback(percent, label)

        if not self.enabled:
            return

        filled = round(self.width * percent / 100)
        bar = "#" * filled + "-" * (self.width - filled)
        elapsed = time.monotonic() - self.started_at
        print(
            f"\r[{bar}] {percent:3d}% {label} ({elapsed:.1f}s)",
            end="",
            flush=True
        )

        if self.current_step >= self.total_steps:
            print()


def create_mask(image, boxes, padding=28):
    height, width = image.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)

        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

    return mask


def inpaint_masked_area(image_bgr, mask, padding=96):
    ys, xs = np.where(mask > 0)

    if len(xs) == 0 or len(ys) == 0:
        return image_bgr

    height, width = image_bgr.shape[:2]
    x1 = max(0, int(xs.min()) - padding)
    y1 = max(0, int(ys.min()) - padding)
    x2 = min(width, int(xs.max()) + padding)
    y2 = min(height, int(ys.max()) + padding)

    image_crop = image_bgr[y1:y2, x1:x2]
    mask_crop = mask[y1:y2, x1:x2]

    image_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)
    mask_pil = Image.fromarray(mask_crop).convert("L")

    result_pil = get_lama()(image_pil, mask_pil)
    result_rgb = np.array(result_pil)
    result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)

    crop_height, crop_width = image_crop.shape[:2]
    if result_bgr.shape[:2] != (crop_height, crop_width):
        result_bgr = cv2.resize(
            result_bgr,
            (crop_width, crop_height),
            interpolation=cv2.INTER_LINEAR
        )

    result = image_bgr.copy()
    blended_crop = np.where(mask_crop[..., None] > 0, result_bgr, image_crop)
    result[y1:y2, x1:x2] = blended_crop

    return result


def blur_license_plates(
    input_path,
    output_path,
    confidence=0.35,
    mode="frosted",
    show_progress=True,
    progress_callback=None
):
    progress = ProgressBar(
        total_steps=5,
        enabled=show_progress,
        callback=progress_callback
    )

    progress.update("Bild wird geladen")
    image_bgr = cv2.imread(input_path)

    if image_bgr is None:
        raise Exception("Bild konnte nicht geladen werden.")

    progress.update("Kennzeichen werden erkannt")
    results = plate_model.predict(
        source=image_bgr,
        device="cpu",
        conf=confidence,
        imgsz=960,
        verbose=False
    )

    boxes = results[0].boxes

    if len(boxes) == 0:
        progress.update("Keine Kennzeichen gefunden")
        progress.update("Originalbild wird gespeichert")
        cv2.imwrite(output_path, image_bgr)
        progress.update("Fertig")
        return 0

    progress.update("Maske wird erstellt")
    mask = create_mask(image_bgr, boxes, padding=28)

    progress.update("Kennzeichen werden verpixelt")
    if mode == "pixel":
        small = cv2.resize(image_bgr, None, fx=0.06, fy=0.06, interpolation=cv2.INTER_LINEAR)
        processed = cv2.resize(
            small,
            (image_bgr.shape[1], image_bgr.shape[0]),
            interpolation=cv2.INTER_NEAREST
        )
    else:
        small = cv2.resize(image_bgr, None, fx=0.035, fy=0.035, interpolation=cv2.INTER_LINEAR)
        frosted = cv2.resize(
            small,
            (image_bgr.shape[1], image_bgr.shape[0]),
            interpolation=cv2.INTER_LINEAR
        )
        processed = cv2.GaussianBlur(frosted, (51, 51), 0)

    result_bgr = np.where(mask[..., None] > 0, processed, image_bgr)

    progress.update("Ergebnis wird gespeichert")
    cv2.imwrite(output_path, result_bgr)

    return len(boxes)


def remove_license_plates_lama(
    input_path,
    output_path,
    confidence=0.35,
    show_progress=False,
    progress_callback=None
):
    progress = ProgressBar(
        total_steps=5,
        enabled=show_progress,
        callback=progress_callback
    )

    progress.update("Bild wird geladen")
    image_bgr = cv2.imread(input_path)

    if image_bgr is None:
        raise Exception("Bild konnte nicht geladen werden.")

    progress.update("Kennzeichen werden erkannt")
    results = plate_model.predict(
        source=image_bgr,
        device="cpu",
        conf=confidence,
        imgsz=960,
        verbose=False
    )

    boxes = results[0].boxes

    if len(boxes) == 0:
        progress.update("Keine Kennzeichen gefunden")
        progress.update("Originalbild wird gespeichert")
        cv2.imwrite(output_path, image_bgr)
        progress.update("Fertig")
        return 0

    progress.update("Maske wird erstellt")
    mask = create_mask(image_bgr, boxes, padding=28)

    progress.update("Kennzeichen werden entfernt")
    result_bgr = inpaint_masked_area(image_bgr, mask, padding=96)

    progress.update("Ergebnis wird gespeichert")
    cv2.imwrite(output_path, result_bgr)

    return len(boxes)


if __name__ == "__main__":
    anzahl = remove_license_plates_lama(
        input_path="test2.jpg",
        output_path="auto_lama.jpg",
        show_progress=True,  
    )
    #anzahl = blur_license_plates(
    #    input_path="test2.jpg",
    #    output_path="auto_blur.jpg",
    #    mode="frosted"
    #)

    print(f"{anzahl} Kennzeichen entfernt.")
