"""
ocr.py - OCR for FMB PDF
Currently using Tesseract (free)
Claude Vision code kept for future use
"""
import pytesseract
import numpy as np
from PIL import Image
import re
import io

# Windows Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def ocr_image(image_bytes: bytes, api_key: str = "") -> list:
    """
    OCR the FMB image using Tesseract
    Returns list of: {text, x, y, color}
    api_key param kept for future Claude Vision switch
    """
    img = Image.open(io.BytesIO(image_bytes))
    img_arr = np.array(img)

    results = []

    # ── Pass 1: Full image OCR (black text) ──────────────────────
    data = pytesseract.image_to_data(
        img, output_type=pytesseract.Output.DICT,
        config='--psm 11 --oem 3'
    )
    for i in range(len(data['text'])):
        txt = data['text'][i].strip()
        if txt and int(data['conf'][i]) > 25:
            x = (data['left'][i] + data['width'][i] / 2)
            y = (data['top'][i] + data['height'][i] / 2)
            results.append({
                "text": txt, "x": x, "y": y,
                "color": "black", "conf": int(data['conf'][i])
            })

    # ── Pass 2: Red channel only (red text = corners A-H) ────────
    red_mask = (
        (img_arr[:,:,0] > 150) &
        (img_arr[:,:,1] < 100) &
        (img_arr[:,:,2] < 100)
    )
    red_img_arr = np.full_like(img_arr, 255)
    red_img_arr[red_mask] = img_arr[red_mask]
    red_img = Image.fromarray(red_img_arr)

    rd = pytesseract.image_to_data(
        red_img, output_type=pytesseract.Output.DICT,
        config='--psm 11 --oem 3 -c tessedit_char_whitelist=ABCDEFGH0123456789 '
    )
    for i in range(len(rd['text'])):
        txt = rd['text'][i].strip()
        if txt and int(rd['conf'][i]) > 20:
            x = (rd['left'][i] + rd['width'][i] / 2)
            y = (rd['top'][i] + rd['height'][i] / 2)
            results.append({
                "text": txt, "x": x, "y": y,
                "color": "red", "conf": int(rd['conf'][i])
            })

    # ── Pass 3: Blue channel only (blue text = chain distances) ───
    blue_mask = (
        (img_arr[:,:,2] > 150) &
        (img_arr[:,:,0] < 120) &
        (img_arr[:,:,1] < 150)
    )
    blue_img_arr = np.full_like(img_arr, 255)
    blue_img_arr[blue_mask] = img_arr[blue_mask]
    blue_img = Image.fromarray(blue_img_arr)

    bd = pytesseract.image_to_data(
        blue_img, output_type=pytesseract.Output.DICT,
        config='--psm 11 --oem 3'
    )
    for i in range(len(bd['text'])):
        txt = bd['text'][i].strip()
        if txt and int(bd['conf'][i]) > 20:
            x = (bd['left'][i] + bd['width'][i] / 2)
            y = (bd['top'][i] + bd['height'][i] / 2)
            results.append({
                "text": txt, "x": x, "y": y,
                "color": "blue", "conf": int(bd['conf'][i])
            })

    return results


def detect_text_colors(image_arr, results: list, zoom: float = 1.0) -> list:
    """Verify colors by sampling actual pixels"""
    for item in results:
        x = int(item["x"])
        y = int(item["y"])
        r = 8

        x1 = max(0, x - r); x2 = min(image_arr.shape[1], x + r)
        y1 = max(0, y - r); y2 = min(image_arr.shape[0], y + r)

        region = image_arr[y1:y2, x1:x2]
        if region.size == 0:
            continue

        not_white = (region[:,:,0]<220)|(region[:,:,1]<220)|(region[:,:,2]<220)
        if not not_white.any():
            continue

        pixels = region[not_white]
        avg_r = pixels[:,0].mean()
        avg_g = pixels[:,1].mean()
        avg_b = pixels[:,2].mean()

        if avg_r > 160 and avg_g < 100 and avg_b < 100:
            item["color"] = "red"
        elif avg_b > 160 and avg_r < 120:
            item["color"] = "blue"

    return results


# ═══════════════════════════════════════════════════════════════════
# CLAUDE VISION CODE — kept for future use
# Uncomment and replace ocr_image() above when credits available
# ═══════════════════════════════════════════════════════════════════
#
# def ocr_image_claude(image_bytes: bytes, api_key: str) -> list:
#     import anthropic, base64, json
#     client = anthropic.Anthropic(api_key=api_key)
#     b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
#     prompt = """Extract ALL text from this Tamil Nadu FMB survey drawing.
#     Return JSON array: [{"text":"A","x":120,"y":310,"color":"red"}, ...]
#     RED=corners(A-H)+chain points, BLUE=chain distances, BLACK=measurements+SF numbers"""
#     response = client.messages.create(
#         model="claude-sonnet-4-6", max_tokens=4096,
#         messages=[{"role":"user","content":[
#             {"type":"image","source":{"type":"base64",
#              "media_type":"image/png","data":b64}},
#             {"type":"text","text":prompt}
#         ]}]
#     )
#     raw = response.content[0].text.strip()
#     match = re.search(r'\[.*\]', raw, re.DOTALL)
#     if not match: return []
#     results = json.loads(match.group())
#     return [{"text":str(r["text"]).strip(),"x":float(r["x"]),
#              "y":float(r["y"]),"color":str(r.get("color","black")),
#              "conf":1.0} for r in results if "text" in r]