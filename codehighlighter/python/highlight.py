# Code Highligher is a LibreOffice extension to highlight code snippets
# over 350 languages.

# Copyright (C) 2017  Gobinath

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import uno
from com.sun.star.awt.Key import RETURN as KEY_RETURN
from com.sun.star.drawing.FillStyle import NONE as FS_NONE, SOLID as FS_SOLID
from com.sun.star.awt.FontSlant import NONE as SL_NONE, ITALIC as SL_ITALIC
from com.sun.star.awt.FontWeight import NORMAL as W_NORMAL, BOLD as W_BOLD

from com.sun.star.beans import PropertyValue

from pygments import styles
from pygments.lexers import get_all_lexers
from pygments.lexers import get_lexer_by_name
from pygments.lexers import guess_lexer
from pygments.styles import get_all_styles
import pygments.util
import os


def rgb(r, g, b):
    return (r & 255) << 16 | (g & 255) << 8 | (b & 255)


def to_rgbint(hex_str):
    if hex_str:
        # the background color starts with #, the foreground colors don't
        hex_str = hex_str.lstrip('#')
        r = int(hex_str[:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:], 16)
        return rgb(r, g, b)
    return rgb(0, 0, 0)


def log(msg):
    with open("/tmp/code-highlighter.log", "a") as text_file:
        text_file.write(str(msg) + "\r\n\r\n")


def create_dialog():
    # get_all_lexers() returns:
    # (longname, tuple of aliases, tuple of filename patterns, tuple of mimetypes)
    all_lexers = [lex[0] for lex in get_all_lexers()]
    all_lexer_aliases = [lex[0] for lex in get_all_lexers()]
    for lex in get_all_lexers():
        all_lexer_aliases.extend(list(lex[1]))
    all_styles = list(get_all_styles())

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    dialog_provider = smgr.createInstance("com.sun.star.awt.DialogProvider")
    dialog = dialog_provider.createDialog("vnd.sun.star.extension://javahelps.codehighlighter/dialogs/CodeHighlighter.xdl")

    cfg = smgr.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider', ctx)
    prop = PropertyValue()
    prop.Name = 'nodepath'
    prop.Value = '/ooo.ext.code-highlighter.Registry/Settings'
    cfg_access = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationUpdateAccess', (prop,))

    cb_lang = dialog.getControl('cb_lang')
    cb_style = dialog.getControl('cb_style')
    check_col_bg = dialog.getControl('check_col_bg')

    cb_lang.addItem('automatic', 0)
    cb_lang.Text = cfg_access.getPropertyValue('Language')
    for i, lex in enumerate(all_lexers):
        cb_lang.addItem(lex, i+1)

    style = cfg_access.getPropertyValue('Style')
    if style in all_styles:
        cb_style.Text = style
    for i, style in enumerate(all_styles):
        cb_style.addItem(style, i)

    check_col_bg.State = int(cfg_access.getPropertyValue('ColorizeBackground'))

    dialog.setVisible(True)
    # 0: canceled, 1: OK
    if dialog.execute() == 0:
        return

    lang = cb_lang.Text
    style = cb_style.Text
    colorize_bg = check_col_bg.State
    if lang == 'automatic':
        lang = None
    assert lang == None or (lang in all_lexer_aliases), 'no valid language: ' + lang
    assert style in all_styles, 'no valid style: ' + style

    cfg_access.setPropertyValue('Style', style)
    cfg_access.setPropertyValue('Language', lang or 'automatic')
    cfg_access.setPropertyValue('ColorizeBackground', str(colorize_bg))
    cfg_access.commitChanges()

    highlightSourceCode(lang, style, colorize_bg != 0)


def apply_previous_settings():
    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    cfg = smgr.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider', ctx)
    prop = PropertyValue()
    prop.Name = 'nodepath'
    prop.Value = '/ooo.ext.code-highlighter.Registry/Settings'
    cfg_access = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationAccess', (prop,))

    lang = cfg_access.getPropertyValue('Language')
    style = cfg_access.getPropertyValue('Style')
    colorize_bg = int(cfg_access.getPropertyValue('ColorizeBackground'))

    if lang == 'automatic':
        lang = None

    highlightSourceCode(lang, style, colorize_bg != 0)


def key_pressed(event):
    if event.KeyCode == KEY_RETURN:
        # handle 'return key press' like OK button
        dialog = event.Source.getContext()
        dialog.endDialog(1)

def highlightSourceCode(lang, style, colorize_bg=False):
    style = styles.get_style_by_name(style)
    bg_color = style.background_color if colorize_bg else None

    ctx = XSCRIPTCONTEXT
    doc = ctx.getDocument()
    # Get the selected item
    selected_item = doc.getCurrentController().getSelection()
    if hasattr(selected_item, 'getCount'):
        for item_idx in range(selected_item.getCount()):
            code_block = selected_item.getByIndex(item_idx)
            if 'com.sun.star.drawing.Text' in code_block.SupportedServiceNames:
                # TextBox
                # highlight_code(style, lang, code_block)
                code_block.FillStyle = FS_NONE
                if bg_color:
                    code_block.FillStyle = FS_SOLID
                    code_block.FillColor = to_rgbint(bg_color)
                code = code_block.String
                cursor = code_block.createTextCursor()
                cursor.gotoStart(False)
            else:
                # Plain text
                # highlight_code_string(style, lang, code_block)
                if bg_color:
                    code_block.ParaBackColor = to_rgbint(bg_color)
                code = code_block.getString()
                cursor = code_block.getText().createTextCursorByRange(code_block)
                cursor.goLeft(0, False)
            highlight_code(code, cursor, lang, style)
    elif hasattr(selected_item, 'SupportedServiceNames') and 'com.sun.star.text.TextCursor' in selected_item.SupportedServiceNames:
        # LO Impress text selection
        code_block = selected_item
        code = code_block.getString()
        cursor = code_block.getText().createTextCursorByRange(code_block)
        cursor.goLeft(0, False)
        highlight_code(code, cursor, lang, style)


def highlight_code(code, cursor, lang, style):
    if lang is None:
        lexer = guess_lexer(code)
    else:
        try:
            lexer = get_lexer_by_name(lang)
        except pygments.util.ClassNotFound:
            # get_lexer_by_name() only checks aliases, not the actual longname
            for lex in get_all_lexers():
                if lex[0] == lang:
                    # found the longname, use the first alias
                    lexer = get_lexer_by_name(lex[1][0])
                    break
            else:
                raise
    for tok_type, tok_value in lexer.get_tokens(code):
        cursor.goRight(len(tok_value), True)  # selects the token's text
        try:
            tok_style = style.style_for_token(tok_type)
            cursor.CharColor = to_rgbint(tok_style['color'])
            cursor.CharWeight = W_BOLD if tok_style['bold'] else W_NORMAL
            cursor.CharPosture = SL_ITALIC if tok_style['italic'] else SL_NONE
        except:
            pass
        finally:
            cursor.goRight(0, False)  # deselects the selected text


# export these, so they can be used for key bindings
g_exportedScripts = (create_dialog, apply_previous_settings)
