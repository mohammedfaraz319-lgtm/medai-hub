"""Skin-lesion screening from a photo using the clinical ABCD rule.

HOW IT WORKS (honest description): the lesion is segmented from the surrounding
skin with Otsu thresholding, then four measurable ABCD features are computed:
  A - Asymmetry, B - Border irregularity, C - Colour variation, D - Diameter.
These features (plus darkness and redness) are mapped to likelihoods for common
lesion types with a transparent weighted scoring function.

This is a *screening heuristic for a student project*, not a trained deep
network. To upgrade it, train a CNN on HAM10000 and replace `score_classes`.
"""
import base64
import io

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage as ndi

CLASSES = [
    "Melanocytic Nevus",
    "Melanoma (suspicious)",
    "Basal Cell Carcinoma",
    "Benign Keratosis",
    "Dermatofibroma",
    "Actinic Keratosis",
    "Vascular Lesion",
]

URGENCY = {
    "Melanocytic Nevus": ("low", "Typically a benign mole. Keep monitoring for change in size, shape or colour."),
    "Benign Keratosis": ("low", "Usually a harmless skin growth. A doctor can confirm."),
    "Dermatofibroma": ("low", "Usually a harmless firm skin nodule."),
    "Vascular Lesion": ("low", "Usually harmless blood-vessel related lesion. Confirm with a dermatologist."),
    "Actinic Keratosis": ("medium", "A sun-damage patch that can become cancerous. Dermatologist review is advised."),
    "Basal Cell Carcinoma": ("high", "A common skin cancer. See a dermatologist for examination."),
    "Melanoma (suspicious)": ("high", "Features that need prompt dermatologist evaluation. Early detection is critical."),
}


def _otsu(values, bins=64):
    hist, edges = np.histogram(values, bins=bins)
    hist = hist.astype(float)
    total = hist.sum()
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = total - w0
    m0 = np.cumsum(hist * centers) / np.maximum(w0, 1)
    m1 = (np.sum(hist * centers) - np.cumsum(hist * centers)) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return centers[np.argmax(between)]


def _segment(arr):
    h, w, _ = arr.shape
    bh, bw = max(2, h // 10), max(2, w // 10)
    border = np.concatenate([
        arr[:bh].reshape(-1, 3), arr[-bh:].reshape(-1, 3),
        arr[:, :bw].reshape(-1, 3), arr[:, -bw:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(arr - bg, axis=2)
    dist = ndi.gaussian_filter(dist, 2)
    mask = dist > _otsu(dist.ravel())
    mask = ndi.binary_closing(mask, iterations=2)
    mask = ndi.binary_fill_holes(mask)
    mask = ndi.binary_opening(mask, iterations=2)
    lab, n = ndi.label(mask)
    ok = True
    if n:
        sizes = ndi.sum(mask, lab, range(1, n + 1))
        mask = lab == (np.argmax(sizes) + 1)
    frac = mask.mean()
    if n == 0 or frac < 0.01 or frac > 0.85:
        # fallback: central ellipse so the pipeline still returns something
        yy, xx = np.ogrid[:h, :w]
        mask = ((yy - h / 2) / (h * .3)) ** 2 + ((xx - w / 2) / (w * .3)) ** 2 <= 1
        ok = False
    return mask, bg, ok


def _features(arr, mask, bg):
    h, w, _ = arr.shape
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = mask[y0:y1, x0:x1]
    area = crop.sum()

    # A - asymmetry: overlap of lesion with its mirror images
    def iou(a, b):
        return (a & b).sum() / max((a | b).sum(), 1)
    asym = 1 - (iou(crop, crop[:, ::-1]) + iou(crop, crop[::-1, :])) / 2

    # B - border irregularity vs. a disc of equal area (same pixel-perimeter method)
    def perimeter(m):
        return (m & ~ndi.binary_erosion(m)).sum()
    r = np.sqrt(area / np.pi)
    yy, xx = np.ogrid[:int(2 * r) + 4, :int(2 * r) + 4]
    disc = (yy - r - 2) ** 2 + (xx - r - 2) ** 2 <= r ** 2
    ratio = (perimeter(crop) ** 2 / max(area, 1)) / max(perimeter(disc) ** 2 / max(disc.sum(), 1), 1e-6)
    border = float(np.clip((ratio - 1) / 1.5, 0, 1))

    # C - colour variation inside the lesion
    px = arr[mask]
    bins = (px // 48).astype(int)
    keys, counts = np.unique(bins[:, 0] * 100 + bins[:, 1] * 10 + bins[:, 2], return_counts=True)
    n_colors = int((counts / counts.sum() > .06).sum())
    color = float(np.clip(0.55 * np.clip(px.std(axis=0).mean() / 45, 0, 1) + 0.45 * np.clip((n_colors - 1) / 4, 0, 1), 0, 1))

    # D - diameter proxy: lesion extent as fraction of image width
    diameter = float(np.clip(max(y1 - y0, x1 - x0) / max(h, w) / 0.7, 0, 1))

    lesion = px.mean(axis=0)
    dark = float(np.clip((bg.mean() - lesion.mean()) / 120, 0, 1))
    red = float(np.clip(((lesion[0] - (lesion[1] + lesion[2]) / 2) - (bg[0] - (bg[1] + bg[2]) / 2)) / 60, 0, 1))
    return {"asymmetry": float(np.clip(asym * 2, 0, 1)), "border": border, "color": color,
            "diameter": diameter, "dark": dark, "red": red}


def score_classes(f):
    A, B, C, D, dark, red = f["asymmetry"], f["border"], f["color"], f["diameter"], f["dark"], f["red"]
    logits = {
        "Melanocytic Nevus": 2.7 - 2.4 * A - 2.4 * B - 2.8 * C + 0.8 * dark - 0.2 * red,
        "Melanoma (suspicious)": -3.0 + 3.2 * A + 3.4 * B + 4.0 * C + 1.2 * dark,
        "Basal Cell Carcinoma": -0.9 + 1.4 * red + 1.2 * B + 0.8 * (1 - dark) + 0.6 * C,
        "Benign Keratosis": -0.2 + 0.8 * B + 0.8 * C - 0.8 * red + 0.4 * dark - 0.6 * A,
        "Dermatofibroma": -0.4 + 0.9 * (1 - C) + 0.6 * (1 - A) + 0.5 * red,
        "Actinic Keratosis": -1.0 + 1.3 * red + 0.9 * B + 0.5 * (1 - dark),
        "Vascular Lesion": -1.6 + 3.2 * red - 1.2 * dark - 0.6 * B,
    }
    z = np.array([logits[c] for c in CLASSES])
    p = np.exp(z - z.max())
    return p / p.sum()


def _overlay(img, mask):
    big = img.copy()
    m = Image.fromarray((mask * 255).astype("uint8")).resize(big.size)
    edge = np.array(m) > 127
    edge = edge & ~ndi.binary_erosion(edge, iterations=2)
    arr = np.array(big)
    arr[edge] = [255, 60, 60]
    out = Image.fromarray(arr)
    out.thumbnail((420, 420))
    buf = io.BytesIO()
    out.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def analyze(file_obj):
    img = Image.open(file_obj)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((512, 512))
    small = img.copy()
    small.thumbnail((256, 256))
    arr = np.asarray(small, dtype=float)

    mask, bg, segmented = _segment(arr)
    feats = _features(arr, mask, bg)
    probs = score_classes(feats)
    order = np.argsort(-probs)
    ranked = [{"label": CLASSES[i], "prob": round(float(probs[i]) * 100, 1)} for i in order]
    top = ranked[0]
    urgency, note = URGENCY[top["label"]]
    return {
        "top_prediction": top["label"],
        "confidence": top["prob"],
        "ranked": ranked,
        "urgency": urgency,
        "note": note,
        "abcd": {k: round(feats[k] * 100) for k in ("asymmetry", "border", "color", "diameter")},
        "segmented": segmented,
        "overlay": _overlay(small, mask),
        "method": "ABCD-rule heuristic (not a trained neural network)",
    }
