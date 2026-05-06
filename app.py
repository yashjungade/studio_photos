import os
import requests
from flask import Flask, render_template, request, jsonify
# from rembg import remove
from PIL import Image, ImageEnhance, ImageOps

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# def remove_background(image_path):
#     """Remove background from image using rembg library."""
#     output_path = image_path.replace(".", "_local.")
#     with open(image_path, "rb") as i:
#         with open(output_path, "wb") as o:
#             o.write(remove(i.read()))
#     return output_path

def remove_background(image_path):
    # try:
    url = "https://api.remove.bg/v1.0/removebg"
    with open(image_path, "rb") as img:
        response = requests.post(
            url,
            files={"image_file": img},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
            timeout=10
        )
    if response.status_code == 200:
        output_path = os.path.join(UPLOAD_FOLDER, "no_bg.png")
        with open(output_path, "wb") as out:
            out.write(response.content)
        return output_path
    #     else:
    #         return remove_bg_local(image_path)
    # except:
    #     return remove_bg_local(image_path)

def enhance_local(image_path):
    """Apply comprehensive local image enhancements."""
    img = Image.open(image_path)

    # Convert RGBA to RGB if necessary
    if img.mode == "RGBA":
        img = img.convert("RGB")

    # Enhance sharpness
    sharpness_enhancer = ImageEnhance.Sharpness(img)
    img = sharpness_enhancer.enhance(2.5)  # Increased from 2.0

    # Enhance contrast
    contrast_enhancer = ImageEnhance.Contrast(img)
    img = contrast_enhancer.enhance(1.4)  # Increased from 1.3

    # Enhance brightness slightly
    brightness_enhancer = ImageEnhance.Brightness(img)
    img = brightness_enhancer.enhance(1.1)  # Slight brightness boost

    # Enhance color saturation
    color_enhancer = ImageEnhance.Color(img)
    img = color_enhancer.enhance(1.2)  # Boost colors slightly

    # Apply auto contrast for better dynamic range
    img = ImageOps.autocontrast(img, cutoff=2)

    output_path = image_path.replace(".", "_enhanced.")
    img.save(output_path, "JPEG", quality=95)  # Higher quality
    return output_path

def enhance_image_stability(image_path):
    """Enhance image using Stability AI API."""
    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*"
    }

    with open(image_path, "rb") as img_file:
        files = {"image": img_file}
        data = {
            "mode": "image-to-image",
            "prompt": "generate e commerce style product photography of given product photo",
            "strength": 0.5,
            "output_format": "jpeg"
        }

        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f"Stability API error: {response.text}")

    output_path = image_path.replace(".", "_stability.")
    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["image"]
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)

    # Remove background
    no_bg_path = remove_background(original_path)

    # Apply local enhancement first
    enhanced_local_path = enhance_local(no_bg_path)

    # Try Stability AI enhancement, fallback to local if fails
    try:
        enhanced_path = enhance_image_stability(enhanced_local_path)
        used_stability = True
    except Exception as e:
        print(f"Stability API failed: {e}")
        enhanced_path = enhanced_local_path
        used_stability = False

    return jsonify({
        "original": original_path,
        "no_bg":no_bg_path,
        "enhanced": enhanced_path,
        "used_stability": used_stability
    })

# if __name__ == "__main__":
#     app.run(debug=True)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)