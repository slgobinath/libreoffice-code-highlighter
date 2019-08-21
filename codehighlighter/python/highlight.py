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


def highlight_automatic_default(*args):
    highlightSourceCode(None, 'default')


def highlight_abap_default(*args):
    highlightSourceCode('abap', 'default')


def highlight_abnf_default(*args):
    highlightSourceCode('abnf', 'default')


def highlight_as3_default(*args):
    highlightSourceCode('as3', 'default')


def highlight_as_default(*args):
    highlightSourceCode('as', 'default')


def highlight_ada_default(*args):
    highlightSourceCode('ada', 'default')


def highlight_adl_default(*args):
    highlightSourceCode('adl', 'default')


def highlight_agda_default(*args):
    highlightSourceCode('agda', 'default')


def highlight_aheui_default(*args):
    highlightSourceCode('aheui', 'default')


def highlight_alloy_default(*args):
    highlightSourceCode('alloy', 'default')


def highlight_at_default(*args):
    highlightSourceCode('at', 'default')


def highlight_ampl_default(*args):
    highlightSourceCode('ampl', 'default')


def highlight_ng2_default(*args):
    highlightSourceCode('ng2', 'default')


def highlight_antlr_default(*args):
    highlightSourceCode('antlr', 'default')


def highlight_apacheconf_default(*args):
    highlightSourceCode('apacheconf', 'default')


def highlight_apl_default(*args):
    highlightSourceCode('apl', 'default')


def highlight_applescript_default(*args):
    highlightSourceCode('applescript', 'default')


def highlight_arduino_default(*args):
    highlightSourceCode('arduino', 'default')


def highlight_aspectj_default(*args):
    highlightSourceCode('aspectj', 'default')


def highlight_aspx_cs_default(*args):
    highlightSourceCode('aspx-cs', 'default')


def highlight_aspx_vb_default(*args):
    highlightSourceCode('aspx-vb', 'default')


def highlight_asy_default(*args):
    highlightSourceCode('asy', 'default')


def highlight_ahk_default(*args):
    highlightSourceCode('ahk', 'default')


def highlight_autoit_default(*args):
    highlightSourceCode('autoit', 'default')


def highlight_awk_default(*args):
    highlightSourceCode('awk', 'default')


def highlight_basemake_default(*args):
    highlightSourceCode('basemake', 'default')


def highlight_console_default(*args):
    highlightSourceCode('console', 'default')


def highlight_bash_default(*args):
    highlightSourceCode('bash', 'default')


def highlight_bat_default(*args):
    highlightSourceCode('bat', 'default')


def highlight_bbcode_default(*args):
    highlightSourceCode('bbcode', 'default')


def highlight_bc_default(*args):
    highlightSourceCode('bc', 'default')


def highlight_befunge_default(*args):
    highlightSourceCode('befunge', 'default')


def highlight_bib_default(*args):
    highlightSourceCode('bib', 'default')


def highlight_blitzbasic_default(*args):
    highlightSourceCode('blitzbasic', 'default')


def highlight_blitzmax_default(*args):
    highlightSourceCode('blitzmax', 'default')


def highlight_bnf_default(*args):
    highlightSourceCode('bnf', 'default')


def highlight_boo_default(*args):
    highlightSourceCode('boo', 'default')


def highlight_boogie_default(*args):
    highlightSourceCode('boogie', 'default')


def highlight_brainfuck_default(*args):
    highlightSourceCode('brainfuck', 'default')


def highlight_bro_default(*args):
    highlightSourceCode('bro', 'default')


def highlight_bst_default(*args):
    highlightSourceCode('bst', 'default')


def highlight_bugs_default(*args):
    highlightSourceCode('bugs', 'default')


def highlight_csharp_default(*args):
    highlightSourceCode('csharp', 'default')


def highlight_c_objdump_default(*args):
    highlightSourceCode('c-objdump', 'default')


def highlight_c_default(*args):
    highlightSourceCode('c', 'default')


def highlight_cpp_default(*args):
    highlightSourceCode('cpp', 'default')


def highlight_ca65_default(*args):
    highlightSourceCode('ca65', 'default')


def highlight_cadl_default(*args):
    highlightSourceCode('cadl', 'default')


def highlight_camkes_default(*args):
    highlightSourceCode('camkes', 'default')


def highlight_capnp_default(*args):
    highlightSourceCode('capnp', 'default')


def highlight_capdl_default(*args):
    highlightSourceCode('capdl', 'default')


def highlight_cbmbas_default(*args):
    highlightSourceCode('cbmbas', 'default')


def highlight_ceylon_default(*args):
    highlightSourceCode('ceylon', 'default')


def highlight_cfengine3_default(*args):
    highlightSourceCode('cfengine3', 'default')


def highlight_cfs_default(*args):
    highlightSourceCode('cfs', 'default')


def highlight_chai_default(*args):
    highlightSourceCode('chai', 'default')


def highlight_chapel_default(*args):
    highlightSourceCode('chapel', 'default')


def highlight_cheetah_default(*args):
    highlightSourceCode('cheetah', 'default')


def highlight_cirru_default(*args):
    highlightSourceCode('cirru', 'default')


def highlight_clay_default(*args):
    highlightSourceCode('clay', 'default')


def highlight_clean_default(*args):
    highlightSourceCode('clean', 'default')


def highlight_clojure_default(*args):
    highlightSourceCode('clojure', 'default')


def highlight_clojurescript_default(*args):
    highlightSourceCode('clojurescript', 'default')


def highlight_cmake_default(*args):
    highlightSourceCode('cmake', 'default')


def highlight_cobol_default(*args):
    highlightSourceCode('cobol', 'default')


def highlight_cobolfree_default(*args):
    highlightSourceCode('cobolfree', 'default')


def highlight_coffee_script_default(*args):
    highlightSourceCode('coffee-script', 'default')


def highlight_cfc_default(*args):
    highlightSourceCode('cfc', 'default')


def highlight_cfm_default(*args):
    highlightSourceCode('cfm', 'default')


def highlight_common_lisp_default(*args):
    highlightSourceCode('common-lisp', 'default')


def highlight_componentpascal_default(*args):
    highlightSourceCode('componentpascal', 'default')


def highlight_coq_default(*args):
    highlightSourceCode('coq', 'default')


def highlight_cpp_objdump_default(*args):
    highlightSourceCode('cpp-objdump', 'default')


def highlight_cpsa_default(*args):
    highlightSourceCode('cpsa', 'default')


def highlight_crmsh_default(*args):
    highlightSourceCode('crmsh', 'default')


def highlight_croc_default(*args):
    highlightSourceCode('croc', 'default')


def highlight_cryptol_default(*args):
    highlightSourceCode('cryptol', 'default')


def highlight_cr_default(*args):
    highlightSourceCode('cr', 'default')


def highlight_csound_document_default(*args):
    highlightSourceCode('csound-document', 'default')


def highlight_csound_default(*args):
    highlightSourceCode('csound', 'default')


def highlight_csound_score_default(*args):
    highlightSourceCode('csound-score', 'default')


def highlight_css_default(*args):
    highlightSourceCode('css', 'default')


def highlight_cuda_default(*args):
    highlightSourceCode('cuda', 'default')


def highlight_cypher_default(*args):
    highlightSourceCode('cypher', 'default')


def highlight_cython_default(*args):
    highlightSourceCode('cython', 'default')


def highlight_d_objdump_default(*args):
    highlightSourceCode('d-objdump', 'default')


def highlight_d_default(*args):
    highlightSourceCode('d', 'default')


def highlight_dpatch_default(*args):
    highlightSourceCode('dpatch', 'default')


def highlight_dart_default(*args):
    highlightSourceCode('dart', 'default')


def highlight_control_default(*args):
    highlightSourceCode('control', 'default')


def highlight_sourceslist_default(*args):
    highlightSourceCode('sourceslist', 'default')


def highlight_delphi_default(*args):
    highlightSourceCode('delphi', 'default')


def highlight_dg_default(*args):
    highlightSourceCode('dg', 'default')


def highlight_diff_default(*args):
    highlightSourceCode('diff', 'default')


def highlight_django_default(*args):
    highlightSourceCode('django', 'default')


def highlight_docker_default(*args):
    highlightSourceCode('docker', 'default')


def highlight_dtd_default(*args):
    highlightSourceCode('dtd', 'default')


def highlight_duel_default(*args):
    highlightSourceCode('duel', 'default')


def highlight_dylan_console_default(*args):
    highlightSourceCode('dylan-console', 'default')


def highlight_dylan_default(*args):
    highlightSourceCode('dylan', 'default')


def highlight_dylan_lid_default(*args):
    highlightSourceCode('dylan-lid', 'default')


def highlight_earl_grey_default(*args):
    highlightSourceCode('earl-grey', 'default')


def highlight_easytrieve_default(*args):
    highlightSourceCode('easytrieve', 'default')


def highlight_ebnf_default(*args):
    highlightSourceCode('ebnf', 'default')


def highlight_ec_default(*args):
    highlightSourceCode('ec', 'default')


def highlight_ecl_default(*args):
    highlightSourceCode('ecl', 'default')


def highlight_eiffel_default(*args):
    highlightSourceCode('eiffel', 'default')


def highlight_iex_default(*args):
    highlightSourceCode('iex', 'default')


def highlight_elixir_default(*args):
    highlightSourceCode('elixir', 'default')


def highlight_elm_default(*args):
    highlightSourceCode('elm', 'default')


def highlight_emacs_default(*args):
    highlightSourceCode('emacs', 'default')


def highlight_ragel_em_default(*args):
    highlightSourceCode('ragel-em', 'default')


def highlight_erb_default(*args):
    highlightSourceCode('erb', 'default')


def highlight_erl_default(*args):
    highlightSourceCode('erl', 'default')


def highlight_erlang_default(*args):
    highlightSourceCode('erlang', 'default')


def highlight_evoque_default(*args):
    highlightSourceCode('evoque', 'default')


def highlight_ezhil_default(*args):
    highlightSourceCode('ezhil', 'default')


def highlight_factor_default(*args):
    highlightSourceCode('factor', 'default')


def highlight_fancy_default(*args):
    highlightSourceCode('fancy', 'default')


def highlight_fan_default(*args):
    highlightSourceCode('fan', 'default')


def highlight_felix_default(*args):
    highlightSourceCode('felix', 'default')


def highlight_fish_default(*args):
    highlightSourceCode('fish', 'default')


def highlight_flatline_default(*args):
    highlightSourceCode('flatline', 'default')


def highlight_forth_default(*args):
    highlightSourceCode('forth', 'default')


def highlight_fortran_default(*args):
    highlightSourceCode('fortran', 'default')


def highlight_fortranfixed_default(*args):
    highlightSourceCode('fortranfixed', 'default')


def highlight_foxpro_default(*args):
    highlightSourceCode('foxpro', 'default')


def highlight_fsharp_default(*args):
    highlightSourceCode('fsharp', 'default')


def highlight_gap_default(*args):
    highlightSourceCode('gap', 'default')


def highlight_gas_default(*args):
    highlightSourceCode('gas', 'default')


def highlight_genshitext_default(*args):
    highlightSourceCode('genshitext', 'default')


def highlight_genshi_default(*args):
    highlightSourceCode('genshi', 'default')


def highlight_pot_default(*args):
    highlightSourceCode('pot', 'default')


def highlight_cucumber_default(*args):
    highlightSourceCode('cucumber', 'default')


def highlight_glsl_default(*args):
    highlightSourceCode('glsl', 'default')


def highlight_gnuplot_default(*args):
    highlightSourceCode('gnuplot', 'default')


def highlight_go_default(*args):
    highlightSourceCode('go', 'default')


def highlight_golo_default(*args):
    highlightSourceCode('golo', 'default')


def highlight_gooddata_cl_default(*args):
    highlightSourceCode('gooddata-cl', 'default')


def highlight_gst_default(*args):
    highlightSourceCode('gst', 'default')


def highlight_gosu_default(*args):
    highlightSourceCode('gosu', 'default')


def highlight_groff_default(*args):
    highlightSourceCode('groff', 'default')


def highlight_groovy_default(*args):
    highlightSourceCode('groovy', 'default')


def highlight_haml_default(*args):
    highlightSourceCode('haml', 'default')


def highlight_handlebars_default(*args):
    highlightSourceCode('handlebars', 'default')


def highlight_haskell_default(*args):
    highlightSourceCode('haskell', 'default')


def highlight_hx_default(*args):
    highlightSourceCode('hx', 'default')


def highlight_hexdump_default(*args):
    highlightSourceCode('hexdump', 'default')


def highlight_hsail_default(*args):
    highlightSourceCode('hsail', 'default')


def highlight_html_default(*args):
    highlightSourceCode('html', 'default')


def highlight_http_default(*args):
    highlightSourceCode('http', 'default')


def highlight_haxeml_default(*args):
    highlightSourceCode('haxeml', 'default')


def highlight_hylang_default(*args):
    highlightSourceCode('hylang', 'default')


def highlight_hybris_default(*args):
    highlightSourceCode('hybris', 'default')


def highlight_idl_default(*args):
    highlightSourceCode('idl', 'default')


def highlight_idris_default(*args):
    highlightSourceCode('idris', 'default')


def highlight_igor_default(*args):
    highlightSourceCode('igor', 'default')


def highlight_i6t_default(*args):
    highlightSourceCode('i6t', 'default')


def highlight_inform6_default(*args):
    highlightSourceCode('inform6', 'default')


def highlight_inform7_default(*args):
    highlightSourceCode('inform7', 'default')


def highlight_ini_default(*args):
    highlightSourceCode('ini', 'default')


def highlight_io_default(*args):
    highlightSourceCode('io', 'default')


def highlight_ioke_default(*args):
    highlightSourceCode('ioke', 'default')


def highlight_irc_default(*args):
    highlightSourceCode('irc', 'default')


def highlight_isabelle_default(*args):
    highlightSourceCode('isabelle', 'default')


def highlight_j_default(*args):
    highlightSourceCode('j', 'default')


def highlight_jags_default(*args):
    highlightSourceCode('jags', 'default')


def highlight_jasmin_default(*args):
    highlightSourceCode('jasmin', 'default')


def highlight_jsp_default(*args):
    highlightSourceCode('jsp', 'default')


def highlight_java_default(*args):
    highlightSourceCode('java', 'default')


def highlight_js_default(*args):
    highlightSourceCode('js', 'default')


def highlight_jcl_default(*args):
    highlightSourceCode('jcl', 'default')


def highlight_jsgf_default(*args):
    highlightSourceCode('jsgf', 'default')


def highlight_jsonld_default(*args):
    highlightSourceCode('jsonld', 'default')


def highlight_json_default(*args):
    highlightSourceCode('json', 'default')


def highlight_json_object_default(*args):
    highlightSourceCode('json-object', 'default')


def highlight_jlcon_default(*args):
    highlightSourceCode('jlcon', 'default')


def highlight_julia_default(*args):
    highlightSourceCode('julia', 'default')


def highlight_juttle_default(*args):
    highlightSourceCode('juttle', 'default')


def highlight_kal_default(*args):
    highlightSourceCode('kal', 'default')


def highlight_kconfig_default(*args):
    highlightSourceCode('kconfig', 'default')


def highlight_koka_default(*args):
    highlightSourceCode('koka', 'default')


def highlight_kotlin_default(*args):
    highlightSourceCode('kotlin', 'default')


def highlight_lasso_default(*args):
    highlightSourceCode('lasso', 'default')


def highlight_lean_default(*args):
    highlightSourceCode('lean', 'default')


def highlight_less_default(*args):
    highlightSourceCode('less', 'default')


def highlight_lighty_default(*args):
    highlightSourceCode('lighty', 'default')


def highlight_limbo_default(*args):
    highlightSourceCode('limbo', 'default')


def highlight_liquid_default(*args):
    highlightSourceCode('liquid', 'default')


def highlight_lagda_default(*args):
    highlightSourceCode('lagda', 'default')


def highlight_lcry_default(*args):
    highlightSourceCode('lcry', 'default')


def highlight_lhs_default(*args):
    highlightSourceCode('lhs', 'default')


def highlight_lidr_default(*args):
    highlightSourceCode('lidr', 'default')


def highlight_live_script_default(*args):
    highlightSourceCode('live-script', 'default')


def highlight_llvm_default(*args):
    highlightSourceCode('llvm', 'default')


def highlight_logos_default(*args):
    highlightSourceCode('logos', 'default')


def highlight_logtalk_default(*args):
    highlightSourceCode('logtalk', 'default')


def highlight_lsl_default(*args):
    highlightSourceCode('lsl', 'default')


def highlight_lua_default(*args):
    highlightSourceCode('lua', 'default')


def highlight_make_default(*args):
    highlightSourceCode('make', 'default')


def highlight_mako_default(*args):
    highlightSourceCode('mako', 'default')


def highlight_maql_default(*args):
    highlightSourceCode('maql', 'default')


def highlight_md_default(*args):
    highlightSourceCode('md', 'default')


def highlight_mask_default(*args):
    highlightSourceCode('mask', 'default')


def highlight_mason_default(*args):
    highlightSourceCode('mason', 'default')


def highlight_mathematica_default(*args):
    highlightSourceCode('mathematica', 'default')


def highlight_matlabsession_default(*args):
    highlightSourceCode('matlabsession', 'default')


def highlight_matlab_default(*args):
    highlightSourceCode('matlab', 'default')


def highlight_minid_default(*args):
    highlightSourceCode('minid', 'default')


def highlight_modelica_default(*args):
    highlightSourceCode('modelica', 'default')


def highlight_modula2_default(*args):
    highlightSourceCode('modula2', 'default')


def highlight_trac_wiki_default(*args):
    highlightSourceCode('trac-wiki', 'default')


def highlight_monkey_default(*args):
    highlightSourceCode('monkey', 'default')


def highlight_monte_default(*args):
    highlightSourceCode('monte', 'default')


def highlight_moocode_default(*args):
    highlightSourceCode('moocode', 'default')


def highlight_moon_default(*args):
    highlightSourceCode('moon', 'default')


def highlight_mozhashpreproc_default(*args):
    highlightSourceCode('mozhashpreproc', 'default')


def highlight_mozpercentpreproc_default(*args):
    highlightSourceCode('mozpercentpreproc', 'default')


def highlight_mql_default(*args):
    highlightSourceCode('mql', 'default')


def highlight_mscgen_default(*args):
    highlightSourceCode('mscgen', 'default')


def highlight_doscon_default(*args):
    highlightSourceCode('doscon', 'default')


def highlight_mupad_default(*args):
    highlightSourceCode('mupad', 'default')


def highlight_mxml_default(*args):
    highlightSourceCode('mxml', 'default')


def highlight_myghty_default(*args):
    highlightSourceCode('myghty', 'default')


def highlight_mysql_default(*args):
    highlightSourceCode('mysql', 'default')


def highlight_nasm_default(*args):
    highlightSourceCode('nasm', 'default')


def highlight_ncl_default(*args):
    highlightSourceCode('ncl', 'default')


def highlight_nemerle_default(*args):
    highlightSourceCode('nemerle', 'default')


def highlight_nesc_default(*args):
    highlightSourceCode('nesc', 'default')


def highlight_newlisp_default(*args):
    highlightSourceCode('newlisp', 'default')


def highlight_newspeak_default(*args):
    highlightSourceCode('newspeak', 'default')


def highlight_nginx_default(*args):
    highlightSourceCode('nginx', 'default')


def highlight_nim_default(*args):
    highlightSourceCode('nim', 'default')


def highlight_nit_default(*args):
    highlightSourceCode('nit', 'default')


def highlight_nixos_default(*args):
    highlightSourceCode('nixos', 'default')


def highlight_nsis_default(*args):
    highlightSourceCode('nsis', 'default')


def highlight_numpy_default(*args):
    highlightSourceCode('numpy', 'default')


def highlight_nusmv_default(*args):
    highlightSourceCode('nusmv', 'default')


def highlight_objdump_nasm_default(*args):
    highlightSourceCode('objdump-nasm', 'default')


def highlight_objdump_default(*args):
    highlightSourceCode('objdump', 'default')


def highlight_objective_c_default(*args):
    highlightSourceCode('objective-c', 'default')


def highlight_objective_j_default(*args):
    highlightSourceCode('objective-j', 'default')


def highlight_ocaml_default(*args):
    highlightSourceCode('ocaml', 'default')


def highlight_octave_default(*args):
    highlightSourceCode('octave', 'default')


def highlight_odin_default(*args):
    highlightSourceCode('odin', 'default')


def highlight_ooc_default(*args):
    highlightSourceCode('ooc', 'default')


def highlight_opa_default(*args):
    highlightSourceCode('opa', 'default')


def highlight_openedge_default(*args):
    highlightSourceCode('openedge', 'default')


def highlight_pacmanconf_default(*args):
    highlightSourceCode('pacmanconf', 'default')


def highlight_pan_default(*args):
    highlightSourceCode('pan', 'default')


def highlight_parasail_default(*args):
    highlightSourceCode('parasail', 'default')


def highlight_pawn_default(*args):
    highlightSourceCode('pawn', 'default')


def highlight_perl6_default(*args):
    highlightSourceCode('perl6', 'default')


def highlight_perl_default(*args):
    highlightSourceCode('perl', 'default')


def highlight_php_default(*args):
    highlightSourceCode('php', 'default')


def highlight_pig_default(*args):
    highlightSourceCode('pig', 'default')


def highlight_pike_default(*args):
    highlightSourceCode('pike', 'default')


def highlight_pkgconfig_default(*args):
    highlightSourceCode('pkgconfig', 'default')


def highlight_plpgsql_default(*args):
    highlightSourceCode('plpgsql', 'default')


def highlight_psql_default(*args):
    highlightSourceCode('psql', 'default')


def highlight_postgresql_default(*args):
    highlightSourceCode('postgresql', 'default')


def highlight_postscript_default(*args):
    highlightSourceCode('postscript', 'default')


def highlight_pov_default(*args):
    highlightSourceCode('pov', 'default')


def highlight_ps1con_default(*args):
    highlightSourceCode('ps1con', 'default')


def highlight_powershell_default(*args):
    highlightSourceCode('powershell', 'default')


def highlight_praat_default(*args):
    highlightSourceCode('praat', 'default')


def highlight_prolog_default(*args):
    highlightSourceCode('prolog', 'default')


def highlight_properties_default(*args):
    highlightSourceCode('properties', 'default')


def highlight_protobuf_default(*args):
    highlightSourceCode('protobuf', 'default')


def highlight_pug_default(*args):
    highlightSourceCode('pug', 'default')


def highlight_puppet_default(*args):
    highlightSourceCode('puppet', 'default')


def highlight_pypylog_default(*args):
    highlightSourceCode('pypylog', 'default')


def highlight_py3tb_default(*args):
    highlightSourceCode('py3tb', 'default')


def highlight_python3_default(*args):
    highlightSourceCode('python3', 'default')


def highlight_pycon_default(*args):
    highlightSourceCode('pycon', 'default')


def highlight_pytb_default(*args):
    highlightSourceCode('pytb', 'default')


def highlight_python_default(*args):
    highlightSourceCode('python', 'default')


def highlight_qbasic_default(*args):
    highlightSourceCode('qbasic', 'default')


def highlight_qml_default(*args):
    highlightSourceCode('qml', 'default')


def highlight_qvto_default(*args):
    highlightSourceCode('qvto', 'default')


def highlight_racket_default(*args):
    highlightSourceCode('racket', 'default')


def highlight_ragel_c_default(*args):
    highlightSourceCode('ragel-c', 'default')


def highlight_ragel_cpp_default(*args):
    highlightSourceCode('ragel-cpp', 'default')


def highlight_ragel_d_default(*args):
    highlightSourceCode('ragel-d', 'default')


def highlight_ragel_java_default(*args):
    highlightSourceCode('ragel-java', 'default')


def highlight_ragel_objc_default(*args):
    highlightSourceCode('ragel-objc', 'default')


def highlight_ragel_ruby_default(*args):
    highlightSourceCode('ragel-ruby', 'default')


def highlight_ragel_default(*args):
    highlightSourceCode('ragel', 'default')


def highlight_rconsole_default(*args):
    highlightSourceCode('rconsole', 'default')


def highlight_rd_default(*args):
    highlightSourceCode('rd', 'default')


def highlight_rebol_default(*args):
    highlightSourceCode('rebol', 'default')


def highlight_red_default(*args):
    highlightSourceCode('red', 'default')


def highlight_redcode_default(*args):
    highlightSourceCode('redcode', 'default')


def highlight_registry_default(*args):
    highlightSourceCode('registry', 'default')


def highlight_rnc_default(*args):
    highlightSourceCode('rnc', 'default')


def highlight_resource_default(*args):
    highlightSourceCode('resource', 'default')


def highlight_rst_default(*args):
    highlightSourceCode('rst', 'default')


def highlight_rexx_default(*args):
    highlightSourceCode('rexx', 'default')


def highlight_rhtml_default(*args):
    highlightSourceCode('rhtml', 'default')


def highlight_roboconf_graph_default(*args):
    highlightSourceCode('roboconf-graph', 'default')


def highlight_roboconf_instances_default(*args):
    highlightSourceCode('roboconf-instances', 'default')


def highlight_robotframework_default(*args):
    highlightSourceCode('robotframework', 'default')


def highlight_spec_default(*args):
    highlightSourceCode('spec', 'default')


def highlight_rql_default(*args):
    highlightSourceCode('rql', 'default')


def highlight_rsl_default(*args):
    highlightSourceCode('rsl', 'default')


def highlight_rbcon_default(*args):
    highlightSourceCode('rbcon', 'default')


def highlight_rb_default(*args):
    highlightSourceCode('rb', 'default')


def highlight_rust_default(*args):
    highlightSourceCode('rust', 'default')


def highlight_splus_default(*args):
    highlightSourceCode('splus', 'default')


def highlight_sas_default(*args):
    highlightSourceCode('sas', 'default')


def highlight_sass_default(*args):
    highlightSourceCode('sass', 'default')


def highlight_scala_default(*args):
    highlightSourceCode('scala', 'default')


def highlight_ssp_default(*args):
    highlightSourceCode('ssp', 'default')


def highlight_scaml_default(*args):
    highlightSourceCode('scaml', 'default')


def highlight_scheme_default(*args):
    highlightSourceCode('scheme', 'default')


def highlight_scilab_default(*args):
    highlightSourceCode('scilab', 'default')


def highlight_scss_default(*args):
    highlightSourceCode('scss', 'default')


def highlight_shen_default(*args):
    highlightSourceCode('shen', 'default')


def highlight_silver_default(*args):
    highlightSourceCode('silver', 'default')


def highlight_slim_default(*args):
    highlightSourceCode('slim', 'default')


def highlight_smali_default(*args):
    highlightSourceCode('smali', 'default')


def highlight_smalltalk_default(*args):
    highlightSourceCode('smalltalk', 'default')


def highlight_smarty_default(*args):
    highlightSourceCode('smarty', 'default')


def highlight_snobol_default(*args):
    highlightSourceCode('snobol', 'default')


def highlight_snowball_default(*args):
    highlightSourceCode('snowball', 'default')


def highlight_sp_default(*args):
    highlightSourceCode('sp', 'default')


def highlight_sparql_default(*args):
    highlightSourceCode('sparql', 'default')


def highlight_sql_default(*args):
    highlightSourceCode('sql', 'default')


def highlight_sqlite3_default(*args):
    highlightSourceCode('sqlite3', 'default')


def highlight_squidconf_default(*args):
    highlightSourceCode('squidconf', 'default')


def highlight_stan_default(*args):
    highlightSourceCode('stan', 'default')


def highlight_sml_default(*args):
    highlightSourceCode('sml', 'default')


def highlight_stata_default(*args):
    highlightSourceCode('stata', 'default')


def highlight_sc_default(*args):
    highlightSourceCode('sc', 'default')


def highlight_swift_default(*args):
    highlightSourceCode('swift', 'default')


def highlight_swig_default(*args):
    highlightSourceCode('swig', 'default')


def highlight_systemverilog_default(*args):
    highlightSourceCode('systemverilog', 'default')


def highlight_tads3_default(*args):
    highlightSourceCode('tads3', 'default')


def highlight_tap_default(*args):
    highlightSourceCode('tap', 'default')


def highlight_tasm_default(*args):
    highlightSourceCode('tasm', 'default')


def highlight_tcl_default(*args):
    highlightSourceCode('tcl', 'default')


def highlight_tcshcon_default(*args):
    highlightSourceCode('tcshcon', 'default')


def highlight_tcsh_default(*args):
    highlightSourceCode('tcsh', 'default')


def highlight_tea_default(*args):
    highlightSourceCode('tea', 'default')


def highlight_termcap_default(*args):
    highlightSourceCode('termcap', 'default')


def highlight_terminfo_default(*args):
    highlightSourceCode('terminfo', 'default')


def highlight_terraform_default(*args):
    highlightSourceCode('terraform', 'default')


def highlight_tex_default(*args):
    highlightSourceCode('tex', 'default')


def highlight_text_default(*args):
    highlightSourceCode('text', 'default')


def highlight_thrift_default(*args):
    highlightSourceCode('thrift', 'default')


def highlight_todotxt_default(*args):
    highlightSourceCode('todotxt', 'default')


def highlight_rts_default(*args):
    highlightSourceCode('rts', 'default')


def highlight_tsql_default(*args):
    highlightSourceCode('tsql', 'default')


def highlight_treetop_default(*args):
    highlightSourceCode('treetop', 'default')


def highlight_turtle_default(*args):
    highlightSourceCode('turtle', 'default')


def highlight_twig_default(*args):
    highlightSourceCode('twig', 'default')


def highlight_ts_default(*args):
    highlightSourceCode('ts', 'default')


def highlight_typoscript_default(*args):
    highlightSourceCode('typoscript', 'default')


def highlight_typoscriptcssdata_default(*args):
    highlightSourceCode('typoscriptcssdata', 'default')


def highlight_typoscripthtmldata_default(*args):
    highlightSourceCode('typoscripthtmldata', 'default')


def highlight_urbiscript_default(*args):
    highlightSourceCode('urbiscript', 'default')


def highlight_vala_default(*args):
    highlightSourceCode('vala', 'default')


def highlight_vb_net_default(*args):
    highlightSourceCode('vb.net', 'default')


def highlight_vcl_default(*args):
    highlightSourceCode('vcl', 'default')


def highlight_vclsnippets_default(*args):
    highlightSourceCode('vclsnippets', 'default')


def highlight_vctreestatus_default(*args):
    highlightSourceCode('vctreestatus', 'default')


def highlight_velocity_default(*args):
    highlightSourceCode('velocity', 'default')


def highlight_verilog_default(*args):
    highlightSourceCode('verilog', 'default')


def highlight_vgl_default(*args):
    highlightSourceCode('vgl', 'default')


def highlight_vhdl_default(*args):
    highlightSourceCode('vhdl', 'default')


def highlight_vim_default(*args):
    highlightSourceCode('vim', 'default')


def highlight_wdiff_default(*args):
    highlightSourceCode('wdiff', 'default')


def highlight_whiley_default(*args):
    highlightSourceCode('whiley', 'default')


def highlight_x10_default(*args):
    highlightSourceCode('x10', 'default')


def highlight_xml_default(*args):
    highlightSourceCode('xml', 'default')


def highlight_xquery_default(*args):
    highlightSourceCode('xquery', 'default')


def highlight_xslt_default(*args):
    highlightSourceCode('xslt', 'default')


def highlight_xtend_default(*args):
    highlightSourceCode('xtend', 'default')


def highlight_extempore_default(*args):
    highlightSourceCode('extempore', 'default')


def highlight_yaml_default(*args):
    highlightSourceCode('yaml', 'default')


def highlight_zephir_default(*args):
    highlightSourceCode('zephir', 'default')


g_exportedScripts = (create_dialog, apply_previous_settings, highlight_abap_default, highlight_abnf_default, highlight_as3_default, highlight_as_default, highlight_ada_default, highlight_adl_default, highlight_agda_default, highlight_aheui_default, highlight_alloy_default, highlight_at_default, highlight_ampl_default, highlight_ng2_default, highlight_antlr_default, highlight_apacheconf_default, highlight_apl_default, highlight_applescript_default, highlight_arduino_default, highlight_aspectj_default, highlight_aspx_cs_default, highlight_aspx_vb_default, highlight_asy_default, highlight_ahk_default, highlight_autoit_default, highlight_awk_default, highlight_basemake_default, highlight_console_default, highlight_bash_default, highlight_bat_default, highlight_bbcode_default, highlight_bc_default, highlight_befunge_default, highlight_bib_default, highlight_blitzbasic_default, highlight_blitzmax_default, highlight_bnf_default, highlight_boo_default, highlight_boogie_default, highlight_brainfuck_default, highlight_bro_default, highlight_bst_default, highlight_bugs_default, highlight_csharp_default, highlight_c_objdump_default, highlight_c_default, highlight_cpp_default, highlight_ca65_default, highlight_cadl_default, highlight_camkes_default, highlight_capnp_default, highlight_capdl_default, highlight_cbmbas_default, highlight_ceylon_default, highlight_cfengine3_default, highlight_cfs_default, highlight_chai_default, highlight_chapel_default, highlight_cheetah_default, highlight_cirru_default, highlight_clay_default, highlight_clean_default, highlight_clojure_default, highlight_clojurescript_default, highlight_cmake_default, highlight_cobol_default, highlight_cobolfree_default, highlight_coffee_script_default, highlight_cfc_default, highlight_cfm_default, highlight_common_lisp_default, highlight_componentpascal_default, highlight_coq_default, highlight_cpp_objdump_default, highlight_cpsa_default, highlight_crmsh_default, highlight_croc_default, highlight_cryptol_default, highlight_cr_default, highlight_csound_document_default, highlight_csound_default, highlight_csound_score_default, highlight_css_default, highlight_cuda_default, highlight_cypher_default, highlight_cython_default, highlight_d_objdump_default, highlight_d_default, highlight_dpatch_default, highlight_dart_default, highlight_control_default, highlight_sourceslist_default, highlight_delphi_default, highlight_dg_default, highlight_diff_default, highlight_django_default, highlight_docker_default, highlight_dtd_default, highlight_duel_default, highlight_dylan_console_default, highlight_dylan_default, highlight_dylan_lid_default, highlight_earl_grey_default, highlight_easytrieve_default, highlight_ebnf_default, highlight_ec_default, highlight_ecl_default, highlight_eiffel_default, highlight_iex_default, highlight_elixir_default, highlight_elm_default, highlight_emacs_default, highlight_ragel_em_default, highlight_erb_default, highlight_erl_default, highlight_erlang_default, highlight_evoque_default, highlight_ezhil_default, highlight_factor_default, highlight_fancy_default, highlight_fan_default, highlight_felix_default, highlight_fish_default, highlight_flatline_default, highlight_forth_default, highlight_fortran_default, highlight_fortranfixed_default, highlight_foxpro_default, highlight_fsharp_default, highlight_gap_default, highlight_gas_default, highlight_genshitext_default, highlight_genshi_default, highlight_pot_default, highlight_cucumber_default, highlight_glsl_default, highlight_gnuplot_default, highlight_go_default, highlight_golo_default, highlight_gooddata_cl_default, highlight_gst_default, highlight_gosu_default, highlight_groff_default, highlight_groovy_default, highlight_haml_default, highlight_handlebars_default, highlight_haskell_default, highlight_hx_default, highlight_hexdump_default, highlight_hsail_default, highlight_html_default, highlight_http_default, highlight_haxeml_default, highlight_hylang_default, highlight_hybris_default, highlight_idl_default, highlight_idris_default, highlight_igor_default, highlight_i6t_default, highlight_inform6_default, highlight_inform7_default, highlight_ini_default, highlight_io_default, highlight_ioke_default, highlight_irc_default, highlight_isabelle_default, highlight_j_default, highlight_jags_default, highlight_jasmin_default, highlight_jsp_default, highlight_java_default, highlight_js_default, highlight_jcl_default, highlight_jsgf_default, highlight_jsonld_default, highlight_json_default, highlight_json_object_default, highlight_jlcon_default, highlight_julia_default, highlight_juttle_default, highlight_kal_default, highlight_kconfig_default, highlight_koka_default, highlight_kotlin_default, highlight_lasso_default, highlight_lean_default, highlight_less_default, highlight_lighty_default, highlight_limbo_default, highlight_liquid_default, highlight_lagda_default, highlight_lcry_default, highlight_lhs_default, highlight_lidr_default,
                     highlight_live_script_default, highlight_llvm_default, highlight_logos_default, highlight_logtalk_default, highlight_lsl_default, highlight_lua_default, highlight_make_default, highlight_mako_default, highlight_maql_default, highlight_md_default, highlight_mask_default, highlight_mason_default, highlight_mathematica_default, highlight_matlabsession_default, highlight_matlab_default, highlight_minid_default, highlight_modelica_default, highlight_modula2_default, highlight_trac_wiki_default, highlight_monkey_default, highlight_monte_default, highlight_moocode_default, highlight_moon_default, highlight_mozhashpreproc_default, highlight_mozpercentpreproc_default, highlight_mql_default, highlight_mscgen_default, highlight_doscon_default, highlight_mupad_default, highlight_mxml_default, highlight_myghty_default, highlight_mysql_default, highlight_nasm_default, highlight_ncl_default, highlight_nemerle_default, highlight_nesc_default, highlight_newlisp_default, highlight_newspeak_default, highlight_nginx_default, highlight_nim_default, highlight_nit_default, highlight_nixos_default, highlight_nsis_default, highlight_numpy_default, highlight_nusmv_default, highlight_objdump_nasm_default, highlight_objdump_default, highlight_objective_c_default, highlight_objective_j_default, highlight_ocaml_default, highlight_octave_default, highlight_odin_default, highlight_ooc_default, highlight_opa_default, highlight_openedge_default, highlight_pacmanconf_default, highlight_pan_default, highlight_parasail_default, highlight_pawn_default, highlight_perl6_default, highlight_perl_default, highlight_php_default, highlight_pig_default, highlight_pike_default, highlight_pkgconfig_default, highlight_plpgsql_default, highlight_psql_default, highlight_postgresql_default, highlight_postscript_default, highlight_pov_default, highlight_ps1con_default, highlight_powershell_default, highlight_praat_default, highlight_prolog_default, highlight_properties_default, highlight_protobuf_default, highlight_pug_default, highlight_puppet_default, highlight_pypylog_default, highlight_py3tb_default, highlight_python3_default, highlight_pycon_default, highlight_pytb_default, highlight_python_default, highlight_qbasic_default, highlight_qml_default, highlight_qvto_default, highlight_racket_default, highlight_ragel_c_default, highlight_ragel_cpp_default, highlight_ragel_d_default, highlight_ragel_java_default, highlight_ragel_objc_default, highlight_ragel_ruby_default, highlight_ragel_default, highlight_rconsole_default, highlight_rd_default, highlight_rebol_default, highlight_red_default, highlight_redcode_default, highlight_registry_default, highlight_rnc_default, highlight_resource_default, highlight_rst_default, highlight_rexx_default, highlight_rhtml_default, highlight_roboconf_graph_default, highlight_roboconf_instances_default, highlight_robotframework_default, highlight_spec_default, highlight_rql_default, highlight_rsl_default, highlight_rbcon_default, highlight_rb_default, highlight_rust_default, highlight_splus_default, highlight_sas_default, highlight_sass_default, highlight_scala_default, highlight_ssp_default, highlight_scaml_default, highlight_scheme_default, highlight_scilab_default, highlight_scss_default, highlight_shen_default, highlight_silver_default, highlight_slim_default, highlight_smali_default, highlight_smalltalk_default, highlight_smarty_default, highlight_snobol_default, highlight_snowball_default, highlight_sp_default, highlight_sparql_default, highlight_sql_default, highlight_sqlite3_default, highlight_squidconf_default, highlight_stan_default, highlight_sml_default, highlight_stata_default, highlight_sc_default, highlight_swift_default, highlight_swig_default, highlight_systemverilog_default, highlight_tads3_default, highlight_tap_default, highlight_tasm_default, highlight_tcl_default, highlight_tcshcon_default, highlight_tcsh_default, highlight_tea_default, highlight_termcap_default, highlight_terminfo_default, highlight_terraform_default, highlight_tex_default, highlight_text_default, highlight_thrift_default, highlight_todotxt_default, highlight_rts_default, highlight_tsql_default, highlight_treetop_default, highlight_turtle_default, highlight_twig_default, highlight_ts_default, highlight_typoscript_default, highlight_typoscriptcssdata_default, highlight_typoscripthtmldata_default, highlight_urbiscript_default, highlight_vala_default, highlight_vb_net_default, highlight_vcl_default, highlight_vclsnippets_default, highlight_vctreestatus_default, highlight_velocity_default, highlight_verilog_default, highlight_vgl_default, highlight_vhdl_default, highlight_vim_default, highlight_wdiff_default, highlight_whiley_default, highlight_x10_default, highlight_xml_default, highlight_xquery_default, highlight_xslt_default, highlight_xtend_default, highlight_extempore_default, highlight_yaml_default, highlight_zephir_default,)
