"""Keep existing ASCII-path preprocessing; support Unicode filenames on Windows."""
from pathlib import Path
import cv2
import numpy as np


def face_image_input(path):
    path=Path(path).expanduser()
    text=str(path)
    if text.isascii():
        # Preserve the library's existing path-loading behavior for validated data.
        return text
    pixels=cv2.imdecode(np.frombuffer(path.read_bytes(),dtype=np.uint8),cv2.IMREAD_COLOR)
    if pixels is None:raise ValueError('The photograph could not be decoded.')
    # DeepFace accepts BGR arrays and therefore does not reject a Unicode path.
    return pixels
