"""
glof_watch.ui.theme
Centralized Theme Palette and Button Styling Utilities for GLOF-Watch.
Provides high-contrast, professional radar-cockpit styling with guaranteed
legibility across active, inactive, and action button states.
"""

from typing import Optional, Union
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout

# ==============================================================================
# Palette Constants (W3C AAA / WCAG High Contrast Dark Theme)
# ==============================================================================

# Window & Header Backgrounds
COLOR_WINDOW_BG = [0.04, 0.06, 0.08, 1.0]          # Pure cockpit dark slate
COLOR_HEADER_BG = [0.06, 0.09, 0.12, 1.0]          # Raised header bar

# Card Containers
COLOR_CARD_BG = [0.07, 0.10, 0.14, 0.95]            # Sleek card container
COLOR_CARD_BORDER = [0.18, 0.26, 0.34, 1.0]        # Crisp slate card border

# Text & Icon Typography Colors
COLOR_TEXT_PRIMARY = [1.0, 1.0, 1.0, 1.0]          # Crisp pure white
COLOR_TEXT_CYAN = [0.0, 0.90, 1.0, 1.0]            # Glowing electric cyan
COLOR_TEXT_SECONDARY = [0.82, 0.88, 0.94, 1.0]      # High-legibility silver-white
COLOR_TEXT_MUTED = [0.65, 0.75, 0.82, 1.0]          # Readable slate-silver (never dark/black)

# Hazard Badges
COLOR_HAZARD_HIGH = [1.0, 0.35, 0.35, 1.0]         # High Alert coral red
COLOR_HAZARD_MOD = [1.0, 0.78, 0.22, 1.0]          # Moderate hazard amber
COLOR_HAZARD_LOW = [0.20, 0.90, 0.45, 1.0]         # Stable emerald green

# Active / Selected Button States (Deep luminous teal background with crisp white text)
COLOR_ACTIVE_BG = [0.0, 0.48, 0.58, 1.0]            # Deep vibrant cyan-teal #007a94
COLOR_ACTIVE_FG = [1.0, 1.0, 1.0, 1.0]              # Crisp pure white
COLOR_ACTIVE_ICON = [1.0, 1.0, 1.0, 1.0]            # Pure white
COLOR_ACTIVE_BORDER = [0.0, 0.90, 1.0, 0.85]        # Electric cyan glowing outline

# Inactive / Unselected Button States (Dark slate container with bright readable silver text)
COLOR_INACTIVE_BG = [0.10, 0.14, 0.18, 1.0]          # Dark slate container #1a242e
COLOR_INACTIVE_FG = [0.82, 0.90, 0.95, 1.0]          # Crisp silver-white text (never dark/muddy)
COLOR_INACTIVE_ICON = [0.35, 0.78, 0.88, 1.0]        # Subtle cyan icon
COLOR_INACTIVE_BORDER = [0.22, 0.30, 0.38, 1.0]      # Subtle slate border

# Prominent Action States (Analyze AOI, Cross-Check Lake, Standalone 3D Window)
COLOR_ACTION_BG = [0.0, 0.54, 0.62, 1.0]            # Glowing action teal #008a9e
COLOR_ACTION_FG = [1.0, 1.0, 1.0, 1.0]              # Pure white bold
COLOR_ACTION_ICON = [0.0, 0.95, 1.0, 1.0]           # High-luminance electric cyan
COLOR_ACTION_BORDER = [0.0, 0.95, 1.0, 0.9]         # Vivid electric border

# Secondary Action States (e.g. Back to Map, Export GeoJSON, Reset)
COLOR_SECONDARY_BG = [0.12, 0.17, 0.22, 1.0]        # Medium slate
COLOR_SECONDARY_FG = [0.85, 0.92, 0.96, 1.0]        # Light silver
COLOR_SECONDARY_ICON = [0.45, 0.82, 0.92, 1.0]      # Cyan icon
COLOR_SECONDARY_BORDER = [0.28, 0.38, 0.48, 1.0]    # Slate blue border


def apply_button_style(
    btn: MDButton,
    state: str = "inactive",  # "active" | "inactive" | "action" | "secondary"
    custom_bg: Optional[list] = None,
    custom_fg: Optional[list] = None,
) -> None:
    """
    Applies high-contrast styling to an MDButton and its child MDButtonText / MDButtonIcon.
    Guarantees text is never washed out, pale on light background, or low-contrast.
    """
    if not isinstance(btn, MDButton):
        return

    btn.theme_bg_color = "Custom"
    btn.theme_line_color = "Custom"
    btn.theme_elevation_level = "Custom"
    btn.elevation_level = 0
    if hasattr(btn, "focus_behavior"):
        btn.focus_behavior = False

    if btn.size_hint_x is not None:
        btn.theme_width = "Custom"
    if btn.size_hint_y is not None:
        btn.theme_height = "Custom"

    if state == "active":
        btn.style = "filled"
        btn.md_bg_color = custom_bg or COLOR_ACTIVE_BG
        btn._md_bg_color = btn.md_bg_color
        btn.line_color = COLOR_ACTIVE_BORDER
        fg = custom_fg or COLOR_ACTIVE_FG
        icon_fg = COLOR_ACTIVE_ICON
    elif state == "action":
        btn.style = "filled"
        btn.md_bg_color = custom_bg or COLOR_ACTION_BG
        btn._md_bg_color = btn.md_bg_color
        btn.line_color = COLOR_ACTION_BORDER
        fg = custom_fg or COLOR_ACTION_FG
        icon_fg = COLOR_ACTION_ICON
    elif state == "secondary":
        btn.style = "outlined"
        btn.md_bg_color = custom_bg or COLOR_SECONDARY_BG
        btn._md_bg_color = btn.md_bg_color
        btn.line_color = COLOR_SECONDARY_BORDER
        fg = custom_fg or COLOR_SECONDARY_FG
        icon_fg = COLOR_SECONDARY_ICON
    else:  # "inactive"
        btn.style = "outlined"
        btn.md_bg_color = custom_bg or COLOR_INACTIVE_BG
        btn._md_bg_color = btn.md_bg_color
        btn.line_color = COLOR_INACTIVE_BORDER
        fg = custom_fg or COLOR_INACTIVE_FG
        icon_fg = COLOR_INACTIVE_ICON

    btn._glof_style_fg = fg
    btn._glof_style_icon_fg = icon_fg

    def _sync_children(*_):
        curr_fg = getattr(btn, "_glof_style_fg", fg)
        curr_icon_fg = getattr(btn, "_glof_style_icon_fg", icon_fg)
        for child in btn.children:
            if isinstance(child, MDButtonText):
                child.theme_text_color = "Custom"
                child.text_color = curr_fg
                child.color = curr_fg
            elif isinstance(child, MDButtonIcon):
                child.theme_icon_color = "Custom"
                child.icon_color = curr_icon_fg
                child.color = curr_icon_fg

    _sync_children()

    # Re-apply styling if children are added or replaced later
    if not hasattr(btn, "_glof_bound_children"):
        btn._glof_bound_children = True
        btn.bind(children=_sync_children)


def apply_icon_button_style(
    btn: MDIconButton,
    state: str = "secondary",
    custom_icon_color: Optional[list] = None,
) -> None:
    """
    Applies high-contrast cockpit styling to an MDIconButton.
    """
    if not isinstance(btn, MDIconButton):
        return

    btn.theme_bg_color = "Custom"
    btn.theme_icon_color = "Custom"
    btn.theme_line_color = "Custom"

    if state == "action":
        btn.style = "filled"
        btn.md_bg_color = COLOR_ACTION_BG
        btn._md_bg_color = btn.md_bg_color
        color = custom_icon_color or COLOR_ACTION_ICON
        btn.icon_color = color
        btn.color = color
    elif state == "active":
        btn.style = "filled"
        btn.md_bg_color = COLOR_ACTIVE_BG
        btn._md_bg_color = btn.md_bg_color
        color = custom_icon_color or COLOR_ACTIVE_ICON
        btn.icon_color = color
        btn.color = color
    else:
        btn.style = "outlined"
        btn.md_bg_color = COLOR_SECONDARY_BG
        btn._md_bg_color = btn.md_bg_color
        btn.line_color = COLOR_SECONDARY_BORDER
        btn._line_color = COLOR_SECONDARY_BORDER
        color = custom_icon_color or COLOR_TEXT_CYAN
        btn.icon_color = color
        btn.color = color


def apply_card_style(
    container: Union[MDCard, MDBoxLayout],
    custom_bg: Optional[list] = None,
    custom_border: Optional[list] = None,
    radius: Optional[list] = None,
) -> None:
    """
    Applies high-contrast dark telemetry container styling to an MDBoxLayout or MDCard.
    Eliminates elevation shadow FBO overhead while ensuring crisp borders and background fill.
    """
    if not isinstance(container, (MDCard, MDBoxLayout)):
        return

    if hasattr(container, "style"):
        container.style = "outlined"
    if hasattr(container, "theme_bg_color"):
        container.theme_bg_color = "Custom"
    if hasattr(container, "theme_line_color"):
        container.theme_line_color = "Custom"
    if hasattr(container, "elevation_level"):
        container.elevation_level = 0
    if hasattr(container, "focus_behavior"):
        container.focus_behavior = False

    bg = custom_bg or COLOR_CARD_BG
    container.md_bg_color = bg
    container._md_bg_color = bg

    border = custom_border or COLOR_CARD_BORDER
    container.line_color = border
    if hasattr(container, "_line_color"):
        container._line_color = border

    r = radius or [10, 10, 10, 10]
    container.radius = r
    if hasattr(container, "_radius"):
        container._radius = r
