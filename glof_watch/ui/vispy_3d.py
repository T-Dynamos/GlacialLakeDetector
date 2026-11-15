"""
glof_watch.ui.vispy_3d
High-Performance 3D Digital Elevation Model (DEM) and Glacial Lake Visualization.

Features:
- High-fidelity 3D DEM surface modeling with VisPy (Mesa OpenGL 4.6).
- Elevation normalization with adjustable vertical exaggeration (e.g., 1.5x - 2.5x).
- Mountain terrain colormapping (Alpine terrain with glaciated snow summits, Viridis, Earth tones).
- Glacial Lake Draping: drapes detected glacial lake mask/polygons in glowing cyan
  (#00FFFF, alpha=0.85) precisely positioned on the 3D surface at the lake's elevation plane.
- Offscreen Framebuffer Rendering: render_3d_terrain_rgba() returning a NumPy uint8 (H, W, 4)
  array ready for direct conversion to Kivy Texture via blit_buffer().
- Standalone 60 FPS Orbit Window: launch_interactive_vispy_window() with TurntableCamera
  (left mouse drag rotate, right mouse drag pan, scroll wheel zoom, hotkeys R/W/L/T/Esc).
"""

import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("QT_API", "pyqt6")

from typing import List, Tuple, Optional, Any, Union, Dict
import multiprocessing
import numpy as np
import cv2
import skimage.measure
from vispy import scene, app
from vispy.scene import visuals
from vispy.color import Colormap, get_colormap
from vispy.visuals.filters import WireframeFilter

# Standard glowing cyan water color: #00FFFF with 85% opacity
CYAN_WATER_COLOR = (0.0, 1.0, 1.0, 0.85)
CYAN_CONTOUR_COLOR = (0.0, 1.0, 1.0, 1.0)

# High-fidelity Alpine Terrain Colormap (lush valley -> rock -> moraine -> snow summits)
ALPINE_TERRAIN_STOPS = [
    "#163820",  # 0.00: Deep glacial valley floor (forest/moss)
    "#265335",  # 0.14: Lower subalpine woodland
    "#4e6834",  # 0.28: Alpine meadow / tundra
    "#826d4c",  # 0.42: Lower talus & rocky slopes
    "#967d62",  # 0.56: Mid-mountain ochre granite
    "#737579",  # 0.70: Rugged moraine scree / basalt
    "#9fa4a9",  # 0.84: Sub-peak cold stone
    "#dce2e6",  # 0.93: Permafrost & firn ice
    "#ffffff",  # 1.00: High glaciated summits & seracs
]

EARTH_TONES_STOPS = [
    "#0d2316",  # Valley evergreen
    "#204b2b",  # Valley flank
    "#4a6132",  # Subalpine vegetation
    "#78593a",  # Brown sandstone
    "#997a5b",  # Moraine sediment
    "#6b7077",  # Cold shale
    "#b0b5ba",  # Frost line
    "#ffffff",  # Summit snow
]

GLACIAL_ICE_STOPS = [
    "#0b1d28",
    "#143c54",
    "#1c6382",
    "#298db5",
    "#4db5d9",
    "#82d5ed",
    "#c4effa",
    "#ffffff",
]

_TERRAIN_CMAP = Colormap(ALPINE_TERRAIN_STOPS)
_EARTH_CMAP = Colormap(EARTH_TONES_STOPS)
_ICE_CMAP = Colormap(GLACIAL_ICE_STOPS)

COLORMAP_PRESETS = {
    "terrain": _TERRAIN_CMAP,
    "alpine": _TERRAIN_CMAP,
    "earth": _EARTH_CMAP,
    "ice": _ICE_CMAP,
    "blues": _ICE_CMAP,
}


def resolve_colormap(cmap_name_or_obj: Union[str, Colormap]) -> Colormap:
    """Resolves a colormap from string name or returns Colormap instance."""
    if isinstance(cmap_name_or_obj, Colormap):
        return cmap_name_or_obj
    name = str(cmap_name_or_obj).lower().strip()
    if name in COLORMAP_PRESETS:
        return COLORMAP_PRESETS[name]
    try:
        return get_colormap(name)
    except Exception:
        return _TERRAIN_CMAP


def sanitize_and_normalize_dem(
    dem_arr: np.ndarray,
    vertical_exaggeration: float = 1.8,
    base_scale: float = 0.35
) -> Tuple[np.ndarray, np.ndarray, float, float, float]:
    """
    Sanitizes raw DEM array (replaces NaNs / NoData values) and normalizes elevations to [0, 1].

    Returns:
        dem_clean: Array with NaNs/nodata replaced by minimum valid elevation.
        dem_norm: Normalized elevations in range [0.0, 1.0].
        z_scaled: Scaled 3D elevation plane z = dem_norm * (base_scale * vertical_exaggeration).
        min_el: Minimum valid elevation in meters.
        max_el: Maximum valid elevation in meters.
    """
    arr = np.asarray(dem_arr, dtype=np.float32)
    valid_mask = np.isfinite(arr) & (arr > -1000.0)

    if not np.any(valid_mask):
        dem_clean = np.zeros_like(arr, dtype=np.float32)
        min_el = 0.0
        max_el = 1.0
    else:
        min_el = float(np.min(arr[valid_mask]))
        max_el = float(np.max(arr[valid_mask]))
        dem_clean = np.where(valid_mask, arr, min_el)

    el_range = max(max_el - min_el, 1e-5)
    dem_norm = np.clip((dem_clean - min_el) / el_range, 0.0, 1.0).astype(np.float32)

    vert_exag = max(0.1, float(vertical_exaggeration))
    z_scaled = dem_norm * (base_scale * vert_exag)

    return dem_clean, dem_norm, z_scaled, min_el, max_el


def compute_aspect_coordinates(
    dem_shape: Tuple[int, int],
    bbox: Optional[List[float]] = None
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """
    Calculates geographic or grid aspect ratio and returns centered x and y coordinate vectors.

    dem_shape: (H, W) where H is rows (lat), W is cols (lon).
    bbox: [min_lon, min_lat, max_lon, max_lat] or None.
    """
    H, W = dem_shape
    if bbox is not None and len(bbox) == 4:
        min_lon, min_lat, max_lon, max_lat = bbox
        mid_lat = (min_lat + max_lat) / 2.0
        cos_factor = np.cos(np.radians(mid_lat))
        dx_meters = max(1e-4, (max_lon - min_lon) * 111320.0 * cos_factor)
        dy_meters = max(1e-4, (max_lat - min_lat) * 111320.0)
        aspect = float(dx_meters / dy_meters)
    else:
        aspect = float(W) / float(max(1, H))

    if aspect >= 1.0:
        aspect_x = 1.0
        aspect_y = float(1.0 / aspect)
    else:
        aspect_x = float(aspect)
        aspect_y = 1.0

    x = np.linspace(-aspect_x, aspect_x, W, dtype=np.float32)
    y = np.linspace(-aspect_y, aspect_y, H, dtype=np.float32)
    return aspect_x, aspect_y, x, y


def generate_lake_water_mesh(
    lake_mask_t: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    z_water_plane: float,
    z_offset: float = 0.003
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Constructs 3D quad mesh vertices and triangular faces covering all lake pixels.
    The water surface is placed flat at the lake's elevation plane (z_water_plane + z_offset).

    lake_mask_t: Lake mask oriented to match (W, H) coordinate layout.
    """
    cols_idx, rows_idx = np.where(lake_mask_t)
    n_pixels = len(cols_idx)
    if n_pixels == 0:
        return None

    dx = float(x[1] - x[0]) if len(x) > 1 else 0.01
    dy = float(y[1] - y[0]) if len(y) > 1 else 0.01

    px = x[cols_idx]
    py = y[rows_idx]

    # 4 corner vertices per pixel quad
    v0 = np.column_stack([px - dx * 0.5, py - dy * 0.5])
    v1 = np.column_stack([px + dx * 0.5, py - dy * 0.5])
    v2 = np.column_stack([px + dx * 0.5, py + dy * 0.5])
    v3 = np.column_stack([px - dx * 0.5, py + dy * 0.5])

    all_verts_2d = np.empty((n_pixels * 4, 2), dtype=np.float32)
    all_verts_2d[0::4] = v0
    all_verts_2d[1::4] = v1
    all_verts_2d[2::4] = v2
    all_verts_2d[3::4] = v3

    zw = np.full((n_pixels * 4, 1), z_water_plane + z_offset, dtype=np.float32)
    vertices_3d = np.hstack([all_verts_2d, zw]).astype(np.float32)

    base_idx = np.arange(0, n_pixels * 4, 4, dtype=np.uint32)[:, None]
    f1 = base_idx + np.array([0, 1, 2], dtype=np.uint32)
    f2 = base_idx + np.array([0, 2, 3], dtype=np.uint32)

    faces = np.empty((n_pixels * 2, 3), dtype=np.uint32)
    faces[0::2] = f1
    faces[1::2] = f2

    return vertices_3d, faces


def extract_lake_contour_lines(
    lake_mask: np.ndarray,
    aspect_x: float,
    aspect_y: float,
    z_contour_plane: float,
    z_offset: float = 0.005
) -> List[np.ndarray]:
    """
    Extracts high-resolution 2D lake contours via marching squares and projects
    them into 3D perimeter loops sitting slightly above the water mesh.
    """
    H, W = lake_mask.shape
    try:
        contours = skimage.measure.find_contours(lake_mask.astype(float), 0.5)
    except Exception:
        return []

    lines_3d = []
    for c in contours:
        if len(c) < 3:
            continue
        # c[:, 0] is row (0 to H-1), c[:, 1] is column (0 to W-1)
        # In 3D: col maps to -aspect_x..+aspect_x, row (flipped) maps to -aspect_y..+aspect_y
        cx_pts = -aspect_x + (c[:, 1] / float(max(1, W - 1))) * (2.0 * aspect_x)
        cy_pts = -aspect_y + ((H - 1.0 - c[:, 0]) / float(max(1, H - 1))) * (2.0 * aspect_y)
        cz_pts = np.full_like(cx_pts, z_contour_plane + z_offset)
        pts_3d = np.column_stack([cx_pts, cy_pts, cz_pts]).astype(np.float32)
        lines_3d.append(pts_3d)

    return lines_3d


def create_3d_terrain_scene(
    dem_arr: np.ndarray,
    lake_mask: Optional[np.ndarray] = None,
    bbox: Optional[List[float]] = None,
    size: Tuple[int, int] = (800, 600),
    elevation: float = 35.0,
    azimuth: float = 45.0,
    vertical_exaggeration: float = 1.8,
    colormap: Union[str, Colormap] = "terrain",
    bgcolor: Any = "#0e1117",
    interactive: bool = False,
    show: bool = False,
    title: str = "GlacialLakeDetector 3D Terrain Explorer",
    satellite_img: Optional[np.ndarray] = None
) -> Tuple[scene.SceneCanvas, scene.ViewBox, Dict[str, Any]]:
    """
    Assembles the VisPy SceneCanvas, 3D terrain surface mesh, draped lake polygon & contours,
    and a TurntableCamera configured for smooth 60 FPS orbit navigation.

    Returns:
        canvas: Configured SceneCanvas.
        view: Central ViewBox.
        scene_elements: Dictionary of created visuals and controls for runtime manipulation.
    """
    dem_clean, dem_norm, z_scaled, min_el, max_el = sanitize_and_normalize_dem(
        dem_arr, vertical_exaggeration=vertical_exaggeration
    )
    H, W = dem_clean.shape
    aspect_x, aspect_y, x, y = compute_aspect_coordinates((H, W), bbox)

    # In geographic rasters: row 0 is North (+y), row H-1 is South (-y)
    # Align to 3D Cartesian space: invert rows so index 0 is South (-aspect_y)
    z_3d = z_scaled[::-1, :].T  # Shape: (W, H)
    dem_norm_t = dem_norm[::-1, :].T

    # Generate terrain coloring: Genuine True-Color Satellite Imagery or Colormap
    has_sat = False
    if satellite_img is not None:
        try:
            sat = np.asarray(satellite_img)
            # If shape is (channels, H, W) e.g. (3, H, W)
            if sat.ndim == 3 and sat.shape[0] in (3, 4) and sat.shape[2] not in (3, 4):
                sat = np.transpose(sat[:3], (1, 2, 0))
            if sat.ndim == 3 and sat.shape[2] >= 3:
                sat_rgb = sat[:, :, :3].astype(np.float32)
                if np.max(sat_rgb) > 1.0:
                    sat_rgb = sat_rgb / 255.0
                sat_res = cv2.resize(sat_rgb, (W, H), interpolation=cv2.INTER_LINEAR)
                sat_res_t = sat_res[::-1, :, :].transpose(1, 0, 2)
                vertex_colors = np.column_stack([
                    sat_res_t.reshape(-1, 3),
                    np.ones((W * H, 1), dtype=np.float32)
                ]).astype(np.float32)
                has_sat = True
        except Exception:
            has_sat = False

    if not has_sat:
        cmap = resolve_colormap(colormap)
        norm_vals = dem_norm_t.ravel()
        vertex_colors = cmap.map(norm_vals).astype(np.float32)

    # Match lake mask dimensions if provided
    has_lake = False
    clean_mask = None
    mask_t = None
    if lake_mask is not None:
        raw_mask = np.asarray(lake_mask)
        if raw_mask.shape != (H, W):
            clean_mask = cv2.resize(
                raw_mask.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST
            ) > 0
        else:
            clean_mask = raw_mask > 0

        has_lake = bool(np.any(clean_mask))
        if has_lake:
            mask_t = clean_mask[::-1, :].T
            # Tint the terrain surface under the lake bed with cyan/deep azure
            # so the depression glows cyan even through water transparency
            lake_indices = np.where(mask_t.ravel())[0]
            if len(lake_indices) > 0:
                cyan_tint = np.array([0.0, 0.85, 0.95, 1.0], dtype=np.float32)
                vertex_colors[lake_indices] = (
                    0.25 * vertex_colors[lake_indices] + 0.75 * cyan_tint
                )

    # Create SceneCanvas
    keys_mode = "interactive" if interactive else None
    canvas = scene.SceneCanvas(
        title=title,
        size=size,
        bgcolor=bgcolor,
        keys=keys_mode,
        show=show,
        vsync=True
    )
    view = canvas.central_widget.add_view()

    # 1. Digital Elevation Model Surface visual
    terrain_surface = visuals.SurfacePlot(x=x, y=y, z=z_3d, shading="smooth")
    terrain_surface.set_data(colors=vertex_colors)
    view.add(terrain_surface)

    # Attach wireframe filter (toggled with 'W' key)
    wireframe_filter = WireframeFilter(width=1.0, color="#ffffff")
    terrain_surface.attach(wireframe_filter)
    wireframe_filter.enabled = False

    # 2. Glacial Lake Draping: Water polygon mesh & shoreline contours
    water_mesh = None
    contour_lines = []
    lake_elev_meters = 0.0
    lake_elev_norm = 0.0

    if has_lake and clean_mask is not None and mask_t is not None:
        lake_elev_meters = float(np.median(dem_clean[clean_mask]))
        el_range = max(max_el - min_el, 1e-5)
        vert_exag = max(0.1, float(vertical_exaggeration))
        lake_elev_norm = float(np.clip((lake_elev_meters - min_el) / el_range, 0.0, 1.0) * (0.35 * vert_exag))

        # Draped cyan water polygon mesh
        mesh_data = generate_lake_water_mesh(
            mask_t, x, y, z_water_plane=lake_elev_norm, z_offset=0.003
        )
        if mesh_data is not None:
            w_verts, w_faces = mesh_data
            water_mesh = visuals.Mesh(
                vertices=w_verts,
                faces=w_faces,
                color=CYAN_WATER_COLOR
            )
            view.add(water_mesh)

        # Crisp glowing cyan shoreline contour line loops
        c_lines = extract_lake_contour_lines(
            clean_mask, aspect_x, aspect_y, z_contour_plane=lake_elev_norm, z_offset=0.005
        )
        for line_pts in c_lines:
            line_visual = visuals.Line(
                pos=line_pts,
                color=CYAN_CONTOUR_COLOR,
                width=3.0,
                method="gl"
            )
            view.add(line_visual)
            contour_lines.append(line_visual)

    # 3. TurntableCamera Orbit Navigation
    z_span = float(0.35 * max(0.1, float(vertical_exaggeration)))
    center = (0.0, 0.0, z_span * 0.5)
    bounding_radius = float(np.sqrt(aspect_x**2 + aspect_y**2 + (z_span * 0.5)**2))
    camera_distance = max(1.5, bounding_radius * 2.15)
    initial_fov = 32.0

    camera = scene.cameras.TurntableCamera(
        elevation=float(elevation),
        azimuth=float(azimuth),
        center=center,
        distance=camera_distance,
        fov=initial_fov
    )
    view.camera = camera

    scene_elements = {
        "terrain_surface": terrain_surface,
        "water_mesh": water_mesh,
        "contour_lines": contour_lines,
        "wireframe_filter": wireframe_filter,
        "camera": camera,
        "initial_elevation": float(elevation),
        "initial_azimuth": float(azimuth),
        "initial_center": center,
        "initial_distance": camera_distance,
        "dem_norm_t": dem_norm_t,
        "current_cmap": colormap if isinstance(colormap, str) else "terrain",
        "lake_elev_meters": lake_elev_meters,
        "has_lake": has_lake,
    }

    if interactive:
        _bind_interactive_hotkeys(canvas, scene_elements)

    return canvas, view, scene_elements


def _bind_interactive_hotkeys(canvas: scene.SceneCanvas, elements: Dict[str, Any]) -> None:
    """Binds keyboard shortcuts for interactive 3D exploration."""
    cmaps_list = ["terrain", "earth", "viridis", "ice"]

    @canvas.events.key_press.connect
    def on_key_press(event: Any) -> None:
        key = getattr(event, "key", None)
        if not key:
            return
        key_str = str(key.name if hasattr(key, "name") else key).upper()

        if key_str in ("ESCAPE", "Q"):
            canvas.close()
            try:
                app.quit()
            except Exception:
                pass

        elif key_str == "R":
            # Reset camera to default elevation, azimuth, and orbit center
            elements["camera"].elevation = elements["initial_elevation"]
            elements["camera"].azimuth = elements["initial_azimuth"]
            elements["camera"].center = elements["initial_center"]
            elements["camera"].distance = elements["initial_distance"]
            canvas.update()

        elif key_str == "W":
            # Toggle wireframe mesh overlay
            wf = elements.get("wireframe_filter")
            if wf is not None:
                wf.enabled = not wf.enabled
                canvas.update()

        elif key_str == "L":
            # Toggle glacial lake water surface and contour visibility
            wm = elements.get("water_mesh")
            lines = elements.get("contour_lines", [])
            if wm is not None:
                wm.visible = not wm.visible
            for line in lines:
                line.visible = not line.visible
            canvas.update()

        elif key_str == "T":
            # Cycle through scientific colormaps
            cur = elements.get("current_cmap", "terrain")
            next_idx = (cmaps_list.index(cur) + 1) % len(cmaps_list) if cur in cmaps_list else 0
            new_cmap_name = cmaps_list[next_idx]
            elements["current_cmap"] = new_cmap_name
            new_cmap = resolve_colormap(new_cmap_name)
            dem_norm_t = elements["dem_norm_t"]
            new_cols = new_cmap.map(dem_norm_t.ravel()).astype(np.float32)
            elements["terrain_surface"].set_data(colors=new_cols)
            canvas.update()


def _render_3d_terrain_direct(
    dem_arr: np.ndarray,
    lake_mask: Optional[np.ndarray],
    bbox: Optional[List[float]],
    size: Tuple[int, int],
    elevation: float,
    azimuth: float,
    vertical_exaggeration: float,
    colormap: Union[str, Colormap],
    bgcolor: Any,
    satellite_img: Optional[np.ndarray] = None
) -> np.ndarray:
    """Direct in-process offscreen framebuffer rendering."""
    canvas = None
    try:
        canvas, _, _ = create_3d_terrain_scene(
            dem_arr=dem_arr,
            lake_mask=lake_mask,
            bbox=bbox,
            size=size,
            elevation=elevation,
            azimuth=azimuth,
            vertical_exaggeration=vertical_exaggeration,
            colormap=colormap,
            bgcolor=bgcolor,
            interactive=False,
            show=False,
            satellite_img=satellite_img
        )
        rgba_img = canvas.render()
        return np.ascontiguousarray(rgba_img, dtype=np.uint8)
    finally:
        if canvas is not None:
            try:
                canvas.close()
            except Exception:
                pass


def _isolated_render_worker(
    pipe_conn: Any,
    dem_arr: np.ndarray,
    lake_mask: Optional[np.ndarray],
    bbox: Optional[List[float]],
    size: Tuple[int, int],
    elevation: float,
    azimuth: float,
    vertical_exaggeration: float,
    colormap: str,
    bgcolor: Any,
    satellite_img: Optional[np.ndarray] = None
) -> None:
    """Worker process for completely isolated 3D offscreen rendering without Kivy GL context sharing."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_API", "pyqt6")
    try:
        rgba = _render_3d_terrain_direct(
            dem_arr=dem_arr,
            lake_mask=lake_mask,
            bbox=bbox,
            size=size,
            elevation=elevation,
            azimuth=azimuth,
            vertical_exaggeration=vertical_exaggeration,
            colormap=colormap,
            bgcolor=bgcolor,
            satellite_img=satellite_img
        )
        pipe_conn.send(rgba)
    except Exception as exc:
        pipe_conn.send(exc)
    finally:
        try:
            pipe_conn.close()
        except Exception:
            pass


def render_3d_terrain_rgba(
    dem_arr: Optional[np.ndarray] = None,
    lake_mask: Optional[np.ndarray] = None,
    bbox: Optional[List[float]] = None,
    size: Tuple[int, int] = (800, 600),
    elevation: float = 35.0,
    azimuth: float = 45.0,
    vertical_exaggeration: float = 1.8,
    colormap: Union[str, Colormap] = "terrain",
    bgcolor: Any = "#0e1117",
    width: Optional[int] = None,
    height: Optional[int] = None,
    dem: Optional[np.ndarray] = None,
    satellite_img: Optional[np.ndarray] = None,
    isolated: bool = True,
    **kwargs: Any
) -> np.ndarray:
    """
    Renders the 3D DEM terrain and draped glacial lake offscreen into a NumPy uint8 (H, W, 4)
    RGBA framebuffer array.

    Seamlessly compatible with Kivy Texture blit_buffer:
    >>> rgba = render_3d_terrain_rgba(dem_arr, lake_mask, width=800, height=600)
    >>> h, w = rgba.shape[:2]
    >>> tex = Texture.create(size=(w, h), colorfmt='rgba')
    >>> tex.blit_buffer(np.ascontiguousarray(np.flipud(rgba)).tobytes(), colorfmt='rgba', bufferfmt='ubyte')

    Parameters:
        dem_arr: 2D numpy array of elevation values in meters. Also accepts 'dem=' keyword.
        lake_mask: Optional 2D binary/boolean array indicating detected lake pixels.
        bbox: Optional [min_lon, min_lat, max_lon, max_lat] bounding box.
        size: (width, height) tuple for canvas dimensions.
        elevation: Initial TurntableCamera elevation angle in degrees (default: 35.0).
        azimuth: Initial TurntableCamera azimuth angle in degrees (default: 45.0).
        vertical_exaggeration: Terrain vertical exaggeration multiplier (default: 1.8x).
        colormap: Terrain colormap ('terrain', 'earth', 'viridis', 'ice', or Colormap).
        bgcolor: Background color (default '#0e1117').
        width: Optional override for width.
        height: Optional override for height.
        isolated: When True (default), renders in an isolated subprocess to protect Kivy's GL context.

    Returns:
        NumPy uint8 array of shape (H, W, 4) with RGBA channels.
    """
    if dem_arr is None:
        dem_arr = dem
    if dem_arr is None:
        raise ValueError("dem_arr must be provided as an input array")

    w = int(width) if width is not None else int(size[0])
    h = int(height) if height is not None else int(size[1])
    target_size = (w, h)
    sat_img = kwargs.get("satellite_img", satellite_img)

    if isolated:
        try:
            ctx = multiprocessing.get_context("spawn")
            parent_conn, child_conn = ctx.Pipe()
            p = ctx.Process(
                target=_isolated_render_worker,
                args=(
                    child_conn,
                    dem_arr,
                    lake_mask,
                    bbox,
                    target_size,
                    elevation,
                    azimuth,
                    vertical_exaggeration,
                    colormap if isinstance(colormap, str) else "terrain",
                    bgcolor,
                    sat_img
                ),
                daemon=True
            )
            p.start()
            if parent_conn.poll(10.0):
                res = parent_conn.recv()
                p.join(timeout=2.0)
                if not isinstance(res, Exception):
                    return res
            p.terminate()
            p.join(timeout=1.0)
        except Exception:
            pass

    # Direct fallback if isolated is False or failed
    return _render_3d_terrain_direct(
        dem_arr=dem_arr,
        lake_mask=lake_mask,
        bbox=bbox,
        size=target_size,
        elevation=elevation,
        azimuth=azimuth,
        vertical_exaggeration=vertical_exaggeration,
        colormap=colormap,
        bgcolor=bgcolor,
        satellite_img=sat_img
    )


def _standalone_window_process_worker(
    dem_arr: np.ndarray,
    lake_mask: Optional[np.ndarray],
    bbox: Optional[List[float]],
    title: str,
    size: Tuple[int, int],
    elevation: float,
    azimuth: float,
    vertical_exaggeration: float,
    colormap: str,
    bgcolor: Any,
    satellite_img: Optional[np.ndarray] = None
) -> None:
    """Worker process entrypoint for isolated multi-process 3D window."""
    import os
    if "QT_QPA_PLATFORM" not in os.environ:
        if os.environ.get("XDG_SESSION_TYPE") == "wayland" or "WAYLAND_DISPLAY" in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ.setdefault("QT_API", "pyqt6")

    try:
        from vispy import app
        app.use_app("pyqt6")
        canvas, _, _ = create_3d_terrain_scene(
            dem_arr=dem_arr,
            lake_mask=lake_mask,
            bbox=bbox,
            size=size,
            elevation=elevation,
            azimuth=azimuth,
            vertical_exaggeration=vertical_exaggeration,
            colormap=colormap,
            bgcolor=bgcolor,
            interactive=True,
            show=True,
            title=title,
            satellite_img=satellite_img
        )
        if hasattr(canvas, "native") and canvas.native is not None:
            try:
                canvas.native.show()
                canvas.native.raise_()
                canvas.native.activateWindow()
            except Exception:
                pass
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"[vispy_3d] Error in standalone 3D window: {e}")


def launch_interactive_vispy_window(
    dem_arr: Optional[np.ndarray] = None,
    lake_mask: Optional[np.ndarray] = None,
    bbox: Optional[List[float]] = None,
    title: str = "GlacialLakeDetector 3D Terrain Explorer",
    size: Tuple[int, int] = (1280, 720),
    elevation: float = 35.0,
    azimuth: float = 45.0,
    vertical_exaggeration: float = 1.8,
    colormap: Union[str, Colormap] = "terrain",
    bgcolor: Any = "#0b0f19",
    block: bool = True,
    run_in_background: Optional[bool] = None,
    dem: Optional[np.ndarray] = None,
    satellite_img: Optional[np.ndarray] = None,
    **kwargs: Any
) -> Any:
    """
    Opens an independent VisPy 60 FPS OpenGL orbit window with TurntableCamera controls:
    - Left mouse drag: Rotate terrain orbit
    - Right mouse drag: Pan view center
    - Mouse scroll wheel: Zoom in/out
    - Key 'R': Reset camera orientation
    - Key 'W': Toggle wireframe overlay
    - Key 'L': Toggle glacial lake draping
    - Key 'T': Cycle colormaps
    - Key 'Escape' / 'Q': Close window

    Parameters:
        dem_arr: Elevation grid in meters.
        lake_mask: Glacial lake detection binary mask.
        bbox: [min_lon, min_lat, max_lon, max_lat] geographic extent.
        title: Window caption.
        size: Initial window dimensions (width, height).
        block: Whether to block caller execution with app.run() or return canvas.
        run_in_background: If True, launches the window in an isolated background process.

    Returns:
        canvas instance if block=False and in-process, or multiprocessing.Process if run_in_background=True.
    """
    if dem_arr is None:
        dem_arr = dem
    if dem_arr is None:
        raise ValueError("dem_arr must be provided")

    cmap_name = colormap if isinstance(colormap, str) else "terrain"

    # Automatically enforce process isolation if Kivy or foreign GL context is present
    is_kivy_active = "kivy" in sys.modules or "kivy.core.window" in sys.modules
    if run_in_background is None:
        run_in_background = is_kivy_active or bool(block is False)

    if run_in_background or is_kivy_active:
        ctx = multiprocessing.get_context("spawn")
        p = ctx.Process(
            target=_standalone_window_process_worker,
            args=(
                dem_arr,
                lake_mask,
                bbox,
                title,
                size,
                elevation,
                azimuth,
                vertical_exaggeration,
                cmap_name,
                bgcolor,
                satellite_img
            ),
            daemon=False
        )
        p.start()
        return p

    canvas, _, _ = create_3d_terrain_scene(
        dem_arr=dem_arr,
        lake_mask=lake_mask,
        bbox=bbox,
        size=size,
        elevation=elevation,
        azimuth=azimuth,
        vertical_exaggeration=vertical_exaggeration,
        colormap=colormap,
        bgcolor=bgcolor,
        interactive=True,
        show=True,
        title=title,
        satellite_img=satellite_img
    )

    if block:
        app.run()
        return None
    return canvas
