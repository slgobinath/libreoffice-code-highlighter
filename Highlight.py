from pygments import styles
from pygments.lexers import (get_lexer_by_name)


def highlight_source_code(*args):
    ctx = XSCRIPTCONTEXT
    doc = ctx.getDocument()
    # Get the selected item
    selected_item = doc.getCurrentController().getSelection()
    # Validate that the selected item is a Shape
    if 'com.sun.star.drawing.Shapes' in selected_item.getSupportedServiceNames():
        for item_idx in range(selected_item.getCount()):
            # Get the textbox from the shape
            box = selected_item.getByIndex(item_idx)
            if 'com.sun.star.drawing.Text' in box.SupportedServiceNames:
                # Extract the language name.
                lang = ''
                # For Libreoffice Writer, check the Description attribute of the textbox
                try:
                    if box.Description.lower().find("code-") == 0:
                        lang = box.Description.lower().replace("code-", "")
                except Exception as err:
                    lang = ''

                # For Libreoffice Impress, check the Style attribute of the textbox
                if not lang:
                    try:
                        if box.Style.getName().lower().find("code-") == 0:
                            lang = box.Style.getName().lower().replace("code-", "")
                    except Exception as err:
                        lang = ''

                if lang:
                    highlight_code(lang, box)


def rgb(r, g, b):
    return (r & 255) << 16 | (g & 255) << 8 | (b & 255)


def to_rgbint(hex_str):
    if hex_str:
        r = int(hex_str[:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:], 16)
        return rgb(r, g, b)
    return rgb(0, 0, 0)


def highlight_code(lang, codebox):
    code = codebox.String
    lexer = get_lexer_by_name(lang)
    cursor = codebox.createTextCursor()
    style = styles.get_style_by_name('default')
    cursor.gotoStart(False)
    for tok_type, tok_value in lexer.get_tokens(code):
        cursor.goRight(len(tok_value), True)  # selects the token's text
        cursor.CharColor = to_rgbint(style.style_for_token(tok_type)['color'])
        cursor.goRight(0, False)  # deselects the selected text


g_exportedScripts = (highlight_source_code,)
