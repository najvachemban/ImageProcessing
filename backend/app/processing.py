import os
import time
import numpy as np
from PIL import Image


def _svd_compress_channel(channel: np.ndarray, k: int) -> np.ndarray:
    """Applies rank-k SVD approximation to a single 2D channel matrix."""
    U, S, Vt = np.linalg.svd(channel, full_matrices=False)

    max_k = min(channel.shape)
    k = min(k, max_k)

    U_k = U[:, :k]
    S_k = np.diag(S[:k])
    Vt_k = Vt[:k, :]

    reconstructed = U_k @ S_k @ Vt_k
    return np.clip(reconstructed, 0, 255).astype(np.uint8), k


def compress_image_svd(input_path: str, output_path: str, k: int, mode: str = "grayscale") -> dict:
    """
    Compresses an image using rank-k SVD approximation.
    mode="grayscale": single-channel SVD (fast, simple).
    mode="color": per-channel SVD on R, G, B independently (slower, preserves color).
    Returns stats about the operation.
    """
    start_time = time.perf_counter()

    if mode == "color":
        img = Image.open(input_path).convert("RGB")
        arr = np.array(img, dtype=np.float64)  # shape: (H, W, 3)

        channels_compressed = []
        k_used = k
        for c in range(3):  # R, G, B
            compressed_channel, k_used = _svd_compress_channel(arr[:, :, c], k)
            channels_compressed.append(compressed_channel)

        compressed_matrix = np.stack(channels_compressed, axis=2)  # back to (H, W, 3)
        compressed_img = Image.fromarray(compressed_matrix, mode="RGB")

    else:  # grayscale (default)
        img = Image.open(input_path).convert("L")
        arr = np.array(img, dtype=np.float64)  # shape: (H, W)

        compressed_matrix, k_used = _svd_compress_channel(arr, k)
        compressed_img = Image.fromarray(compressed_matrix, mode="L")

    compressed_img.save(output_path)

    processing_time = time.perf_counter() - start_time
    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_path)

    return {
        "mode": mode,
        "k_used": k_used,
        "original_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "compression_ratio": round(original_size / compressed_size, 2) if compressed_size else None,
        "processing_time_seconds": round(processing_time, 3),
    }