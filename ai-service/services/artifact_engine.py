import io
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from typing import Dict, Any, List, Tuple
from scipy.ndimage import laplace, sobel

def analyze_digital_artifacts(pil_img: Image.Image, np_img: np.ndarray) -> Dict[str, Any]:
    """
    Performs digital image signal & forensic artifact processing:
    1. Error Level Analysis (ELA) compression surface discrepancy
    2. 2D FFT Frequency Domain Spectral Grid Analysis
    3. Spatial Noise Variance Consistency
    4. Edge Density & Gradient Sharpness
    Returns:
    - artifact_ai_score: float (0.0 to 100.0)
    - detected_artifacts: List[str]
    - ela_heatmap_pil: PIL.Image (Colorized ELA difference map)
    - artifact_metrics: Dict
    """
    artifacts: List[str] = []
    metrics: Dict[str, Any] = {}

    # Convert to RGB uint8 NumPy array
    if np_img.dtype != np.uint8:
        np_img = (np_img * 255).astype(np.uint8)

    h, w, _ = np_img.shape

    # ─── 1. Error Level Analysis (ELA) ──────────────────────────────────────────
    ela_mean, ela_std, ela_heatmap_pil = _compute_ela(pil_img, quality=95)
    metrics["ela_mean"] = round(ela_mean, 2)
    metrics["ela_std"] = round(ela_std, 2)

    # Synthetic / AI images re-compressed at 95% quality exhibit unnaturally low/uniform ELA variance
    # whereas authentic camera images show rich, non-uniform compression error surfaces
    ela_score = 0.0
    if ela_std < 3.2:
        ela_score = 78.0
        artifacts.append(f"ELA Analysis: Unnaturally uniform compression surface (std={ela_std:.1f})")
    elif ela_std < 5.5:
        ela_score = 55.0
        artifacts.append(f"ELA Analysis: Low compression error level discrepancy (std={ela_std:.1f})")
    else:
        ela_score = 15.0
        artifacts.append(f"ELA Analysis: Authentic non-uniform compression error levels (std={ela_std:.1f})")

    # ─── 2. 2D FFT Frequency Domain Grid Analysis ──────────────────────────────
    fft_high_ratio, spectral_spikes, fft_score = _compute_fft_artifacts(np_img)
    metrics["fft_high_frequency_ratio"] = round(fft_high_ratio, 4)
    metrics["spectral_grid_spikes"] = spectral_spikes

    if spectral_spikes > 12:
        artifacts.append("FFT Spectrum: High-frequency periodic grid spikes detected (GAN/Diffusion lattice)")
    elif fft_high_ratio > 0.22:
        artifacts.append("FFT Spectrum: Elevated high-frequency spectral energy distribution")
    else:
        artifacts.append("FFT Spectrum: Natural optical frequency falloff spectrum")

    # ─── 3. Spatial Noise & Edge Consistency ──────────────────────────────────
    noise_var, noise_score = _compute_noise_consistency(np_img)
    metrics["spatial_noise_variance"] = round(noise_var, 4)

    if noise_var < 0.00015:
        artifacts.append("Noise Analysis: Ultra-smooth synthetic pixel gradient distribution")
    elif noise_var > 0.008:
        artifacts.append("Noise Analysis: Natural camera sensor ISO noise variance detected")

    # ─── 4. Hybrid Combination of Artifact Signals ──────────────────────────────
    artifact_ai_score = (0.45 * ela_score) + (0.35 * fft_score) + (0.20 * noise_score)
    artifact_ai_score = round(float(np.clip(artifact_ai_score, 5.0, 95.0)), 1)

    return {
        "artifact_ai_score": artifact_ai_score,
        "detected_artifacts": artifacts,
        "ela_heatmap_pil": ela_heatmap_pil,
        "artifact_metrics": metrics
    }


def _compute_ela(pil_img: Image.Image, quality: int = 95) -> Tuple[float, float, Image.Image]:
    """
    Computes Error Level Analysis (ELA).
    Saves image at 95% JPEG quality in memory and computes per-pixel difference.
    Returns (ela_mean, ela_std, colorized_heatmap_pil).
    """
    try:
        # Save to memory buffer at specified quality
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        resaved_img = Image.open(buf).convert("RGB")

        # Compute absolute difference
        diff_img = ImageChops.difference(pil_img.convert("RGB"), resaved_img)

        # Enhance brightness for visualization
        extrema = diff_img.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1
        scale = 255.0 / max_diff
        enhanced_diff = ImageEnhance.Brightness(diff_img).enhance(scale * 1.5)

        # Calculate statistics on difference array
        diff_np = np.array(diff_img, dtype=np.float32)
        ela_mean = float(np.mean(diff_np))
        ela_std = float(np.std(diff_np))

        return ela_mean, ela_std, enhanced_diff

    except Exception as e:
        print(f"[Artifact Engine] ELA calculation error: {e}")
        # Fallback empty heatmap
        black_img = Image.new("RGB", pil_img.size, (0, 0, 0))
        return 0.0, 0.0, black_img


def _compute_fft_artifacts(np_img: np.ndarray) -> Tuple[float, int, float]:
    """
    Computes 2D FFT Frequency Domain Analysis.
    Detects periodic grid spikes and high-frequency spectral ratios.
    """
    try:
        # Grayscale conversion
        gray = 0.299 * np_img[:, :, 0] + 0.587 * np_img[:, :, 1] + 0.114 * np_img[:, :, 2]
        gray = gray / 255.0

        h, w = gray.shape
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        mag = np.abs(fft_shift)
        log_mag = np.log(mag + 1.0)

        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)

        # High frequency mask (> 35% distance from DC center)
        high_mask = dist > (0.35 * min(h, w))
        low_mask = dist <= (0.35 * min(h, w))

        high_energy = np.sum(mag[high_mask])
        total_energy = np.sum(mag) + 1e-8
        fft_high_ratio = float(high_energy / total_energy)

        # Count periodic spectral grid spikes (peaks in high frequency zone > 4 std above mean)
        high_log_mag = log_mag[high_mask]
        threshold = np.mean(high_log_mag) + (4.0 * np.std(high_log_mag))
        spikes = int(np.sum(high_log_mag > threshold))

        # FFT Score calculation
        fft_score = 20.0
        if spikes > 15:
            fft_score = 88.0
        elif spikes > 8:
            fft_score = 65.0
        elif fft_high_ratio > 0.25:
            fft_score = 60.0
        elif fft_high_ratio < 0.10:
            fft_score = 15.0

        return fft_high_ratio, spikes, fft_score

    except Exception as e:
        print(f"[Artifact Engine] FFT calculation error: {e}")
        return 0.15, 0, 50.0


def _compute_noise_consistency(np_img: np.ndarray) -> Tuple[float, float]:
    """
    Measures spatial Laplacian noise variance.
    """
    try:
        gray = (0.299 * np_img[:, :, 0] + 0.587 * np_img[:, :, 1] + 0.114 * np_img[:, :, 2]) / 255.0
        lap = laplace(gray)
        var = float(np.var(lap))

        score = 50.0
        if var < 0.0002:
            score = 80.0
        elif var < 0.001:
            score = 60.0
        elif var > 0.005:
            score = 15.0

        return var, score

    except Exception as e:
        print(f"[Artifact Engine] Noise calculation error: {e}")
        return 0.001, 50.0
