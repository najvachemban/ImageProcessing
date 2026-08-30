import os
import time
import numpy as np
from scipy.fftpack import dct, idct
from PIL import Image

# Standard JPEG luminance quantization table
_QY = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
], dtype=np.float64)


def _dct2(block: np.ndarray) -> np.ndarray:
    """2D DCT via two 1D DCTs (rows, then columns) — DCT is separable."""
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def _idct2(block: np.ndarray) -> np.ndarray:
    """2D Inverse DCT, same separable approach."""
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


def _scale_quant_table(quality: int) -> np.ndarray:
    """Scales the base quantization table by JPEG's standard quality formula."""
    quality = max(1, min(quality, 100))
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - 2 * quality
    table = np.floor((_QY * scale + 50) / 100)
    return np.clip(table, 1, 255)


def _compress_channel_dct(channel: np.ndarray, quality: int) -> np.ndarray:
    """Applies block-wise DCT + quantization + reconstruction to one 2D channel."""
    h, w = channel.shape
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    padded = np.pad(channel, ((0, pad_h), (0, pad_w)), mode="edge")

    quant_table = _scale_quant_table(quality)
    out = np.zeros_like(padded)

    for i in range(0, padded.shape[0], 8):
        for j in range(0, padded.shape[1], 8):
            block = padded[i:i+8, j:j+8] - 128  # center around 0, as JPEG does
            dct_block = _dct2(block)
            quantized = np.round(dct_block / quant_table)   # <-- lossy step
            dequantized = quantized * quant_table
            restored = _idct2(dequantized) + 128
            out[i:i+8, j:j+8] = restored

    out = out[:h, :w]  # remove padding
    return np.clip(out, 0, 255).astype(np.uint8)


def compress_image_dct(input_path: str, output_path: str, quality: int = 50, mode: str = "grayscale") -> dict:
    """
    Compresses an image using block-based DCT + quantization (JPEG's core algorithm).
    mode="grayscale": single-channel.
    mode="color": per-channel (R, G, B) independently.
    Saves the final result as an actual JPEG file, so compressed_size reflects
    real entropy-coded file size, not just the pixel-level transform.
    Returns stats about the operation.
    """
    start_time = time.perf_counter()

    if mode == "color":
        img = Image.open(input_path).convert("RGB")
        arr = np.array(img, dtype=np.float64)
        channels_compressed = [_compress_channel_dct(arr[:, :, c], quality) for c in range(3)]
        compressed_matrix = np.stack(channels_compressed, axis=2)
        compressed_img = Image.fromarray(compressed_matrix, mode="RGB")
    else:
        img = Image.open(input_path).convert("L")
        arr = np.array(img, dtype=np.float64)
        compressed_matrix = _compress_channel_dct(arr, quality)
        compressed_img = Image.fromarray(compressed_matrix, mode="L")

    compressed_img.save(output_path, format="JPEG", quality=quality)

    processing_time = time.perf_counter() - start_time
    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_path)

    return {
        "mode": mode,
        "quality_used": quality,
        "original_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "compression_ratio": round(original_size / compressed_size, 2) if compressed_size else None,
        "processing_time_seconds": round(processing_time, 3),
    }