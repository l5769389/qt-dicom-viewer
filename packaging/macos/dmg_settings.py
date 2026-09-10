"""dmgbuild 的 Finder 安装窗口配置，位置以逻辑点表示。"""

from pathlib import Path

application = Path(defines["app"])
# Qt 6 requires newer macOS versions than ULMO's macOS 10.15 minimum.
format = "ULMO"
compression_level = 9
files = [str(application), (defines["readme"], "安装说明.txt")]
symlinks = {"Applications": "/Applications"}
icon = defines["icon"]
background = "builtin-arrow"
window_rect = ((160, 120), (640, 420))
icon_locations = {application.name: (140, 120), "Applications": (500, 120), "安装说明.txt": (320, 320)}
icon_size = 96
text_size = 14
default_view = "icon-view"
include_icon_view_settings = True
arrange_by = None
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
show_icon_preview = False
