import tkinter as tk
from typing import Any

WINDOW_BG = "#111827"
SECTION_BG = "#1F2937"
INPUT_BG = "#0F172A"

INDICATOR_BG = "#6B7280"
INDICATOR_FILL_BG = "#84CC16"

MAIN_TEXT_COLOR = "#F9FAFB"
SECONDARY_TEXT_COLOR = "#9CA3AF"

PRIMARY_BG = "#3B82F6"
PRIMARY_ACTIVE_BG = "#2563EB"

SECONDARY_BG = INPUT_BG
SECONDARY_ACTIVE_BG = "#374151"

ARM_BG = "#F59E0B"
ARM_ACTIVE_BG = "#D97706"
ARM_DISABLED_BG = "#374151"

LOG_FONT = "monospace"
LOG_FONT_SIZE = 10
LOG_AREA_HEIGHT = 8

BUTTON_DEFAULTS: dict[str, Any] = {
    "relief": tk.FLAT,
    "bd": 0,
    "padx": 12,
    "pady": 7,
}

PRIMARY_BUTTON_STYLE: dict[str, Any] = {
    "bg": PRIMARY_BG,
    "fg": MAIN_TEXT_COLOR,
    "activebackground": PRIMARY_ACTIVE_BG,
    "activeforeground": MAIN_TEXT_COLOR,
    "disabledforeground": SECONDARY_TEXT_COLOR,
}

SECONDARY_BUTTON_STYLE: dict[str, Any] = {
    "bg": SECONDARY_BG,
    "fg": MAIN_TEXT_COLOR,
    "activebackground": SECONDARY_ACTIVE_BG,
    "activeforeground": MAIN_TEXT_COLOR,
    "disabledforeground": SECONDARY_TEXT_COLOR,
}

ARM_BUTTON_STYLE: dict[str, Any] = {
    "bg": ARM_BG,
    "fg": INPUT_BG,
    "activebackground": ARM_ACTIVE_BG,
    "activeforeground": INPUT_BG,
    "disabledforeground": SECONDARY_TEXT_COLOR,
}

LOG_AREA_STYLE: dict[str, Any] = {
    "bg": INPUT_BG,
    "fg": MAIN_TEXT_COLOR,
    "font": (LOG_FONT, LOG_FONT_SIZE),
    "height": LOG_AREA_HEIGHT,
    "width": 1,
    "relief": tk.FLAT,
    "bd": 0,
    "highlightthickness": 0,
    "padx": 10,
    "pady": 8,
    "wrap": tk.WORD,
}
