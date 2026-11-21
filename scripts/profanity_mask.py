#!/usr/bin/env python3
"""Profanity masking for stream captions.

Masks explicit words in burned-in captions to meet platform content policies.
The original audio remains unchanged. This is intended for automated caption
generation where manual review may not be practical.
"""
import re


# Words to mask in captions (lowercase for matching)
# This list focuses on common explicit terms that may trigger platform restrictions
MASK_LIST = {
    # English profanity
    "fuck", "fucking", "fucked", "fucker", "fucks",
    "shit", "shitty", "shitter", "bullshit",
    "ass", "asshole", "asses",
    "bitch", "bitches", "bitching",
    "damn", "damned",
    "hell",
    "piss", "pissed",
    "crap", "crappy",
    "dick", "dicks",
    "cock", "cocks",
    "pussy", "pussies",
    "bastard", "bastards",
    "slut", "sluts", "slutty",
    "whore", "whores",
    "cunt", "cunts",
    
    # Slurs and offensive terms (partial list for common variants)
    "nigger", "nigga", "niggas",
    "faggot", "fag", "fags",
    "retard", "retarded",
    
    # Sexual terms
    "porn", "porno",
    "sex", "sexy",
    "tits", "tit",
    "boobs", "boob",
    "penis",
    "vagina",
}


# Prefix patterns that should be masked regardless of suffix
MASK_PREFIXES = {
    "fuck",
    "shit",
    "nigg",
    "fag"
}


def should_mask_word(word):
    """Check if a word should be masked."""
    # Normalize: remove non-letters and lowercase
    normalized = re.sub(r"[^a-z]", "", word.lower())
    
    if not normalized:
        return False
    
    # Exact match
    if normalized in MASK_LIST:
        return True
    
    # Prefix match
    for prefix in MASK_PREFIXES:
        if normalized.startswith(prefix):
            return True
    
    return False


def mask_word(word):
    """Mask a word by keeping first letter and replacing rest with asterisks.
    
    Examples:
        "fuck" -> "f***"
        "shit" -> "s***"
        "ass" -> "a**"
    """
    if len(word) <= 1:
        return word
    
    # Preserve any leading/trailing punctuation
    leading = ""
    trailing = ""
    core = word
    
    # Extract leading punctuation
    while core and not core[0].isalnum():
        leading += core[0]
        core = core[1:]
    
    # Extract trailing punctuation
    while core and not core[-1].isalnum():
        trailing = core[-1] + trailing
        core = core[:-1]
    
    if not core:
        return word
    
    # Mask: first character + asterisks + trailing punctuation
    masked_core = core[0] + "*" * max(2, len(core) - 1)
    return leading + masked_core + trailing


def mask_profanity(text, enabled=True):
    """Mask profanity in text by replacing most characters with asterisks.
    
    Args:
        text: Input text string
        enabled: If False, returns text unchanged
        
    Returns:
        Text with profanity masked
        
    Examples:
        "This is fucking amazing!" -> "This is f****** amazing!"
        "What the hell was that?" -> "What the h*** was that?"
    """
    if not enabled or not text:
        return text
    
    words = text.split()
    masked_words = []
    
    for word in words:
        if should_mask_word(word):
            masked_words.append(mask_word(word))
        else:
            masked_words.append(word)
    
    return " ".join(masked_words)


def mask_profanity_in_words(words, enabled=True):
    """Mask profanity in a list of word timing dicts.
    
    Args:
        words: List of dicts with at least a "text" or "word" key
        enabled: If False, returns words unchanged
        
    Returns:
        List of word dicts with profanity masked in text field
    """
    if not enabled:
        return words
    
    result = []
    for w in words:
        w_copy = dict(w)
        text_key = "text" if "text" in w else "word"
        if text_key in w_copy:
            w_copy[text_key] = mask_profanity(w_copy[text_key], enabled=True)
        result.append(w_copy)
    
    return result
