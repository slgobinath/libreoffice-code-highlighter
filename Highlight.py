from pygments import styles
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_all_styles


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
                smt = ''
                try:
                    # Libreoffice Writer and Calc have the Description attribute
                    smt = box.Description.lower()
                except Exception as err:
                    smt = ''

                if not smt:
                    try:
                        # Libreoffice Impress has Style attribute not Description
                        smt = box.Style.getName().lower()
                    except Exception as err:
                        smt = ''

                if smt:
                    if 'code-' in smt:
                        # Remove the prefix code-
                        lang = smt.replace('code-', '')
                        # Default style
                        style = 'default'

                        # Check for explicit style. lang-style
                        if '-' in lang:
                            temp = lang.split('-')
                            lang = temp[0]
                            style = temp[1]

                            # Check whether the style is supported by pygments
                            supported_styles = list(get_all_styles())
                            if(style not in supported_styles):
                                # If the given style is not supported, use the default style
                                style = 'default'

                        highlight_code(style, lang, box)


def rgb(r, g, b):
    return (r & 255) << 16 | (g & 255) << 8 | (b & 255)


def to_rgbint(hex_str):
    if hex_str:
        r = int(hex_str[:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:], 16)
        return rgb(r, g, b)
    return rgb(0, 0, 0)


def highlight_code(style, lang, codebox):
    code = codebox.String
    lexer = get_lexer_by_name(lang)
    cursor = codebox.createTextCursor()
    style = styles.get_style_by_name(style)
    cursor.gotoStart(False)
    for tok_type, tok_value in lexer.get_tokens(code):
        cursor.goRight(len(tok_value), True)  # selects the token's text
        cursor.CharColor = to_rgbint(style.style_for_token(tok_type)['color'])
        cursor.goRight(0, False)  # deselects the selected text


g_exportedScripts = (highlight_source_code,)
