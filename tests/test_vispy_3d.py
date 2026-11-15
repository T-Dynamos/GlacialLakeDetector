"""
tests/test_vispy_3d.py
Unit and integration tests for VisPy 3D Elevation and Scientific Visualization module.
Validates offscreen framebuffer rendering with both synthetic DEM grids and real target GeoTIFFs.
"""

import os
import time
from typing import Tuple
import pytest
import numpy as np
import rasterio

from glof_watch.ui.vispy_3d import (
    render_3d_terrain_rgba,
    launch_interactive_vispy_window,
    sanitize_and_normalize_dem,
    compute_aspect_coordinates,
    generate_lake_water_mesh,
    extract_lake_contour_lines,
    resolve_colormap
)

REAL_GYA_DEM_PATH = "/run/media/tdynamos/Secondary/DATA/GLACIAL_LAKE/targets_cache/gya/dem.tif"
REAL_GYA_BBOX = [77.595, 33.605, 77.635, 33.635]


def create_synthetic_dem(
    shape: Tuple[int, int] = (60, 80),
    with_lake_basin: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """Generates synthetic mountain terrain with an optional central lake depression."""
    H, W = shape
    y = np.linspace(-1.0, 1.0, H, dtype=np.float32)
    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)
    X, Y = np.meshgrid(x, y)

    # Base mountain relief
    dem = 4500.0 + (np.sin(X * 2.5) * np.cos(Y * 2.5) + 1.0) * 600.0

    # Lake depression
    dist = np.sqrt(X**2 + Y**2)
    lake_mask = dist < 0.28
    if with_lake_basin:
        # Carve depression
        dem[lake_mask] = 4800.0 - (0.28 - dist[lake_mask]) * 300.0

    return dem.astype(np.float32), lake_mask


def test_sanitize_and_normalize_dem():
    """Validates elevation sanitization, nodata filtering, and normalization to [0, 1]."""
    raw = np.array([
        [-32768.0, 5000.0, np.nan],
        [4000.0, 6000.0, np.inf]
    ], dtype=np.float32)

    dem_clean, dem_norm, z_scaled, min_el, max_el = sanitize_and_normalize_dem(
        raw, vertical_exaggeration=1.8, base_scale=0.35
    )

    assert min_el == pytest.approx(4000.0)
    assert max_el == pytest.approx(6000.0)
    assert np.all(np.isfinite(dem_clean))
    assert np.all(dem_norm >= 0.0)
    assert np.all(dem_norm <= 1.0)
    assert dem_norm[0, 1] == pytest.approx(0.5)  # 5000 is mid-range between 4000 and 6000
    assert np.all(z_scaled >= 0.0)
    assert np.all(z_scaled <= 0.35 * 1.8 + 1e-5)


def test_compute_aspect_coordinates():
    """Validates aspect ratio calculations with and without geographic bounding box."""
    # Aspect from grid dimensions
    ax, ay, x, y = compute_aspect_coordinates((60, 120), bbox=None)
    assert ax == pytest.approx(1.0)
    assert ay == pytest.approx(0.5)
    assert len(x) == 120
    assert len(y) == 60

    # Aspect from geographic bounding box
    ax2, ay2, x2, y2 = compute_aspect_coordinates((108, 144), bbox=REAL_GYA_BBOX)
    assert ax2 > 0.0
    assert ay2 > 0.0
    assert len(x2) == 144
    assert len(y2) == 108


def test_generate_lake_water_mesh_and_contours():
    """Validates generation of 3D lake water quad mesh and contour line loops."""
    H, W = 40, 50
    mask = np.zeros((H, W), dtype=bool)
    mask[15:25, 20:30] = True

    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)
    y = np.linspace(-0.8, 0.8, H, dtype=np.float32)
    mask_t = mask[::-1, :].T

    mesh_data = generate_lake_water_mesh(mask_t, x, y, z_water_plane=0.15)
    assert mesh_data is not None
    w_verts, w_faces = mesh_data
    assert w_verts.shape[1] == 3
    assert w_faces.shape[1] == 3
    assert len(w_verts) == 100 * 4  # 10x10 lake pixels -> 100 pixels * 4 verts
    assert len(w_faces) == 100 * 2  # 100 quads * 2 triangles

    # Contour lines
    c_lines = extract_lake_contour_lines(mask, aspect_x=1.0, aspect_y=0.8, z_contour_plane=0.15)
    assert len(c_lines) >= 1
    assert c_lines[0].shape[1] == 3


def test_render_3d_terrain_synthetic_no_lake():
    """Validates offscreen framebuffer rendering on synthetic DEM with no lake."""
    dem, _ = create_synthetic_dem(shape=(50, 70), with_lake_basin=False)
    target_size = (400, 300)  # width=400, height=300

    rgba = render_3d_terrain_rgba(
        dem_arr=dem,
        lake_mask=None,
        size=target_size,
        elevation=35.0,
        azimuth=45.0,
        vertical_exaggeration=1.8,
        colormap="terrain"
    )

    # Framebuffer shape is (height, width, 4)
    assert isinstance(rgba, np.ndarray)
    assert rgba.dtype == np.uint8
    assert rgba.shape == (300, 400, 4)

    # Ensure scene contains non-background rendered terrain
    bg_color = np.array([14, 17, 23], dtype=np.uint8)
    diff = np.abs(rgba[:, :, :3].astype(int) - bg_color)
    non_bg_pixels = np.count_nonzero(np.any(diff > 5, axis=-1))
    assert non_bg_pixels > 10000


def test_render_3d_terrain_synthetic_with_lake():
    """Validates that draped lake polygon & contours produce vibrant cyan pixels in render."""
    dem, lake_mask = create_synthetic_dem(shape=(60, 80), with_lake_basin=True)
    target_size = (600, 450)

    rgba = render_3d_terrain_rgba(
        dem_arr=dem,
        lake_mask=lake_mask,
        size=target_size,
        elevation=35.0,
        azimuth=45.0,
        vertical_exaggeration=2.0,
        colormap="terrain"
    )

    assert rgba.shape == (450, 600, 4)
    assert rgba.dtype == np.uint8

    # Check for glowing cyan pixels (#00FFFF): high G and B channels, lower R channel
    is_cyan = (rgba[:, :, 0] < 80) & (rgba[:, :, 1] > 180) & (rgba[:, :, 2] > 180)
    cyan_count = np.count_nonzero(is_cyan)
    assert cyan_count > 100


@pytest.mark.skipif(not os.path.exists(REAL_GYA_DEM_PATH), reason="Target Gya DEM cache not found")
def test_render_3d_real_gya_dem():
    """Validates 3D rendering using genuine Copernicus 30m DEM from targets_cache."""
    with rasterio.open(REAL_GYA_DEM_PATH) as src:
        dem_gya = src.read(1).astype(np.float32)

    assert dem_gya.shape == (108, 144)
    assert np.any(dem_gya > 5000.0)

    rgba = render_3d_terrain_rgba(
        dem_arr=dem_gya,
        lake_mask=None,
        bbox=REAL_GYA_BBOX,
        size=(800, 600),
        elevation=35.0,
        azimuth=45.0,
        vertical_exaggeration=1.8,
        colormap="terrain"
    )

    assert rgba.shape == (600, 800, 4)
    assert rgba.dtype == np.uint8

    # Validate that terrain occupies a significant portion of the rendered frame
    bg_color = np.array([14, 17, 23], dtype=np.uint8)
    diff = np.abs(rgba[:, :, :3].astype(int) - bg_color)
    non_bg_count = np.count_nonzero(np.any(diff > 5, axis=-1))
    assert non_bg_count > 50000


@pytest.mark.skipif(not os.path.exists(REAL_GYA_DEM_PATH), reason="Target Gya DEM cache not found")
def test_render_3d_real_gya_with_lake_draping():
    """Validates lake draping on real Gya DEM with detected / synthetic lake mask."""
    with rasterio.open(REAL_GYA_DEM_PATH) as src:
        dem_gya = src.read(1).astype(np.float32)

    # Synthetic lake mask in center of Gya DEM
    H, W = dem_gya.shape
    cy, cx = H // 2, W // 2
    Y, X = np.ogrid[:H, :W]
    lake_mask = ((Y - cy)**2 + (X - cx)**2) <= 12**2

    rgba = render_3d_terrain_rgba(
        dem_arr=dem_gya,
        lake_mask=lake_mask,
        bbox=REAL_GYA_BBOX,
        size=(800, 600),
        elevation=35.0,
        azimuth=45.0,
        vertical_exaggeration=1.8,
        colormap="terrain"
    )

    assert rgba.shape == (600, 800, 4)

    # Detect glowing cyan lake water
    is_cyan = (rgba[:, :, 0] < 80) & (rgba[:, :, 1] > 180) & (rgba[:, :, 2] > 180)
    assert np.count_nonzero(is_cyan) > 200


def test_colormaps_and_vertical_exaggeration():
    """Validates different terrain colormaps and vertical exaggeration values."""
    dem, _ = create_synthetic_dem(shape=(30, 40))

    for cmap in ["terrain", "earth", "viridis", "ice"]:
        for exag in [1.2, 1.8, 2.5]:
            rgba = render_3d_terrain_rgba(
                dem_arr=dem,
                size=(320, 240),
                vertical_exaggeration=exag,
                colormap=cmap
            )
            assert rgba.shape == (240, 320, 4)
            assert rgba.dtype == np.uint8


def test_analysis_screen_api_compatibility():
    """
    Validates parameter compatibility with AnalysisScreen calls:
    render_3d_terrain_rgba(self.dem_arr, self.lake_mask, width=800, height=600)
    and Texture blit buffer flip: np.ascontiguousarray(np.flipud(rgba)).
    """
    dem, mask = create_synthetic_dem(shape=(40, 50))

    rgba = render_3d_terrain_rgba(
        dem_arr=dem,
        lake_mask=mask,
        width=800,
        height=600
    )
    assert rgba.shape == (600, 800, 4)

    flipped = np.ascontiguousarray(np.flipud(rgba))
    assert flipped.shape == (600, 800, 4)
    buffer_bytes = flipped.tobytes()
    assert len(buffer_bytes) == 600 * 800 * 4

    # Test 'dem=' keyword compatibility
    rgba_kw = render_3d_terrain_rgba(
        dem=dem,
        lake_mask=mask,
        width=400,
        height=300
    )
    assert rgba_kw.shape == (300, 400, 4)


def test_robustness_edge_cases():
    """Validates robustness against nodata DEM, mismatched mask shapes, and flat surfaces."""
    # 1. Flat DEM
    flat_dem = np.full((30, 30), 4500.0, dtype=np.float32)
    rgba_flat = render_3d_terrain_rgba(dem_arr=flat_dem, size=(200, 200))
    assert rgba_flat.shape == (200, 200, 4)

    # 2. All NaNs
    nan_dem = np.full((20, 20), np.nan, dtype=np.float32)
    rgba_nan = render_3d_terrain_rgba(dem_arr=nan_dem, size=(200, 200))
    assert rgba_nan.shape == (200, 200, 4)

    # 3. Mismatched lake mask shape (auto-resized via cv2.resize)
    dem = np.zeros((40, 60), dtype=np.float32)
    mismatched_mask = np.ones((80, 100), dtype=bool)
    rgba_mismatch = render_3d_terrain_rgba(
        dem_arr=dem,
        lake_mask=mismatched_mask,
        size=(200, 200)
    )
    assert rgba_mismatch.shape == (200, 200, 4)

    # 4. Missing dem raises ValueError
    with pytest.raises(ValueError):
        render_3d_terrain_rgba(dem_arr=None)


def test_launch_interactive_vispy_window_non_blocking():
    """Validates launching standalone VisPy window in non-blocking test mode."""
    dem, mask = create_synthetic_dem(shape=(30, 40))

    canvas = launch_interactive_vispy_window(
        dem_arr=dem,
        lake_mask=mask,
        size=(640, 480),
        block=False
    )

    try:
        assert canvas is not None
        assert canvas.size == (640, 480)
        assert hasattr(canvas, "central_widget")
    finally:
        canvas.close()


def test_launch_interactive_vispy_window_background_process():
    """Validates launching standalone VisPy 3D window in isolated background process."""
    dem, mask = create_synthetic_dem(shape=(30, 40))

    proc = launch_interactive_vispy_window(
        dem_arr=dem,
        lake_mask=mask,
        size=(640, 480),
        title="GlacialLakeDetector Isolated 3D Test",
        run_in_background=True
    )
    try:
        assert proc is not None
        assert proc.pid is not None
        time.sleep(1.0)
        assert proc.is_alive()
    finally:
        proc.terminate()
        proc.join(timeout=2.0)
