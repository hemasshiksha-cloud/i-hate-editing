"""Person cutout -> RGBA PNG. usage: cutout.py out_dir img..."""
import sys, os, numpy as np, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
from PIL import Image, ImageOps, ImageFilter
M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models/selfie_multiclass.tflite")
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=mpt.BaseOptions(model_asset_path=M), output_confidence_masks=True))
out = sys.argv[1]
for p in sys.argv[2:]:
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(im))))
    m = 1 - np.squeeze(np.array(r.confidence_masks[0].numpy_view(), dtype=np.float32))
    m = np.clip((m - .35) / .3, 0, 1)
    al = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    rgba = im.convert("RGBA"); rgba.putalpha(al)
    rgba.save(os.path.join(out, os.path.basename(p).split("-")[0] + "_cut.png")); print("cut", p, round(float(m.mean()), 3), flush=True)
seg.close()
