# -*- coding: utf-8 -*-
# version 1.1
"""
USFM → Scribus (selected story only)

- Paragraph styles: \p, \s1, \ms, \mr, \q1  → RS/AS styles per map
- Character styles: \c (chapter #), \v (verse #) → RS/AS styles per map
- Delete markers and their following space
- Join verse-per-line into logical paragraphs (internal newlines → spaces)
- Keep only left side of \w … | … \w* and \+w … | … \+w*
- Remove \f … \f* footnotes (inclusive)
- Unwrap \qs … \qs* (keep inner text)
- Insert NBSP (U+00A0) after verse numbers (\v) and ensure the entire digit run is styled
- For Arabic-script output, prefix verse numbers with the ordination mark U+06DD and treat it as part of the styled digit run

Tested with Scribus 1.5.8–1.6.x. Requires Scripter.
"""

import re
import sys
import scribus

# ---------------------------------------------------------------------------
# 1) USER-CONFIGURABLE MAPPINGS (extend here)
# ---------------------------------------------------------------------------
# Values are tuples: (RS_style, AS_style)
paraStyles = {
    r'\p' : ('pRS',  'pAS'),
    r'\b' : ('pRS',  'pAS'), 
    r'\s1': ('s1RS', 's1AS'),
    r'\cl': ('s1RS', 's1AS'),
    r'\ms': ('msRS', 'msAS'),
    r'\ms1': ('msRS', 'msAS'),
    r'\mr': ('mrRS', 'mrAS'),
    r'\r': ('rRS', 'rAS'),
    r'\qa': ('rRS', 'rAS'),
    r'\d': ('dRS', 'dAS'),
    r'\q': ('q1RS', 'q1AS'),
    r'\q1': ('q1RS', 'q1AS'),
    r'\q2': ('q2RS', 'q2AS'),
    r'\qr': ('qrRS', 'qrAS'),
    r'\m': ('mRS', 'mAS'),
    r'\c': ('cRS', 'cAS'),

    # Add more paragraph markers here if needed.
}

charStyles = {
    r'\v': ('vRS', 'vAS'),
    # Add other inline markers if you decide to style them.
}

# ---------------------------------------------------------------------------
# General text replacements (happens before parsing)
# Format: "Old Text" : "New Text"
# ---------------------------------------------------------------------------
generalReplacements = {
    '---': '\u2014',        # Em dash
    
}



# If a paragraph marker has no mapping, fall back to this:
FALLBACK_PARA_MARKER = r'\p'

# ---------------------------------------------------------------------------
# 2) CLEANUP RULES
# ---------------------------------------------------------------------------
RE_FOOTNOTE  = re.compile(r'\\f\b.*?\\f\*', flags=re.S)                      # remove \f ... \f*
RE_WORD_LEFT = re.compile(r'\\\+?w\s+([^|\\]+)\|.*?\\\+?w\*', flags=re.S)    # keep left of '|' for \w / \+w

# RE_W_GLOSSED = re.compile(r'\\\+?w\s+([^|\\\n\r]+)\|.*?\\\+?w\*', flags=re.S)
RE_W_SIMPLE  = re.compile(r'\\\+w\s+([^\\]+?)\\\+w\*', flags=re.S)            # \+w Selah\+w* > Selah

RE_QS_UNWRAP = re.compile(r'\\qs\b\s*(.*?)\\qs\*', flags=re.S)               # unwrap \qs ... \qs* > \qs Selaw.\qs*

# ---------------------------------------------------------------------------
# 3) INTERNALS
# ---------------------------------------------------------------------------

# DIGIT CLASSES: ASCII 0–9 plus Arabic-Indic (0660–0669) and Eastern Arabic-Indic (06F0–06F9)
DIGITS = r'[0-9\u0660-\u0669\u06F0-\u06F9]+'

# Spacer configuration
SPACER_STYLE = 'enableColTopExtraSpace'
SPACER_MARKERS = {r'\s1', r'\ms'}

# Paragraph markers we explicitly support — longest first to avoid partial matches
PARA_MARKERS = tuple(sorted((k.lstrip('\\') for k in paraStyles.keys()), key=len, reverse=True))

# Token scanner:
#  - paragraph markers + trailing space   → start new logical paragraph
#  - \c <digits>, \v <digits>             → keep digits (styled), delete marker + space
#  - any other marker like \qs, \qs* etc. → dropped by generic branch
RE_TOKENS = re.compile(
    r'''
    (\\(?P<pm>''' + '|'.join(map(re.escape, PARA_MARKERS)) + r''')\s)     # paragraph marker + space
  | (\\c\s+(?P<cnum>''' + DIGITS + r'''))                                  # chapter number
  | (\\v\s+(?P<vnum>''' + DIGITS + r'''))                                  # verse number
  | (\\(?P<other>[A-Za-z0-9*]+))                                           # any other marker (drop)
    ''',
    re.X
)

# Final-pass regex: verse number at start of paragraph = (^|\r)(optional 06DD mark + digits) NBSP
# We include the Arabic ordination mark U+06DD before the digits when present so
# that the entire run can be styled together. The capturing group therefore
# includes the mark if it's there.
VERSE_RUN_FINAL_RE = re.compile(r'(?m)(^|\r)(\u06DD?'+DIGITS+r')\u00A0')

def safe_message_box(caption, message, *, icon=None, yes_no_cancel=False, default="ok"):
    icon = scribus.ICON_INFORMATION if icon is None else icon
    if yes_no_cancel:
        b1 = scribus.BUTTON_YES | (scribus.BUTTON_DEFAULT if default.lower() == "yes" else 0)
        b2 = scribus.BUTTON_NO  | (scribus.BUTTON_DEFAULT if default.lower() == "no"  else 0)
        esc = getattr(scribus, "BUTTON_ESCAPE", 0)
        b3 = scribus.BUTTON_CANCEL | esc | (scribus.BUTTON_DEFAULT if default.lower() == "cancel" else 0)
        res = scribus.messageBox(caption, message, icon, b1, b2, b3)
        if res == scribus.BUTTON_YES: return "yes"
        if res == scribus.BUTTON_NO:  return "no"
        return "cancel"
    else:
        b1 = scribus.BUTTON_OK | scribus.BUTTON_DEFAULT
        scribus.messageBox(caption, message, icon, b1, scribus.BUTTON_NONE, scribus.BUTTON_NONE)
        return "ok"

def require_selected_textframe():
    if not scribus.haveDoc():
        safe_message_box("USFM → Styles", "Open a Scribus document first.", icon=scribus.ICON_WARNING)
        sys.exit(1)
    try:
        if scribus.selectionCount() < 1:
            safe_message_box("USFM → Styles", "Select a text frame (or a frame in a chain) and run again.",
                             icon=scribus.ICON_WARNING)
            sys.exit(1)
        name = scribus.getSelectedObject(0)
        kind = scribus.getObjectType(name)
        if kind != "TextFrame" and kind != 4:   # some builds return numeric type code
            safe_message_box("USFM → Styles", "Selected object is not a TextFrame.", icon=scribus.ICON_WARNING)
            sys.exit(1)
        return name
    except Exception as e:
        safe_message_box("USFM → Styles – Error", str(e), icon=scribus.ICON_CRITICAL)
        sys.exit(1)

def ask_script_set():
    """
    Returns 'RS' for Roman (No) or 'AS' for Arabic (Yes). Cancel exits.
    """
    ans = safe_message_box(
        "USFM → Styles",
        "Apply Arabic-script styles?\n\nYes = AS (Arabic)\nNo = RS (Roman)\nCancel = Abort",
        icon=scribus.ICON_INFORMATION,
        yes_no_cancel=True,
        default="no",
    )
    if ans == "cancel":
        sys.exit(0)
    return "AS" if ans == "yes" else "RS"

def pick_style(style_map, marker, script):  # marker like r'\p' or r'\v'
    pair = style_map.get(marker)
    if not pair:
        return None
    return pair[1] if script == "AS" else pair[0]

def get_all_text(frame):
    try:
        return scribus.getAllText(frame)
    except Exception:
        try:
            return scribus.getText(frame)
        except Exception:
            return u""

def set_whole_text(frame, text):
    # Replace entire story text of the chain that starts at this frame
    try:
        total = scribus.getTextLength(frame)
        if total > 0:
            scribus.selectText(0, total, frame)
            scribus.deleteText(frame)
    except Exception:
        pass
    scribus.insertText(text, 0, frame)

def reset_formatting(frame, script):
    """
    Select all text and apply 'Default Paragraph Style' and 'Default Character Style'.
    """
    try:
        total = scribus.getTextLength(frame)
        if total > 0:
            scribus.selectText(0, total, frame)
            scribus.setParagraphStyle("Default Paragraph Style " + script, frame)
            scribus.setCharacterStyle("Default Character Style " + script, frame)
    except Exception as e:
        print(f"[WARN] Could not reset formatting: {e}")

def apply_paragraph_style(frame, start, length, style_name):
    """Apply paragraph style; include the break in the selection for reliability."""
    if length <= 0: return
    try:
        scribus.selectText(start, length + 1, frame)  # include '\r' after the paragraph
        try:
            scribus.setParagraphStyle(style_name, frame)
        except Exception:
            scribus.setStyle(style_name, frame)
    except Exception as e:
        print(f"[WARN] Could not apply paragraph style '{style_name}' to {start}:{length}: {e}")

def apply_character_style(frame, start, length, style_name):
    if length <= 0: return
    try:
        scribus.selectText(start, length, frame)
        scribus.setCharacterStyle(style_name, frame)
    except Exception as e:
        print(f"[WARN] Could not apply character style '{style_name}' to {start}:{length}: {e}")

def normalize_whitespace(s):
    """
    Convert hard line breaks within a logical paragraph to single spaces,
    collapse ASCII spaces/tabs only (NOT NBSP), so U+00A0 stays intact.
    """
    s = s.replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'[ \t]+', ' ', s)  # NBSP is preserved

def parse_usfm_to_story(usfm_text, script):
    """
    Returns (final_text, para_ranges, char_ranges)
      para_ranges: list of (start, length, para_style_name)
      char_ranges: list of (start, length, char_style_name)
    """
    # 0) Apply general replacements
    for old, new in generalReplacements.items():
        usfm_text = usfm_text.replace(old, new)


    # 1) Strip footnotes entirely
    t = RE_FOOTNOTE.sub('', usfm_text)

    # 2.1) Keep only left side for \w / \+w and remove those wrappers
    t = RE_WORD_LEFT.sub(lambda m: m.group(1), t)

    # 2.2) \+w Selah\+w* > Selah
    t = RE_W_SIMPLE.sub(lambda m: m.group(1), t)

    # 3) Unwrap \qs … \qs* (keep inner text)
    t = RE_QS_UNWRAP.sub(lambda m: normalize_whitespace(m.group(1)), t)

    # 4) Walk the stream and build logical paragraphs
    paragraphs = []  # each: {code:str, text:str, spans:[(start, length, charstyle)]}
    current_code = FALLBACK_PARA_MARKER  # default paragraph kind
    buf = []        # text buffer for current paragraph
    spans = []      # local (start, length, charstyle)
    spans = []      # local (start, length, charstyle)
    has_verse = False # distinct flag for if this paragraph starts with a verse number
    first_verse_num = None
    
    pos = 0
    strip_space_next_seg = False  # used when we've just injected NBSP after \v

    def append_text(chunk):
        if not chunk:
            return
        # If chunk is just a tab or similar special char we want to preserve,
        # we might want to skip normalization or handle it specially.
        # But here, let's just use a simple heuristic: if it starts with \t, keep it raw?
        # Actually, let's just add a param to the internal function if possible? 
        # Python nested functions can't easily change signature without meaningful refactor.
        # So let's check if the chunk is exactly a tab.
        if chunk == '\t':
            flat = chunk
        else:
            flat = normalize_whitespace(chunk)

        # Fix: logical paragraphs are stripped later (''.join(buf).strip()),
        # so if we don't lstrip the first chunk, our calculated indices
        # will be offset by the length of that leading whitespace.
        if not buf:
            flat = flat.lstrip()

        if not flat:
            return

        start = sum(len(x) for x in buf)
        buf.append(flat)
        return start, len(flat)

    while True:
        m = RE_TOKENS.search(t, pos)
        seg = t[pos: m.start()] if m else t[pos:]
        if strip_space_next_seg and seg:
            # Eat one run of ASCII whitespace after the NBSP we just inserted.
            # (Do not eat NBSP — there won’t be one in the source here.)
            seg = seg.lstrip(' \t\r\n')
            strip_space_next_seg = False
        append_text(seg)

        if not m:
            break

        pos = m.end()

        if m.group('pm'):  # paragraph marker matched (space not captured)
            # Commit previous paragraph if it has content
            para_text = ''.join(buf).strip()
            if para_text:
                paragraphs.append({
                    'code': current_code, 
                    'text': para_text, 
                    'spans': spans, 
                    'has_verse': has_verse,
                    'first_verse_num': first_verse_num
                })

            code = '\\' + m.group('pm')  # pm has no trailing space

            # --- SPECIAL CASE: \b (blank line) produces a one‑NBSP paragraph ---
            if code == r'\b':
                paragraphs.append({
                    'code': r'\b',
                    'text': '\u00A0',   # NBSP placeholder so style applies
                    'spans': [],
                    'has_verse': False,
                    'first_verse_num': None
                })
                # After a blank line, start fresh using fallback paragraph type
                current_code = FALLBACK_PARA_MARKER
                buf, spans = [], []
                has_verse = False
                first_verse_num = None
                continue
            # -------------------------------------------------------------------

            # Normal paragraph start
            current_code = code if code in paraStyles else FALLBACK_PARA_MARKER
            buf, spans = [], []
            has_verse = False
            first_verse_num = None
            continue

        if m.group('cnum'):
            digits = m.group('cnum')
            start2, ln = append_text(digits)
            cs = pick_style(charStyles, r'\c', script)
            if cs:
                spans.append((start2, ln, cs))
            continue

        if m.group('vnum'):
            orig_digits = m.group('vnum')

            # If buffer is empty (or whitespace only), this is a "verse-start" paragraph
            if not ''.join(buf).strip():
                has_verse = True
                if first_verse_num is None:
                    first_verse_num = orig_digits

            # Prepend Arabic ordination mark (U+06DD) when using Arabic-script styles
            digits = orig_digits
            if script == "AS":
                digits = '\u06DD' + orig_digits

            start2, ln = append_text(digits)
            
            # Decide separator: TAB for poetry (\q...), NBSP for others
            if current_code.startswith(r'\q'):
                sep = '\t'
            else:
                sep = '\u00A0'
            
            append_text(sep)
            
            strip_space_next_seg = True
            cs = pick_style(charStyles, r'\v', script)
            if cs:
                spans.append((start2, ln, cs))
            continue

        if m.group('other'):
            # Drop unknown marker, and also drop a single following space if present
            if pos < len(t) and t[pos:pos+1] == ' ':
                pos += 1
            continue

    # Finish last paragraph
    para_text = ''.join(buf).strip()
    if para_text:
        paragraphs.append({
            'code': current_code, 
            'text': para_text, 
            'spans': spans, 
            'has_verse': has_verse,
            'first_verse_num': first_verse_num
        })

    # 5) Build final story text and absolute ranges
    final_text = []
    para_ranges = []  # (start, length, para_style_name)
    char_ranges = []  # (start, length, char_style_name)

    offset = 0
    has_seen_header = False

    for p in paragraphs:
        text = p['text']
        if not text:
            continue
        
        # Check if we need to insert a spacer paragraph before this one
        # if p['code'] in SPACER_MARKERS:
        #     if has_seen_header:
        #         # Insert spacer paragraph: single space + CR (so length > 0)
        #         start_spacer = offset
        #         final_text.append(' ')
        #         offset += 1
        #         final_text.append('\r')
        #         offset += 1
        #         para_ranges.append((start_spacer, 1, SPACER_STYLE))
        #     else:
        #         has_seen_header = True

        start = offset
        final_text.append(text)
        offset += len(text)
        # add paragraph break
        final_text.append('\r')
        offset += 1

        # paragraph style
        style_name = pick_style(paraStyles, p['code'], script) or pick_style(paraStyles, FALLBACK_PARA_MARKER, script)
        
        # New Rule: if paragraph is \p and starts with \v 1, use \m style (mRS/mAS)
        # We check p['code'] against r'\p' specifically.
        if p['code'] == r'\p' and p.get('first_verse_num') == '1':
            m_style = pick_style(paraStyles, r'\m', script)
            if m_style:
                style_name = m_style

        # New Requirement: If poetry paragraph starts with verse, inject 'v' before script suffix.
        # e.g., 'q1AS' -> 'q1vAS'
        if p['has_verse'] and p['code'].startswith(r'\q'):
            if style_name:
                if style_name.endswith('AS'):
                    style_name = style_name[:-2] + 'vAS'
                elif style_name.endswith('RS'):
                    style_name = style_name[:-2] + 'vRS'

        para_ranges.append((start, len(text), style_name))

        # character spans (local -> absolute)
        for ls, ln, cs in p['spans']:
            char_ranges.append((start + ls, ln, cs))

    return ''.join(final_text), para_ranges, char_ranges

def process_selected_story(frame, script):
    src = get_all_text(frame)
    if not src.strip():
        safe_message_box("USFM → Styles", "Selected story is empty.", icon=scribus.ICON_WARNING)
        return

    final_text, para_ranges, char_ranges = parse_usfm_to_story(src, script)

    # Replace the story content
    set_whole_text(frame, final_text)

    # Clear prior formatting (e.g. from previous runs or default template junk)
    # reset_formatting(frame, script) # this is not working

    # Apply paragraph styles FIRST, then character styles (so digits keep their style)
    for s, ln, ps in para_ranges:
        apply_paragraph_style(frame, s, ln, ps)

    # First pass: apply character spans computed during parsing
    # (covers \c digits and initial \v digits; harmless to re-apply later)
    def is_digit(ch: str) -> bool:
        # Python's str.isdigit() handles ASCII + Arabic-Indic ranges.
        return ch.isdigit()

    def adjust_to_digit_run(text: str, start: int, _length: int):
        """
        Snap (start, length) to the actual contiguous digit run that begins
        at 'start' or immediately before it (off-by-one safety).
        Returns (new_start, new_length). If no digits found, returns (start, 0).

        When Arabic-script styles are active we also include a preceding U+06DD
        ordination mark in the run so it will get styled alongside the digits.
        """
        n = len(text)
        s = max(0, min(start, n))
        # If we land directly on the ordination mark (U+06DD) at the given
        # start offset, treat that mark as part of the run and grow to include
        # the subsequent digits. This ensures the first pass of character
        # styling doesn't skip the verse when the span begins on the mark.
        if s < n and text[s] == '\u06DD':
            e = s + 1
            while e < n and is_digit(text[e]):
                e += 1
            return (s, e - s)
        # If we landed on a non-digit but the previous char is a digit, step left
        if (s < n and not is_digit(text[s])) and (s > 0 and is_digit(text[s-1])):
            s -= 1
        # If current is not a digit, bail
        if not (s < n and is_digit(text[s])):
            return (start, 0)
        # Grow to cover the whole digit run
        e = s
        while e < n and is_digit(text[e]):
            e += 1
        # include preceding ordination mark if present
        if s > 0 and text[s-1] == '\u06DD':
            s -= 1
            e += 1
        return (s, e - s)

    for s, ln, cs in char_ranges:
        s2, ln2 = adjust_to_digit_run(final_text, s, ln)
        if ln2 > 0:
            apply_character_style(frame, s2, ln2, cs)

    # --- Final pass: ensure the entire verse-number run is styled (handles RTL quirks) ---
    current_text = get_all_text(frame) or final_text
    v_style = pick_style(charStyles, r'\v', script)
    if v_style:
        for m in VERSE_RUN_FINAL_RE.finditer(current_text):
            s = m.start(2)            # start of the digit run
            ln = len(m.group(2))      # length of the digit run
            apply_character_style(frame, s, ln, v_style)

    # Report
    msg = [
        "Finished converting USFM for the selected story.",
        "",
        f"Paragraphs styled: {len(para_ranges)}",
        f"Chapter/Verse runs styled: {len(char_ranges)}",
    ]
    safe_message_box("USFM → Styles", "\n".join(msg), icon=scribus.ICON_INFORMATION)

def main():
    frame = require_selected_textframe()
    script = ask_script_set()  # 'RS' or 'AS'
    process_selected_story(frame, script)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        safe_message_box("USFM → Styles – Error", str(e), icon=scribus.ICON_CRITICAL)
        raise