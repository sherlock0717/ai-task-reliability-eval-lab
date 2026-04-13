label ch1_main:
    call scene_hook_chapter_placeholder
    show char placeholder at char_center

    ch_guide "第一章。占位场景与占位立绘。"
    mc "能推进即可。"

    menu:
        "走向 A（占位）":
            $ ch1_choice = "a"
        "走向 B（占位）":
            $ ch1_choice = "b"

    ch_guide "选择已记录：[ch1_choice!q]"
    jump ch2a_main
