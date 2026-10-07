"""Output sanitiser — strips prompt injection patterns before tool output reaches the LLM.

Design notes
------------
Patterns are chosen to match known prompt-injection phrasing while minimising
false positives on legitimate tool output (e.g. grep hits, log lines, code).

Over-broad patterns that cause false positives — such as matching any word
ending in 'system' followed by ':' — are intentionally avoided.  The pattern
for the 'system' role targets the ChatML / OpenAI message-role format
(a line that begins with exactly the word 'system' followed by a colon) rather
than any occurrence of the substring.
"""
import re

# Each entry: (compiled_pattern, human_readable_name)
_INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # "ignore [all] previous instructions …"
    (re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE), "ignore-instructions"),
    # Role-prefix injection: a line that starts with the literal word "system:"
    # Uses ^ with MULTILINE so it only matches at the beginning of a line, not
    # mid-sentence (avoids false positives on "file system:", "operating system:", etc.)
    (re.compile(r"(?m)^\s*system\s*:", re.IGNORECASE), "system-role-prefix"),
    # ChatML / LLaMA token delimiters
    (re.compile(r"<\|", re.IGNORECASE), "chatml-open"),
    (re.compile(r"\|>", re.IGNORECASE), "chatml-close"),
    # Instruction-tuning delimiters
    (re.compile(r"\[INST\]", re.IGNORECASE), "inst-tag"),
    (re.compile(r"\[/INST\]", re.IGNORECASE), "inst-close-tag"),
    # Identity-switch phrases
    (re.compile(r"you\s+are\s+now\b", re.IGNORECASE), "identity-switch"),
    (re.compile(r"new\s+instructions\s*:", re.IGNORECASE), "new-instructions"),
    # DAN / jailbreak prefix patterns
    (re.compile(r"\bDAN\s+mode\b", re.IGNORECASE), "dan-mode"),
    (re.compile(r"ignore\s+all\s+safety", re.IGNORECASE), "ignore-safety"),
]

_REPLACEMENT = "[REDACTED:potential-injection]"


def sanitise(text: str) -> str:
    """Sanitise tool output, replacing known prompt-injection patterns.

    Returns the sanitised string unchanged if no patterns match.
    Logs (at DEBUG level) when a redaction occurs to aid security auditing.
    """
    for pattern, name in _INJECTION_PATTERNS:
        new_text = pattern.sub(_REPLACEMENT, text)
        if new_text is not text and new_text != text:
            import logging
            logging.getLogger(__name__).debug(
                "sanitiser: redacted pattern '%s' from tool output", name
            )
            text = new_text
    return text
