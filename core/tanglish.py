"""
Tanglish (Telugu + English Code-Switching) Semantic Translation & Normalization Engine.
Translates mixed Telugu conversational words and phrases into natural, professional English meaning
while preserving 100% of Whisper's frame-perfect, acoustic word timestamps.
"""

import re
from typing import List, Tuple, Dict, Any, Optional

# Match phrase-level patterns (evaluated on normalized word sequences)
PHRASE_TRANSLATIONS: List[Tuple[re.Pattern, str]] = [
    # Specific acoustic mishearings from Whisper on Telugu tech phrases
    (re.compile(r"^software\s+job\s+lo\s+m[ie]{1,2}ru\s+(play\s+sa\s+waliyan|place\s+avval[a-z]*|place\s+aval[a-z]*)$", re.IGNORECASE),
     "if you want to get placed in a software job"),
    (re.compile(r"^([a-z0-9+#.]+)\s+job\s+lo\s+m[ie]{1,2}ru\s+(play\s+sa\s+waliyan|place\s+avval[a-z]*|place\s+aval[a-z]*)$", re.IGNORECASE),
     r"if you want to get placed in a \1 job"),
    (re.compile(r"^m[ie]{1,2}ru\s+skill\s+(builder\s+sko\s+alay|build\s+ches[a-z]*|build\s+chey[a-z]*)$", re.IGNORECASE),
     "you have to build your skills"),
    (re.compile(r"^skill\s+(builder\s+sko\s+alay|build\s+chesukovali|build\s+cheskovali)$", re.IGNORECASE),
     "build your skills"),
    (re.compile(r"^m[ie]{1,2}ru\s+(play\s+sa\s+waliyan|place\s+avvali\s+ante|place\s+avvalante)$", re.IGNORECASE),
     "if you want to get placed"),
    (re.compile(r"^place\s+(avvali\s+ante|avvalante|avali\s+ante)$", re.IGNORECASE),
     "to get placed"),
    (re.compile(r"^avvali\s+ante$", re.IGNORECASE), "if you want to become"),
    (re.compile(r"^cheyali\s+ante$", re.IGNORECASE), "if you want to do"),
    (re.compile(r"^cheppali\s+ante$", re.IGNORECASE), "to be honest"),
    (re.compile(r"^software\s+job\s+lo$", re.IGNORECASE), "in a software job"),
    (re.compile(r"^IT\s+job\s+lo$", re.IGNORECASE), "in an IT job"),
    (re.compile(r"^([a-zA-Z0-9+#]+)\s+lo\s+m[ie]{1,2}ru$", re.IGNORECASE), r"in \1 you"),
    (re.compile(r"^([a-zA-Z0-9+#]+)\s+lo$", re.IGNORECASE), r"in \1"),
    (re.compile(r"^([a-zA-Z0-9+#]+)\s+ki$", re.IGNORECASE), r"for \1"),
    (re.compile(r"^m[ie]{1,2}ru\s+ch[ou]{1,2}dandi$", re.IGNORECASE), "you can see"),
    (re.compile(r"^m[ie]{1,2}ru\s+ch[ou]{1,2}sthunara$", re.IGNORECASE), "are you watching"),
    (re.compile(r"^idi\s+chala\s+important$", re.IGNORECASE), "this is very important"),
    (re.compile(r"^chala\s+important$", re.IGNORECASE), "very important"),
    (re.compile(r"^chala\s+baguntundi$", re.IGNORECASE), "will be very good"),
    (re.compile(r"^telusukondi$", re.IGNORECASE), "keep in mind"),
    (re.compile(r"^nerchukondi$", re.IGNORECASE), "learn this"),
]

# Single-word dictionary mappings (case-insensitive)
WORD_TRANSLATIONS: Dict[str, str] = {
    # Pronouns & People
    "miru": "you",
    "meeru": "you",
    "miku": "to you",
    "meeku": "to you",
    "mi": "your",
    "mee": "your",
    "nenu": "I",
    "naku": "to me",
    "naaku": "to me",
    "na": "my",
    "naa": "my",
    "manam": "we",
    "manamu": "we",
    "mana": "our",
    "vaallu": "they",
    "valu": "they",
    "atanu": "he",
    "aame": "she",
    "idi": "this",
    "adi": "that",
    "ivvi": "these",
    "avi": "those",
    # Connectors & Prepositions
    "lo": "in",
    "tho": "with",
    "valla": "because of",
    "kante": "than",
    "kanna": "than",
    "kosam": "for",
    "gurinchi": "about",
    "daggara": "at",
    "varaku": "until",
    # Verbs & Common Slang
    "chesukovali": "need to do",
    "cheskovali": "need to do",
    "cheyali": "should do",
    "cheyandi": "please do",
    "chudandi": "look",
    "choodandi": "look",
    "undi": "is there",
    "untundi": "will be there",
    "ledu": "is not there",
    "kadu": "not",
    "kadha": "right?",
    "kada": "right?",
    "avunu": "yes",
    "anthe": "that is all",
    "ante": "meaning",
    # Time & Adverbs
    "eeroju": "today",
    "eroju": "today",
    "ippudu": "now",
    "epudu": "always",
    "repu": "tomorrow",
    "ninna": "yesterday",
    "chala": "very",
    "konchem": "a little",
    "koddiga": "slightly",
    "baga": "well",
    "kani": "but",
    "kaani": "but",
    "anduke": "that's why",
    "endukante": "because",
}


def translate_words_in_place(words: List[Any]) -> List[Any]:
    """
    Translates Tanglish words and phrases directly in the word list while preserving
    100% of Whisper's frame-perfect acoustic timestamps for every English word.
    """
    from core.transcriber import WordTimestamp

    if not words:
        return []

    new_words: List[WordTimestamp] = []
    i = 0
    n = len(words)

    while i < n:
        matched = False

        # Try multi-word phrase matching from longest window (7 words) down to 2
        for window_size in range(min(7, n - i), 1, -1):
            window_slice = words[i:i + window_size]
            phrase_str = " ".join([re.sub(r"[^\w+#.]", "", w.word).lower() for w in window_slice])

            for pattern, replacement in PHRASE_TRANSLATIONS:
                match = pattern.match(phrase_str)
                if match:
                    # Matched a phrase! Use the exact start and end of this specific phrase window
                    w_start = window_slice[0].start
                    w_end = window_slice[-1].end

                    # Handle regex group substitutions (e.g. \1)
                    actual_replacement = pattern.sub(replacement, phrase_str)

                    # Split replacement into tokens and distribute ONLY over this phrase's exact time window
                    repl_tokens = actual_replacement.split()
                    if repl_tokens:
                        total_window = max(0.1, w_end - w_start)
                        sub_dur = total_window / len(repl_tokens)
                        for idx, tok in enumerate(repl_tokens):
                            tok_s = round(w_start + (idx * sub_dur), 2)
                            tok_e = round(min(w_end, tok_s + sub_dur), 2)

                            # Preserve trailing punctuation from the last word of the original slice
                            last_punc = ""
                            if idx == len(repl_tokens) - 1:
                                punc_match = re.search(r"([.,!?:;]+)$", window_slice[-1].word)
                                if punc_match:
                                    last_punc = punc_match.group(1)

                            new_words.append(WordTimestamp(
                                word=tok + last_punc,
                                start=tok_s,
                                end=tok_e,
                                probability=0.95
                            ))

                    i += window_size
                    matched = True
                    break
            if matched:
                break

        if not matched:
            curr_word = words[i]
            # Under NO circumstances allow Telugu or Indic script characters into subtitles
            if re.search(r"[\u0C00-\u0C7F\u0900-\u0D7F]", curr_word.word):
                i += 1
                continue

            clean_token = re.sub(r"[^\w]", "", curr_word.word).lower().strip()

            if clean_token in WORD_TRANSLATIONS:
                repl = WORD_TRANSLATIONS[clean_token]
                # Preserve existing trailing punctuation and capitalization
                punc = "".join([c for c in curr_word.word if c in ".,!?:;\"'"])
                if curr_word.word.istitle():
                    repl = repl.capitalize()

                # KEEP THE EXACT ORIGINAL TIMESTAMPS FROM WHISPER!
                new_words.append(WordTimestamp(
                    word=repl + punc,
                    start=curr_word.start,
                    end=curr_word.end,
                    probability=curr_word.probability
                ))
            else:
                # English word: keep 100% original word and timestamp
                new_words.append(curr_word)
            i += 1

    return new_words


def translate_tanglish_segment(segment: Any) -> Optional[Any]:
    """
    Translates a SubtitleSegment into natural English meaning.
    Translates words in-place so EVERY word maintains its exact acoustic sync with the audio.
    Strips any Telugu script completely.
    """
    from core.transcriber import SubtitleSegment

    if not segment.words:
        return None

    # Translate words in-place with exact Whisper timestamps
    translated_words = translate_words_in_place(segment.words)
    if not translated_words:
        return None

    # Reconstruct the sentence text from the accurately timed words
    new_text = " ".join([w.word for w in translated_words])

    # Capitalize first letter of sentences
    sentences = re.split(r"([.!?]\s*)", new_text)
    capped = []
    for s in sentences:
        if s and not s.isspace() and s not in (".", "!", "?"):
            capped.append(s[0].upper() + s[1:])
        else:
            capped.append(s)
    clean_sentence = "".join(capped).strip()

    # Double check for any residual Telugu/Indic characters
    clean_sentence = re.sub(r"[\u0C00-\u0C7F\u0900-\u0D7F]+", "", clean_sentence).strip(" :,-.")
    if not clean_sentence:
        return None

    return SubtitleSegment(
        start=segment.start,
        end=segment.end,
        text=clean_sentence,
        words=translated_words
    )


def translate_tanglish_segments(segments: List[Any]) -> List[Any]:
    """
    Processes all segments in a transcript, filtering out noise hallucinations
    and translating all Tanglish words and phrases into natural English meaning
    with frame-perfect acoustic sync.
    Strictly removes any Telugu language subtitles.
    """
    translated: List[Any] = []
    for seg in segments:
        # Check if segment is empty or just Telugu script
        clean_no_indic = re.sub(r"[\u0C00-\u0C7F\u0900-\u0D7F]+", "", seg.text).strip()
        # Filter out standalone low-confidence noise hallucinations like "ount!"
        clean_text = re.sub(r"[【】「」\[\]!?,.]", "", clean_no_indic).strip().lower()
        if not clean_text or (clean_text in ("ount", "chien", "olesome", "") and (seg.end - seg.start) < 0.8):
            continue

        trans_seg = translate_tanglish_segment(seg)
        if trans_seg and trans_seg.words and trans_seg.text.strip():
            translated.append(trans_seg)

    return translated
