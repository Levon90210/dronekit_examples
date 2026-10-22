import tkinter as tk

ROOT_WINDOW_WIDTH = 600
ROOT_WINDOW_HEIGHT = 450
REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]
MODE_LIST = ["GUIDED", "STABILIZE", "LOITER", "LAND", "RTL"]

WINDOW_BG = "#111827"
SECTION_BG = "#1F2937"
INPUT_BG = "#0F172A"

MAIN_TEXT_COLOR = "#F9FAFB"
SECONDARY_TEXT_COLOR = "#9CA3AF"

PRIMARY_BG = "#3B82F6"
PRIMARY_ACTIVE_BG = "#2563EB"

SECONDARY_BG = INPUT_BG
SECONDARY_ACTIVE_BG = "#374151"

ARM_BG = "#F59E0B"
ARM_ACTIVE_BG = "#D97706"

BUTTON_DEFAULTS = {
    "relief": tk.FLAT,
    "bd": 0,
    "padx": 12,
    "pady": 7,
}

PRIMARY_BUTTON_STYLE = {
    "bg": PRIMARY_BG,
    "fg": MAIN_TEXT_COLOR,
    "activebackground": PRIMARY_ACTIVE_BG,
    "activeforeground": MAIN_TEXT_COLOR,
    "disabledforeground": SECONDARY_TEXT_COLOR,
}

SECONDARY_BUTTON_STYLE = {
    "bg": SECONDARY_BG,
    "fg": MAIN_TEXT_COLOR,
    "activebackground": SECONDARY_ACTIVE_BG,
    "activeforeground": MAIN_TEXT_COLOR,
    "disabledforeground": SECONDARY_TEXT_COLOR,
}

ARM_BUTTON_STYLE = {
    "bg": ARM_BG,
    "fg": INPUT_BG,
    "activebackground": ARM_ACTIVE_BG,
    "activeforeground": INPUT_BG,
    "disabledforeground": INPUT_BG,
}
