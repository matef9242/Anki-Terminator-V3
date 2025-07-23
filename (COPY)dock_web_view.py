# -*- coding: utf-8 -*-
import gc
import os
import random
import time
import urllib.parse
from aqt.utils import openLink
from aqt import (QAction, QCheckBox, QComboBox, QCoreApplication, QDockWidget, QEvent, QEventLoop, QFile, QFontMetrics, QGraphicsOpacityEffect,
                QKeySequence, QLabel, QLineEdit, QMenu, QObject,
                QPixmap, QPushButton, QShortcut, QSize, QTimer, QToolBar, QUrl, QVBoxLayout,
                QWebEnginePage,
                QWebEngineProfile, QWebEngineSettings, gui_hooks,
                QWebEngineView, QWidget, Qt, mw)
from aqt.webview import AnkiWebView
from os.path import join, dirname, exists
from anki.cards import Card

from .config.PopUpAnkiConfig import (SOUND_SYSTEM, set_this_addon_Config,CONFIG_FOLDER,
                                    SOUND_OPEN,SOUND_SELECT,SOUND_OPENLINK,SOUND_OK,
                                    SOUND_CANCEL,SOUND_SYSTEM,THEME_CHANGE)
"""
PYGsound(SOUND_OPEN)
PYGsound(SOUND_SELECT)
PYGsound(SOUND_OPENLINK)
PYGsound(SOUND_OK)
PYGsound(SOUND_CANCEL)
PYGsound(SOUND_SYSTEM)
PYGsound(THEME_CHANGE)
"""

from .path_manager import BING_CHAT, CHAT_GPT, COOKIE_DATA, GOOGLE_BARD, NOW_LOADING, SHOW_ANSWER_PNG,HIDE_HIGHT, USER_FILES ,CUSTOM_AI
from .shigetr import shige_tr, qtip_style

from .context_menu.add_fields import add_context_menu

web_shortcut = None

SYMBOL = {
    "single_quotation": ["'","'"],
    "brackets": ["[","]"],
    "parentheses": ["(",")"],
    "braces": ["{","}"],
    "angle_brackets": ["<",">"],
    "none": ["",""],
    "bold_md": [" **","** "],
    "bold_html": ["<b>","</b>"],
    "span_translation_no": ["<span translation=\"no\">","</span>"],
} # どれも効果がありません¯\_(ﾂ)_/¯

CHOICE_SYMBOL = "single_quotation"

class MyWebPage(QWebEnginePage): # 使ってない
    # ﾊﾟｿｺﾝのﾃﾞﾌｫﾙﾄのﾌﾞﾗｳｻﾞで開かれてしまう場合､
    # QWebEnginePageのcreateWindow関数をｵｰﾊﾞｰﾗｲﾄﾞする必要がある
    def createWindow(self, QWebEnginePage_WebWindowType):
        new_webview = AnkiWebView(title="My Web Page")
        new_webview.setPage(MyWebPage(new_webview))
        return new_webview.page()

class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        if not self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():
            if self.pageAction(QWebEnginePage.WebAction.Back).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.Back))
            if self.pageAction(QWebEnginePage.WebAction.Forward).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.Forward))
            if self.pageAction(QWebEnginePage.WebAction.Reload).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.Reload))

        if self.pageAction(QWebEnginePage.WebAction.Paste).isEnabled():
            menu.addAction(self.pageAction(QWebEnginePage.WebAction.Paste))

        if self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():
            menu.addAction(self.pageAction(QWebEnginePage.WebAction.Copy))

            custom_action = QAction("🤖Set text to AnkiTerminator", self)
            custom_action.triggered.connect(
                lambda: self.contextMenu(self, menu))
            menu.addAction(custom_action)

        menu.addSeparator()
        text_action = QAction("❔️📥Add text to card", menu)
        text_action.triggered.connect(
            lambda: openLink(
        "https://shigeyukey.github.io/shige-addons-wiki/AnkiTerminator/anki_terminator_00.html#right-click-actions"))
        # text_action.setEnabled(False)
        menu.addAction(text_action)

        if self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():

            menu.addSeparator()
            add_context_menu(self, menu)
            menu.addSeparator()

        # Show the context menu
        menu.exec(event.globalPos())

    def contextMenu(self, webview: AnkiWebView, menu: QMenu,*args,**kwargs):
        selected = webview.page().selectedText()
        if not selected:
            return
        self.parent_window.set_last_text(selected)
        # self.parent_window.more_function("random_prompt",selected)






class ResizableWebView(QWidget):
    def __init__(self, name, url, parent=None):
        super().__init__(parent)
        # ---------- Cookie monster ---------------
        print(r"""
Cookie monster! Om nom nom nom nom nom nom...
               _  _
             _/0\/ \_
    .-.   .-` \_/\0/ '-.
   /:::\ / ,_________,  \
  /\:::/ \  '. (:::/  `'-;
  \ `-'`\ '._ `"'"'\__    \
   `'-.  \   `)-=-=(  `,   |
jgs    \  `-"`      `"-`   /
                """)
        self.cookie_profile = QWebEngineProfile("my_profile")
        # profile = QWebEngineProfile.defaultProfile() # ﾃﾞﾌｫﾙﾄのﾌﾟﾛﾌｧｲﾙ名
        self.cookie_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        browser_storage_folder = join(dirname(__file__), USER_FILES,COOKIE_DATA)
        if not exists(browser_storage_folder):
            os.makedirs(browser_storage_folder)
        self.cookie_profile.setPersistentStoragePath(browser_storage_folder)
        # ---------- Cookie monster ---------------
        self.last_call = 0
        self.last_card = None
        self.last_text = None
        self.context_action = None
        self.loading = False
        self.last_card_note = None

        self.setWindowTitle(name)
        self.setMinimumSize(QSize(300, 300))

        self.webview = CustomWebEngineView(self)
        # self.webview = QWebEngineView()
        # self.webview = AnkiWebView()

        # ｸﾘｯﾌﾟﾎﾞｰﾄﾞにｺﾋﾟｰ可能にする
        settings = self.cookie_profile.settings() # Cookie monster
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)

        # ----------------------------------
        self.grey_widget = QWidget()
        # self.grey_widget.setStyleSheet("background-color: grey;")
        addon_path = dirname(__file__)
        icon_path = join(addon_path, NOW_LOADING)
        pixmap = QPixmap(icon_path)
        self.label = QLabel(self.grey_widget)
        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self.grey_widget)
        layout.addWidget(self.label)
        self.grey_widget.setLayout(layout)
        # ----------------------------------

        self.webpage = QWebEnginePage(self.cookie_profile, self.webview) # Cookie monster
        self.webview.loadStarted.connect(self.on_load_started)
        self.webview.loadFinished.connect(self.on_load_finished)

        self.webview.loadFinished.connect(self.inject_javascript)

        self.hide_webview()

        self.webview.setPage(self.webpage)
        self.webview.load(QUrl(url))

        layout = QVBoxLayout(self)
        self.last_text_toolbar(layout)
        self.make_menu_button(layout)

        layout.addWidget(self.webview)
        layout.addWidget(self.grey_widget)
        layout.setContentsMargins(1, 1, 1, 1)

        self.setLayout(layout)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)#たぶんいらない

        # closeEventをﾌｯｸしてｵﾌﾞｼﾞｪｸﾄを削除しないようにする
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)#たぶんいらない

        gui_hooks.webview_will_show_context_menu.remove(self.contextMenu)
        gui_hooks.webview_will_show_context_menu.append(self.contextMenu)

        gui_hooks.editor_will_show_context_menu.remove(self.contextMenu)
        gui_hooks.editor_will_show_context_menu.append(self.contextMenu)


        gui_hooks.reviewer_did_show_question.remove(self.ChatGPT_hide_webview)
        gui_hooks.reviewer_did_show_question.append(self.ChatGPT_hide_webview)

        gui_hooks.reviewer_did_show_answer.remove(self.ChatGPT_show_webview)
        gui_hooks.reviewer_did_show_answer.append(self.ChatGPT_show_webview)

        gui_hooks.reviewer_will_end.remove(self.ChatGPT_show_webview)
        gui_hooks.reviewer_will_end.append(self.ChatGPT_show_webview)

        gui_hooks.reviewer_did_show_answer.remove(self.show_answer_preload)
        gui_hooks.reviewer_did_show_answer.append(self.show_answer_preload)

        gui_hooks.reviewer_did_show_question.remove(self.show_question_preload)
        gui_hooks.reviewer_did_show_question.append(self.show_question_preload)

        self.opacity_effect_0 = QGraphicsOpacityEffect(self)
        self.opacity_effect_1 = QGraphicsOpacityEffect(self)




    def inject_javascript(self):
        config = mw.addonManager.getConfig(__name__)
        if not config.get("now_AI_type", False) == CHAT_GPT:
            return
        if not config.get("auto_read_aloud", True):
            return

        javascript_code = """
        let clickedTestIds = new Set();

        function findAndClickButton() {
            const conversationTurns = document.querySelectorAll('[data-testid^="conversation-turn-"]');
            let maxTestIdElement = null;
            let maxTestId = -1;
            conversationTurns.forEach(element => {
                const testId = parseInt(element.getAttribute('data-testid').split('-').pop());
                if (testId > maxTestId && !clickedTestIds.has(testId)) {
                    maxTestId = testId;
                    maxTestIdElement = element;
                }
            });

            if (maxTestIdElement) {
                const button = maxTestIdElement.querySelector('span[data-state="closed"] > button[aria-label="Read Aloud"]');
                if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {
                    button.click();
                    clickedTestIds.add(maxTestId);
                }
            }
        }

        setInterval(findAndClickButton, 2000);
        """

        # javascript_code = """
        # let clickedTestIds = new Set();
        # let queue = [];
        # let isPlaying = false;

        # function findAndClickButton() {
        #     const conversationTurns = document.querySelectorAll('[data-testid^="conversation-turn-"]');
        #     conversationTurns.forEach(element => {
        #         const testId = parseInt(element.getAttribute('data-testid').split('-').pop());
        #         if (!clickedTestIds.has(testId)) {
        #             const button = element.querySelector('span[data-state="closed"] > button[aria-label="Read Aloud"]');
        #             if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {
        #                 queue.push({ testId, button });
        #                 clickedTestIds.add(testId);
        #             }
        #         }
        #     });

        #     if (!isPlaying) {
        #         playNextInQueue();
        #     }
        # }

        # function playNextInQueue() {
        #     if (queue.length === 0) {
        #         isPlaying = false;
        #         return;
        #     }

        #     isPlaying = true;
        #     const { testId, button } = queue.shift();
        #     button.click();

        #     const intervalId = setInterval(() => {
        #         const stopButton = document.querySelector(`[data-testid="conversation-turn-${testId}"] button[aria-label="Stop"]`);
        #         if (!stopButton || stopButton.offsetParent === null) { // Check if the stop button is hidden
        #             clearInterval(intervalId);
        #             playNextInQueue();
        #         }
        #     }, 1000);
        # }

        # setInterval(findAndClickButton, 2000);
        # """

        self.webview.page().runJavaScript(javascript_code)


    def close_cookie_profile(self):

        if hasattr(self, 'webview'):
            if self.webview.page():
                page = self.webview.page()
                self.webview.setPage(None)
                page.deleteLater()
                # del page
            # del self.webview
            self.webview.deleteLater()
            self.webview = None

        if hasattr(self, 'webpage'):
            # del self.webpage
            self.webpage.deleteLater()
            self.webpage = None

        QCoreApplication.processEvents()

        self.cookie_profile.setPersistentStoragePath("")
        self.cookie_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)

        referrers = gc.get_referrers(self.cookie_profile)
        if len(referrers) == 1:  # 参照がselfのみ
            # deleteLaterだと削除されない
            # webviewが削除されるにdelするとｸﾗｯｼｭする
            del self.cookie_profile
            self.cookie_profile = None


    def ChatGPT_hide_webview(self, *args, **kwargs):
        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        if hide:
            self.change_image(SHOW_ANSWER_PNG)
            self.grey_widget.setVisible(True)
            self.webview.setVisible(False)
            self.opacity_effect_0.setOpacity(0)
            self.last_text_edit.setGraphicsEffect(self.opacity_effect_0)

            # self.webview.setFixedHeight(HIDE_HIGHT)
            # self.grey_widget.setVisible(True)
            # self.grey_widget.setFixedHeight(self.height())

    def ChatGPT_show_webview(self, *args, **kwargs):
        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        if hide:
            self.grey_widget.setVisible(False)
            self.webview.setVisible(True)
            # self.last_text_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.opacity_effect_0.setOpacity(1)
            self.last_text_edit.setGraphicsEffect(self.opacity_effect_0)

            # self.grey_widget.setVisible(False)
            # self.webview.setFixedHeight(self.height())

        elif not self.loading and self.webview.height() == HIDE_HIGHT:
            self.grey_widget.setVisible(False)
            self.webview.setVisible(True)
            self.opacity_effect_0.setOpacity(1)
            self.last_text_edit.setGraphicsEffect(self.opacity_effect_0)

            # self.grey_widget.setVisible(False)
            # self.webview.setFixedHeight(self.height())
        else:
            pass

    def change_image(self, image_name):
        addon_path = dirname(__file__)
        icon_path = join(addon_path, image_name)
        pixmap = QPixmap(icon_path)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.label.setPixmap(pixmap)

    def load_url(self):
        config = mw.addonManager.getConfig(__name__)
        now_AI_type = config["now_AI_type"]
         
        if now_AI_type in config["ChatGPT_URL"]:
            ChatGPT_URL = config["ChatGPT_URL"][now_AI_type]
        elif (now_AI_type == CUSTOM_AI
            and not config["Custom_AI_URL"].isspace()):
            ChatGPT_URL = config["Custom_AI_URL"]
        else: # ﾃﾞﾌｫﾙﾄ
            ChatGPT_URL = CHAT_GPT


        self.webview.load(QUrl(ChatGPT_URL))

    def on_load_started(self):
        self.loading = True
        self.hide_webview()

    def on_load_finished(self):
        self.loading = False
        self.show_webview()

    def hide_webview(self):
        self.grey_widget.setVisible(True)
        self.webview.setVisible(False)

    def show_webview(self):
        self.grey_widget.setVisible(False)
        self.webview.setVisible(True)

    # def hide_webview(self):
    #     self.webview.setFixedHeight(HIDE_HIGHT)
    #     self.grey_widget.setVisible(True)
    #     self.grey_widget.setFixedHeight(self.height())


    # def show_webview(self):
    #     self.grey_widget.setVisible(False)
    #     self.webview.setFixedHeight(self.height())



    def last_text_toolbar(self, layout: QVBoxLayout):
        self.last_text_bar = QToolBar()
        self.last_text_bar.setStyleSheet("QToolBar { margin: 1px; padding: 1px; }")
        layout.addWidget(self.last_text_bar)

        self.make_button("AI", lambda :self.change_AI_type(), self.last_text_bar,True)

        config = mw.addonManager.getConfig(__name__)

        self.checkbox = QCheckBox()
        self.checkbox .setStyleSheet("QCheckBox { margin: 1px; padding: 1px; }")
        self.checkbox.stateChanged.connect(self.checkbox_state_changed)
        self.checkbox.setChecked(config["submit_text"])
        self.checkbox.setStyleSheet(qtip_style)
        self.checkbox.setToolTip(shige_tr.check_box_tooltip)
        self.last_text_bar.addWidget(self.checkbox)


        # auto_read_aloud ﾁｪｯｸﾎﾞｯｸｽの追加
        self.auto_read_aloud_checkbox = QCheckBox()
        self.auto_read_aloud_checkbox.setStyleSheet("QCheckBox { margin: 1px; padding: 1px; }")
        self.auto_read_aloud_checkbox.stateChanged.connect(self.auto_read_aloud_checkbox_state_changed)
        self.auto_read_aloud_checkbox.setChecked(config.get("auto_read_aloud", True))
        self.auto_read_aloud_checkbox.setStyleSheet(qtip_style)
        self.auto_read_aloud_checkbox.setToolTip("Auto-read aloud (for ChatGPT only)")
        self.last_text_bar.addWidget(self.auto_read_aloud_checkbox)
        # ------------------------------



        self.last_text_edit = QLineEdit(self.last_text)
        self.last_text_edit.setStyleSheet("QLineEdit { margin: 1px; padding: 1px; }")
        self.last_text_edit.textChanged.connect(self.update_last_text)
        self.last_text_bar.addWidget(self.last_text_edit)

        # self.make_button(shige_tr.option, self.option_button_click, self.last_text_bar)
        self.make_button(" ⚙️ ", self.option_button_click, self.last_text_bar)


        if True:
            self.make_button("❔️", self.question_button_click, self.last_text_bar)

        config = mw.addonManager.getConfig(__name__)

        if not config.get("sidebar_rate_this_clicked", False):
            self.make_button("👍️", self.rate_this_button_click, self.last_text_bar)
        else:
            self.make_button("💖", self.patreon_button_click, self.last_text_bar)

    def question_button_click(self):
        openLink("https://shigeyukey.github.io/shige-addons-wiki/AnkiTerminator/anki_terminator_00.html#ai-sidebar")

    def rate_this_button_click(self):
        ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
        if (isinstance(ADDON_PACKAGE, (int, float))
            or (isinstance(ADDON_PACKAGE, str)
            and ADDON_PACKAGE.isdigit())):
            RATE_THIS_URL = f"https://ankiweb.net/shared/review/{ADDON_PACKAGE}"
            openLink(RATE_THIS_URL)
        config = mw.addonManager.getConfig(__name__)
        config["sidebar_rate_this_clicked"] = True
        mw.addonManager.writeConfig(__name__, config)
        PYGsound(SOUND_OPENLINK)

    def patreon_button_click(self):
        openLink("https://www.patreon.com/Shigeyuki")
        PYGsound(SOUND_OPENLINK)

    def auto_read_aloud_checkbox_state_changed(self, state):
        config = mw.addonManager.getConfig(__name__)
        config["auto_read_aloud"] = (state == 2)
        mw.addonManager.writeConfig(__name__, config)
        self.webview.reload()


    def checkbox_state_changed(self, state):
        config = mw.addonManager.getConfig(__name__)
        if state == 2:
            config["submit_text"] = True
        else:
            config["submit_text"] = False
        mw.addonManager.writeConfig(__name__, config)

    def change_AI_type(self,update=True):
        if update:
            from .path_manager import update_theme
            update_theme()
            PYGsound(THEME_CHANGE)
        self.load_url()
        from .update_top_toolbar import change_AI_icon_on_top_tool_bar # 循環ｲﾝﾎﾟｰﾄ
        change_AI_icon_on_top_tool_bar()


    def option_button_click(self):
        set_this_addon_Config()


    def update_last_text(self, text):
        # ﾃｷｽﾄが編集されたときにself.last_textを更新
        self.last_text = text

    def set_last_text(self, text):
        # self.last_textを更新し､ﾃｷｽﾄｴﾃﾞｨｯﾄも更新
        self.last_text = text
        self.last_text_edit.setText(text)

    def get_field_text(self, card=None):# 書き途中
        config = mw.addonManager.getConfig(__name__)
        if card is None and mw.state == "review":
            card = mw.reviewer.card
        else:
            return
        self.last_card = card
        note = card.note()
        self.last_card_note = note
        note_type = note.note_type()

        if self.is_excluded_note_type(config, note_type):
            return

        # field_names = note_type['flds']
        # first_field_name = field_names[0]['name']

        first_field_name = self.get_priority_field_name(config, note_type)

        text = card.note()[first_field_name]
        self.set_last_text(text)


    # def make_menu_button(self, layout: QVBoxLayout):
    #     config = mw.addonManager.getConfig(__name__)
    #     b_name = config["button_name"]

    #     # ﾎﾞﾀﾝの名前とｱｸｼｮﾝのﾘｽﾄ
    #     buttons = [
    #         # ("field", self.field_function),
    #         (b_name[0], lambda: self.more_function("random_prompt")),
    #         (b_name[1], lambda: self.more_function("more_info")),
    #         (b_name[2], lambda: self.more_function("baby_explanation")),
    #         (b_name[3], lambda: self.more_function("word_origin")),
    #         (b_name[4], lambda: self.more_function("make_joke")),
    #         (b_name[5], lambda: self.more_function("history")),
    #         (b_name[6], lambda: self.more_function("synonym")),
    #         (b_name[7], lambda: self.more_function("mnemonic")),
    #     ]

    #     # ﾂｰﾙﾊﾞｰを作成
    #     self.toolBar = QToolBar()
    #     self.toolBar.setStyleSheet("QToolBar { margin: 1px; padding: 1px; }")

    #     layout.addWidget(self.toolBar)

    #     layout.setContentsMargins(1, 1, 1, 1)

    #     for button_name, action_function in buttons:
    #         self.make_button(button_name, action_function, self.toolBar)

    # ---------------------------------------------------
    def make_menu_button(self, layout: QVBoxLayout):
        config = mw.addonManager.getConfig(__name__)
        b_name = config["button_name"]

        button_function_pairs = {
            "random_prompt": b_name[0],
            "more_info": b_name[1],
            "baby_explanation": b_name[2],
            "word_origin": b_name[3],
            "make_joke": b_name[4],
            "history": b_name[5],
            "synonym": b_name[6],
            "mnemonic": b_name[7]
        }

        # ﾎﾞﾀﾝの名前とｱｸｼｮﾝのﾘｽﾄ
        buttons = []
        for text, name in button_function_pairs.items():
            buttons.append((name, lambda text=text: self.more_function(text)))


        # ﾂｰﾙﾊﾞｰを作成
        self.toolBar = QToolBar()
        self.toolBar.setStyleSheet("QToolBar { margin: 1px; padding: 1px; }")

        layout.addWidget(self.toolBar)

        layout.setContentsMargins(1, 1, 1, 1)

        for button_name, action_function in buttons:
            self.make_button(button_name, action_function, self.toolBar)

        # ｺﾝﾎﾞﾎﾞｯｸｽ ========================
        def save_selection():
            selected_key = combo_box.currentData()
            config["default_prompt"] = selected_key
            mw.addonManager.writeConfig(__name__, config)

        def adjust_combo_box_width():
            font_metrics = QFontMetrics(combo_box.font())
            max_width = 0
            for i in range(combo_box.count()):
                text = combo_box.itemText(i)
                width = font_metrics.horizontalAdvance(text)
                if width > max_width:
                    max_width = width
            combo_box.setFixedWidth(max_width + 20)

        config = mw.addonManager.getConfig(__name__)
        default_prompt = config.get("default_prompt", "random_prompt")
        combo_box = QComboBox()

        for key, value in button_function_pairs.items():
            combo_box.addItem(value, key)

        if default_prompt not in button_function_pairs:
            default_prompt = "random_prompt"

        default_index = combo_box.findData(default_prompt)
        if default_index != -1:
            combo_box.setCurrentIndex(default_index)

        combo_box.currentIndexChanged.connect(save_selection)
        combo_box.currentIndexChanged.connect(adjust_combo_box_width)
        adjust_combo_box_width()
        self.toolBar.addWidget(combo_box)
        # ｺﾝﾎﾞﾎﾞｯｸｽ ========================



    def make_button(self, button_name, action_function, toolbar,sound=False):
        action = QAction(button_name, self)
        button = QPushButton(button_name)
        fm = QFontMetrics(button.font())
        width = fm.horizontalAdvance(button_name)
        button.setFixedSize(width + 10, 25)
        button.setStyleSheet("QPushButton { margin: 1px; padding: 1px; }")
        action.triggered.connect(action_function)
        button.clicked.connect(action.trigger)
        if sound is False:
            button.clicked.connect(lambda: PYGsound(SOUND_SELECT))
        toolbar.addWidget(button)

    def update_button_names(self):
        # 最新の設定を取得
        config = mw.addonManager.getConfig(__name__)
        b_name = config["button_name"]

        # ﾎﾞﾀﾝの名前を更新
        for i, action in enumerate(self.toolBar.actions()):
            button = self.toolBar.widgetForAction(action)
            if isinstance(button, QComboBox):
                continue

            action.setText(b_name[i])
            button = self.toolBar.widgetForAction(action)
            button.setText(b_name[i])
            fm = QFontMetrics(button.font())
            width = fm.horizontalAdvance(b_name[i])
            button.setFixedSize(width + 10, 25)
    # ---------------------------------------------------

    def field_function(self):# 使ってない
        # self.load_and_interact()
        self.get_field_text()

    # def more_function(self,text,search_text=None):
    #     if search_text is not None:
    #         self.set_last_text(search_text)
    #     if self.last_text is not None:
    #         config = mw.addonManager.getConfig(__name__)
    #         more_info = config[text]
    #         more_info = random.choice(more_info)
    #         if "{}" in more_info:
    #             prompt_text = more_info.format(SYMBOL[CHOICE_SYMBOL][0]
    #                                             + self.last_text
    #                                             + SYMBOL[CHOICE_SYMBOL][1])
    #         else:
    #             prompt_text = self.last_text + more_info
    #         self.handle_load_finished(text=prompt_text, click=True)

    def more_function(self, text, search_text=None):
        if search_text is not None:
            self.set_last_text(search_text)
        if self.last_text is not None:
            config = mw.addonManager.getConfig(__name__)
            more_info = config[text]
            more_info = random.choice(more_info)
            if "{}" in more_info:
                prompt_text = more_info.format(SYMBOL[CHOICE_SYMBOL][0]
                                                + self.last_text
                                                + SYMBOL[CHOICE_SYMBOL][1])
            else:
                prompt_text = self.last_text + more_info
            self.handle_load_finished(text=prompt_text, click=True)


    def wrap_with_quotes(self,text):
        return "'" + text + "'"

    def contextMenu(self, webview: AnkiWebView, menu: QMenu,*args,**kwargs):
        selected = webview.page().selectedText()
        if not selected:
            return
        menu.addSeparator()
        # self.context_action = QAction("ChatGPT", mw)
        self.context_action = QAction("🤖Explain with AnkiTerminator", mw)

        config = mw.addonManager.getConfig(__name__)
        default_prompt = config.get("default_prompt", "random_prompt")
        if default_prompt not in config:
            default_prompt = "random_prompt"
        random_prompt = config[default_prompt]

        self.context_action.triggered.connect(lambda:self.more_function(random_prompt, selected))
        # self.context_action.triggered.connect(lambda:self.more_function("random_prompt",selected))

        menu.addAction(self.context_action)

    def show_answer_preload(self,card:Card=None,*args,**kwargs):
        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        submit = config["submit_text"]
        if not hide or not submit:
            self.load_and_interact(card,*args,**kwargs)

    def show_question_preload(self,card:Card=None,*args,**kwargs):
        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        submit = config["submit_text"]
        if hide and submit:
            self.load_and_interact(card,*args,**kwargs)


    def load_and_interact(self,card:Card=None,*args,**kwargs):
        # ﾄﾞｯｸﾞが非表示にされていたらGuiHooksを実行しない
        if not self.isVisible():
            return

        # 特定のﾉｰﾄﾀｲﾌﾟで2回呼び出される場合があるので1秒に制限
        current_time = time.time()
        if current_time - self.last_call < 1:
            return
        self.last_call = current_time

        config = mw.addonManager.getConfig(__name__)

        # text = mw.reviewer.card.note()["Front"] + selected_prompt

        if card is None and self.last_card is not None:# 手動で2回目の呼び出し
            card = self.last_card
        if card is None and self.last_card is None:
            return
        self.last_card = card
        note = card.note()
        self.last_card_note = note
        note_type = note.note_type()

        # 特定のﾉｰﾄﾀｲﾌﾟを除外
        if self.is_excluded_note_type(config, note_type):
            return

        first_field_name = self.get_priority_field_name(config, note_type)

        default_prompt = config.get("default_prompt","random_prompt")
        if default_prompt not in config:
            default_prompt = "random_prompt"
        random_prompt = config[default_prompt]

        # random_prompt = config["random_prompt"]
        selected_prompt = random.choice(random_prompt)



        text = card.note()[first_field_name]
        self.set_last_text(text)
        if "{}" in selected_prompt:
            prompt_text = selected_prompt.format(SYMBOL[CHOICE_SYMBOL][0]
                                                    + text +
                                                    SYMBOL[CHOICE_SYMBOL][1])
        else:
            prompt_text = text + selected_prompt
        self.handle_load_finished(prompt_text)

    # ------------------------------------------------

     
    def is_excluded_note_type(self, config, note_type):
        exclusion_list = config["exclusion_list"]
        # 特定のﾉｰﾄﾀｲﾌﾟを除外
        note_type_name = note_type['name']
        for exclusion in exclusion_list:
            if not exclusion or exclusion.isspace():
                continue
            if exclusion in note_type_name:
                return True
        return False

    def get_priority_field_name(self, config, note_type):
        Priority_Fields_list = config["Priority_Fields_list"]
        field_names = note_type['flds']
        first_field_name = field_names[0]['name']
        for field in field_names:
            if field['name'] in Priority_Fields_list:
                first_field_name = field['name']
                break
        return first_field_name

    def get_priority_tag(self, config):
        Priority_tag_list = config["Priority_tag_list"]
        if self.last_card_note is not None:
            note = self.last_card_note # 引数から直接でないとｽﾞﾚるかも知らん
            tags = note.tags
            priority_tag = ""
            for tag in tags:
                for priority_tag_item in Priority_tag_list:
                    if priority_tag_item in tag:
                        priority_tag = priority_tag_item
                        break
                if priority_tag:
                    break
            return priority_tag
        else:
            priority_tag = ""

    # ------------------------------------------------


# 送信ﾎﾞﾀﾝを押しても実行されないのでこれを参考にした
# https://stackoverflow.com/questions/57879322/how-can-i-enter-data-into-a-custom-handled-input-field/57900849#57900849
        # BingChatはﾃｷｽﾄの入力すらもできません¯\_(ﾂ)_/¯
        # URLでｱｸｾｽすればいけるかも知らん(でもﾛｰﾄﾞが長い)


    def handle_load_finished(self, text, click=False):
        config = mw.addonManager.getConfig(__name__)

        # if not config["input_text"] :
        if not (config["submit_text"] or click):
            return

        if config["change_Language"]:
            random_prompt_lang = config["language"]
            selected_prompt_lang = random.choice(random_prompt_lang)
            lang = shige_tr.lang
            print(lang)
            # if '{}' in selected_prompt_lang and lang is not None:
            if '{}' in selected_prompt_lang:
                selected_prompt_lang = selected_prompt_lang.replace('{}', lang if lang else "")
            text  = text + " " + selected_prompt_lang

        if config["is_i_am_studying"]:
            random_i_am_studying = config["i_am_studying"]
            selected_prompt_study = random.choice(random_i_am_studying)
            study_tag = self.get_priority_tag(config)
            # if '{}' in selected_prompt_study and study_tag is not None:
            if '{}' in selected_prompt_study:
                selected_prompt_study = selected_prompt_study.replace('{}', study_tag if study_tag else "")
            text  = selected_prompt_study + " " + text


        text = text.replace("'", "\\'")
        text = text.replace('"', '\\"')

        now_AI_type = config["now_AI_type"]


        skip_response_icon_check = "true"

        if now_AI_type == CHAT_GPT:
            class_name = "#prompt-textarea"
            button_class = 'button[data-testid="send-button"]'
            # button_class = 'button[data-testid="fruitjuice-send-button"]'
            # stop_button_class = 'button[aria-label="Stop generating"]'
            stop_button_class = 'button[data-testid="stop-button"]'
            # stop_button_class = 'button[data-testid="fruitjuice-stop-button"]'
            parent_element = ""

        elif now_AI_type == GOOGLE_BARD:
            class_name = ".ql-editor.textarea"
            button_class = ".send-button"
            stop_button_class = ".send-button"
            parent_element = ""
            # stop_button_class = "span.overline"
            # parent_element = ".parentElement"
            skip_response_icon_check = "document.querySelector('svg[alt=\"skip response icon\"]')"

        elif now_AI_type == BING_CHAT:
            # if config["submit_text"] or click :
            encoded_text = urllib.parse.quote(text)
            url = f"https://www.bing.com/search?showconv=1&sendquery=1&q={encoded_text}"
            self.webview.load(QUrl(url))

            return
        #     class_name = ".text-area"
        #     button_class = "button[is='cib-button'][aria-label='Submit']"
        #     stop_button_class = "#stop-responding-button"
        #     parent_element = ""
        #     # stop_button_class = "span.overline"
        #     # parent_element = ".parentElement"


        else:
            return

        js_code = f"""
        function replaceValue(selector, value) {{
        const el = document.querySelector(selector);
        if (el) {{
            el.focus();
            document.execCommand('selectAll');
            if (!document.execCommand('insertText', false, value)) {{
            el.value = '{text}';
            }}
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
        return el;
        }}
        replaceValue('{class_name}', '{text}');
        """

        # js_code += f"""
        # setTimeout(function() {{
        #     var button = document.querySelector('{stop_button_class}'){parent_element};
        #     if (button) {{
        #         button.click();
        #     }}
        # }}, 100);
        # """


        js_code += f"""
        setTimeout(function() {{
            if ({skip_response_icon_check}) {{
                var button = document.querySelector('{stop_button_class}'){parent_element};
                if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {{
                    button.click();
                }}
            }}
        }}, 100);
        """

        # if config["submit_text"] or click:
        js_code += f"""
        setTimeout(function() {{
            var submitButton = document.querySelector('{button_class}');
            if (submitButton && !submitButton.disabled && submitButton.getAttribute('aria-disabled') !== 'true') {{
                submitButton.click();
            }}
        }}, 200);
        """

        # if config["submit_text"] or click :
        #     js_code += f"""
        #     setTimeout(function() {{
        #         var submitButton = document.querySelector('{button_class}');
        #         if (submitButton) {{
        #             submitButton.click();
        #         }}
        #     }}, 200);
        #     """

        self.webview.page().runJavaScript(js_code, self.js_callback)


    def js_callback(self, result):
        print("JavaScript result: ", result)




chatGPTdockWidget = None
dock_content = None

def Web_view(name, url):
    global chatGPTdockWidget
    global dock_content
    global web_shortcut

    if chatGPTdockWidget is not None:
        if chatGPTdockWidget.isVisible():
            chatGPTdockWidget.hide()
            mw.web.setFocus()
        else:
            chatGPTdockWidget.show()
            chatGPTdockWidget.setFocus()
            dock_content.get_field_text()
        return

    dock_content = ResizableWebView(name, url, mw)

    chatGPTdockWidget = QDockWidget(mw)
    chatGPTdockWidget.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
    chatGPTdockWidget.setTitleBarWidget(QWidget()) # ﾀｲﾄﾙﾊﾞｰを空のｳｨｼﾞｪｯﾄに置き換え
    chatGPTdockWidget.setObjectName(name)
    chatGPTdockWidget.setWidget(dock_content)
    mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, chatGPTdockWidget)

    config = mw.addonManager.getConfig(__name__)
    Enter_Short_cut_Key = config["Enter_Short_cut_Key"]

    # web_shortcut = QShortcut(QKeySequence(Enter_Short_cut_Key), dock_content)
    # web_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)

    # def execute_current_item():
    #     # JavaScriptを使用して､現在選択されている項目を取得し､その項目を実行
    #     dock_content.webview.page().runJavaScript("""
    #         var activeElement = document.activeElement;
    #         if (activeElement) {
    #             activeElement.click();
    #         }
    #     """)
    # web_shortcut.activated.connect(execute_current_item)

    def send_shortcut():
        print("send_shortcut")
        config = mw.addonManager.getConfig(__name__)
        now_AI_type = config["now_AI_type"]
        if now_AI_type == CHAT_GPT:
            button_class = 'button[data-testid="send-button"]'
        elif now_AI_type == GOOGLE_BARD:
            button_class = ".send-button"
        else:
            return
        js_code = f"""
        setTimeout(function() {{
            var submitButton = document.querySelector('{button_class}');
            if (submitButton) {{
                submitButton.click();
            }}
        }}, 200);
        """
        dock_content.webview.page().runJavaScript(js_code, dock_content.js_callback)
    # web_shortcut.activated.connect(send_shortcut)

    menu = QAction(name, mw)
    menu.triggered.connect(send_shortcut)
    mw.form.menuTools.addAction(menu)
    menu.setShortcut(QKeySequence(Enter_Short_cut_Key))
    web_shortcut = menu










def close_dock_widget(addonmanager, name, *args, **kwargs):
    print(addonmanager, name)
    print(__name__)
    if name == __name__.split(".")[0]:
        print("AnkiTerminator : Close before add-on update")

        global chatGPTdockWidget
        global dock_content

        if isinstance(chatGPTdockWidget, QDockWidget):
            print("isinstance : chatGPTdockWidget")
            if isinstance(dock_content, ResizableWebView):
                print("isinstance : dock_content")
                dock_content.close_cookie_profile()
                dock_content.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
                dock_content.close()
                dock_content.deleteLater()
                dock_content = None

            else:
                print("not isinstance : dock_content")

            chatGPTdockWidget.close()
            chatGPTdockWidget.deleteLater()
            chatGPTdockWidget = None

            loop = QEventLoop()
            QTimer.singleShot(1000, loop.quit)
            loop.exec()
            QCoreApplication.processEvents()

        else:
            print("not isinstance : chatGPTdockWidget")
    print("Done : close_dock_widget")



gui_hooks.addon_manager_will_install_addon.remove(close_dock_widget)
gui_hooks.addon_manager_will_install_addon.append(close_dock_widget)

from .config.BGM_player import pyg_play_sound

def get_path(name):
    addon_path = dirname(__file__)
    parentFoldere = SOUND_SYSTEM
    config_folder = CONFIG_FOLDER
    audio_folder = join(addon_path,config_folder,parentFoldere, name)
    return audio_folder

def PYGsound(sound_name,volume=None):
    config = mw.addonManager.getConfig(__name__)
    if not volume == None:
        EffectVolume = volume
    else:
        EffectVolume = config["EffectVolume"]
    pyg_play_sound(get_path(sound_name), EffectVolume,False,True)
