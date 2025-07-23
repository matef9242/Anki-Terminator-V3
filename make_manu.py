
from aqt import mw, QMenu
from .path_manager import ADDON_TITLE_2

anki_terminator_menu = None

def get_anki_terminator_menu():
    global anki_terminator_menu
    if not isinstance(anki_terminator_menu, QMenu):
        anki_terminator_menu = QMenu("🤖"+ADDON_TITLE_2, mw)
        mw.form.menuTools.addMenu(anki_terminator_menu)
    return anki_terminator_menu
