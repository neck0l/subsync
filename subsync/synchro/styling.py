"""Optional ASS styling / positioning for output subtitles.

When the output is written as .ass, an optional position preset (and opaque box)
is applied to the Default style. Uses pysubs2's native style model rather than
hand-writing ASS. Position presets mirror the common placements used for
translated / secondary subtitles.
"""

import logging
import pysubs2

logger = logging.getLogger(__name__)


# preset -> (alignment numpad, MarginV). Alignment 2 = bottom-center, 8 = top-center.
STYLE_PRESETS = {
    'above':  ('Above hardcoded line', 2, 72),
    'bottom': ('Bottom (standard)',    2, 42),
    'middle': ('Lower middle',         2, 180),
    'top':    ('Top',                  8, 50),
}


def presetLabels():
    return {key: label for key, (label, _a, _v) in STYLE_PRESETS.items()}


def applyStyle(subtitles, preset='above', box=True, font='Arial', size=42):
    """Apply a position/box preset to the Default style of a pysubs2 SSAFile.

    Modifies in place and returns it. Only meaningful for ASS output.
    """
    label_align_margin = STYLE_PRESETS.get(preset, STYLE_PRESETS['above'])
    _label, alignment, margin_v = label_align_margin

    style = subtitles.styles.get('Default')
    if style is None:
        style = pysubs2.SSAStyle()
        subtitles.styles['Default'] = style

    style.fontname = font
    style.fontsize = size
    style.primarycolor = pysubs2.Color(255, 255, 255, 0)
    style.outlinecolor = pysubs2.Color(0, 0, 0, 0)
    try:
        style.alignment = pysubs2.Alignment(alignment)
    except Exception:
        style.alignment = alignment
    style.marginv = margin_v

    if box:
        style.borderstyle = 3                        # opaque box
        style.backcolor = pysubs2.Color(0, 0, 0, 0)  # opaque black
        style.outline = 10
        style.shadow = 0
    else:
        style.borderstyle = 1                        # outline + shadow
        style.outline = 3
        style.shadow = 1

    # Point every event at the Default style so the preset actually applies.
    for event in subtitles:
        if not getattr(event, 'is_comment', False):
            event.style = 'Default'

    return subtitles


def maybeStyle(subtitles, path, preset=None, box=True):
    """Apply styling only when the path is an ASS/SSA file and a preset is set."""
    if not preset:
        return subtitles
    ext = str(path).lower()
    if ext.endswith('.ass') or ext.endswith('.ssa'):
        applyStyle(subtitles, preset=preset, box=box)
    return subtitles
