## Minimal GUI bootstrap (Ren'Py 8 expects gui.init).

init offset = -2

init python:
    gui.init(1280, 720)

define gui.accent_color = "#6b8cae"
define gui.idle_color = "#888888"
define gui.hover_color = "#c8d8e8"
define gui.selected_color = "#ffffff"
define gui.muted_color = "#666666"
define gui.hover_muted_color = "#999999"
define gui.text_color = "#e8e8e8"
define gui.interface_text_color = "#e8e8e8"

define gui.text_font = "DejaVuSans.ttf"
define gui.name_text_font = "DejaVuSans.ttf"
define gui.interface_text_font = "DejaVuSans.ttf"
define gui.button_text_font = "DejaVuSans.ttf"
define gui.choice_button_text_font = "DejaVuSans.ttf"

define gui.main_font = gui.text_font
