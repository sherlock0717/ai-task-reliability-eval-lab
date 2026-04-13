screen demo_end_screen():
    modal True
    zorder 200
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 36
        ypadding 28
        background Solid("#1a1a22")
        vbox:
            spacing 14
            xminimum 520
            text "[UI_LINE_TITLE]" size 26 color "#e8e8e8"
            null height 6
            text "[UI_LINE_END_PRIMARY]" size 22 color "#c8d8e8"
            text "[UI_LINE_END_SUB]" size 16 color "#9aa0aa"
            null height 12
            textbutton _("关闭") action Return() xalign 0.5


label demo_end:
    call screen demo_end_screen
    return
