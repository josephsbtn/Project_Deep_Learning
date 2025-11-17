# utils/enhancement.py
import cv2
import numpy as np

def apply_clahe(image, clipLimit=3.0, tileGridSize=(8,8), **kwargs):
    # **kwargs absorbs any extra parameters like brightness/contrast
    if image is None: return None
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def apply_hist_equalization(image, **kwargs):
    # Add **kwargs to ignore extra parameters
    if image is None: return None
    img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

def apply_contrast_stretching(image, **kwargs):
    # Add **kwargs to ignore extra parameters
    if image is None: return None
    in_min = image.min()
    in_max = image.max()
    if in_max - in_min == 0:
        return image.copy()
    out = ((image - in_min) * (255.0 / (in_max - in_min))).astype('uint8')
    return out

def apply_enhancement(image, kind="CLAHE", **kwargs):
    kind = kind.upper()
    if kind == "CLAHE":
        # Only pass CLAHE-specific parameters
        clahe_params = {
            k: v for k, v in kwargs.items() 
            if k in ['clipLimit', 'tileGridSize']
        }
        return apply_clahe(image, **clahe_params)
    if kind in ["HE", "HIST", "HIST_EQ"]:
        return apply_hist_equalization(image)
    if kind in ["BRIGHTNESS", "BC"]:
        return apply_brightness_contrast(
            image, 
            brightness=kwargs.get("brightness", 0), 
            contrast=kwargs.get("contrast", 0)
        )
    if kind in ["CS", "CONTRAST_STRETCH"]:
        return apply_contrast_stretching(image)
    return image
