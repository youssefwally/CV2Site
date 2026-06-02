#!/usr/bin/env python3
"""Generate website data from a LaTeX CV file.

The script parses a CV written with the provided LaTeX template conventions and
produces a JavaScript payload consumed by the static site.

Usage:
python generate_site_data.py --cv path/to/cv.tex --output code/assets/js/site-data.js --variable window.siteData

"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

DEFAULT_NAME = "Your Name"
DEFAULT_LOCATION = ""
DEFAULT_ROLE = "Professional Profile"

PUBLICATION_METADATA_RAW: dict[str, dict[str, Any]] = {}
VENUE_ALIASES: dict[str, str] = {}
SURNAME_TO_NAME: dict[str, str] = {}
ORGANIZATION_LOCATION_HINTS: dict[str, str] = {}

RESEARCH_FALLBACK_ITEMS: list[dict[str, str]] = [
    {
        "title": "Research and Professional Work",
        "description": "Add your top projects, publications, or presentations here.",
    },
]

MAPPED_SECTION_KEYWORDS: list[str] = [
    "work experience",
    "education",
    "publications talks and posters",
    "professional appointments",
    "professional associations",
    "public outreach",
    "scholarships and grants",
    "service",
    "sevice",
]

SERVICE_SECTION_KEYWORDS: list[str] = [
    "professional appointments",
    "professional associations",
    "public outreach",
    "scholarships and grants",
    "service",
    "sevice",
]

EXCLUDED_UNMAPPED_SECTION_KEYS: set[str] = {
    "appendix", "references"
}

RESERVED_SECTION_IDS: set[str] = {
    "hero",
    "about",
    "research",
    "publications",
    "presentations",
    "experience",
    "education",
    "service",
    "contact",
}

STATIC_NAV_LABELS: dict[str, str] = {
    "about": "About",
    "research": "Research",
    "publications": "Publications",
    "presentations": "Talks",
    "experience": "Experience",
    "education": "Education",
    "service": "Appointments and Outreach",
    "contact": "Contact",
}


def as_sentence(text: Any) -> str:
    if isinstance(text, str):
        return normalize_sentence(text)
    return ""


def as_mapping(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}

    output: dict[str, str] = {}
    for key, value in raw.items():
        key_text = as_sentence(key)
        value_text = as_sentence(value)
        if key_text and value_text:
            output[key_text] = value_text
    return output


def as_sources(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []

    output: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = as_sentence(item.get("label"))
        href = as_sentence(item.get("href"))
        if label and href:
            output.append({"label": label, "href": href})
    return output


def as_publication_metadata(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}

    output: dict[str, dict[str, Any]] = {}
    for title, metadata in raw.items():
        title_text = as_sentence(title)
        if not title_text or not isinstance(metadata, dict):
            continue

        item: dict[str, Any] = {}
        url = as_sentence(metadata.get("url"))
        venue = as_sentence(metadata.get("venue"))
        status = as_sentence(metadata.get("status"))
        sources = as_sources(metadata.get("sources"))

        if url:
            item["url"] = url
        if venue:
            item["venue"] = venue
        if status:
            item["status"] = status
        if sources:
            item["sources"] = sources

        if item:
            output[title_text] = item

    return output


def as_research_fallback_items(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []

    output: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        title = as_sentence(item.get("title"))
        description = as_sentence(item.get("description"))
        if title and description:
            output.append({"title": title, "description": ensure_period(description)})

    return output


def load_overrides(overrides_path: Path) -> None:
    if not overrides_path.exists():
        return

    raw = json.loads(overrides_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Overrides file must contain a JSON object at the top level")

    global PUBLICATION_METADATA_RAW
    global VENUE_ALIASES
    global SURNAME_TO_NAME
    global ORGANIZATION_LOCATION_HINTS
    global RESEARCH_FALLBACK_ITEMS

    publication_metadata = as_publication_metadata(raw.get("publicationMetadata"))
    if publication_metadata:
        PUBLICATION_METADATA_RAW = publication_metadata

    venue_aliases = as_mapping(raw.get("venueAliases"))
    if venue_aliases:
        VENUE_ALIASES = {normalize_key(key): value for key, value in venue_aliases.items()}

    surname_map = as_mapping(raw.get("authorNameMap"))
    if surname_map:
        SURNAME_TO_NAME = {normalize_key(key): value for key, value in surname_map.items()}

    location_hints = as_mapping(raw.get("organizationLocationHints"))
    if location_hints:
        ORGANIZATION_LOCATION_HINTS = {normalize_key(key): value for key, value in location_hints.items()}

    research_fallback_items = as_research_fallback_items(raw.get("researchFallbackItems"))
    if research_fallback_items:
        RESEARCH_FALLBACK_ITEMS = research_fallback_items


def strip_latex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        out: list[str] = []
        index = 0
        while index < len(line):
            char = line[index]
            if char == "%" and (index == 0 or line[index - 1] != "\\"):
                break
            out.append(char)
            index += 1
        lines.append("".join(out))
    return "\n".join(lines)


def parse_braced(text: str, start: int, open_char: str = "{", close_char: str = "}") -> tuple[str, int]:
    if start >= len(text) or text[start] != open_char:
        raise ValueError(f"Expected {open_char!r} at position {start}")

    depth = 0
    buffer: list[str] = []
    index = start

    while index < len(text):
        char = text[index]

        if char == "\\" and index + 1 < len(text):
            nxt = text[index + 1]
            if nxt in "{}[]%":
                if depth > 0:
                    buffer.append(char)
                    buffer.append(nxt)
                index += 2
                continue

        if char == open_char:
            depth += 1
            if depth > 1:
                buffer.append(char)
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return "".join(buffer), index + 1
            buffer.append(char)
        else:
            buffer.append(char)

        index += 1

    raise ValueError(f"Unbalanced braces for block starting at {start}")


def skip_optional_bracket_args(text: str, cursor: int) -> tuple[int, bool]:
    """Advance cursor past optional [..] argument blocks if present."""
    while True:
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1

        if cursor < len(text) and text[cursor] == "[":
            try:
                _, cursor = parse_braced(text, cursor, "[", "]")
            except ValueError:
                return cursor, False
            continue

        return cursor, True


def find_macro_calls(text: str, macro: str, min_args: int = 1, max_args: int | None = None) -> list[list[str]]:
    token = f"\\{macro}"
    index = 0
    calls: list[list[str]] = []

    while True:
        found = text.find(token, index)
        if found == -1:
            break

        token_end = found + len(token)
        if token_end < len(text) and re.match(r"[A-Za-z@]", text[token_end]):
            index = token_end
            continue

        cursor = token_end
        if cursor < len(text) and text[cursor] == "*":
            cursor += 1

        cursor, ok = skip_optional_bracket_args(text, cursor)
        if not ok:
            index = token_end
            continue

        args: list[str] = []
        parse_failed = False

        while True:
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1

            cursor, ok = skip_optional_bracket_args(text, cursor)
            if not ok:
                parse_failed = True
                break

            while cursor < len(text) and text[cursor].isspace():
                cursor += 1

            if cursor >= len(text) or text[cursor] != "{":
                break

            try:
                arg, cursor = parse_braced(text, cursor)
            except ValueError:
                parse_failed = True
                break
            args.append(arg.strip())

            if max_args is not None and len(args) >= max_args:
                break

        if (not parse_failed) and len(args) >= min_args:
            calls.append(args)

        index = token_end

    return calls


def extract_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    token_pattern = re.compile(r"\\section\*?(?![A-Za-z@])")
    index = 0

    while True:
        match = token_pattern.search(text, index)
        if not match:
            break

        cursor = match.end()
        cursor, ok = skip_optional_bracket_args(text, cursor)
        if not ok:
            index = match.end()
            continue

        while cursor < len(text) and text[cursor].isspace():
            cursor += 1

        if cursor >= len(text) or text[cursor] != "{":
            index = match.end()
            continue

        title, after = parse_braced(text, cursor)
        sections.append(
            {
                "title": clean_latex_inline(title),
                "title_raw": title,
                "marker": match.start(),
                "start": after,
            }
        )
        index = after

    for i, section in enumerate(sections):
        end = sections[i + 1]["marker"] if i + 1 < len(sections) else len(text)
        section["end"] = end
        section["content"] = text[section["start"] : end]

    return sections


def extract_subsections(text: str) -> list[dict[str, Any]]:
    subsections: list[dict[str, Any]] = []
    token_pattern = re.compile(r"\\subsection\*?(?![A-Za-z@])")
    index = 0

    while True:
        match = token_pattern.search(text, index)
        if not match:
            break

        cursor = match.end()
        cursor, ok = skip_optional_bracket_args(text, cursor)
        if not ok:
            index = match.end()
            continue

        while cursor < len(text) and text[cursor].isspace():
            cursor += 1

        if cursor >= len(text) or text[cursor] != "{":
            index = match.end()
            continue

        title, after = parse_braced(text, cursor)
        subsections.append(
            {
                "title": clean_latex_inline(title),
                "title_raw": title,
                "marker": match.start(),
                "start": after,
            }
        )
        index = after

    for i, subsection in enumerate(subsections):
        end = subsections[i + 1]["marker"] if i + 1 < len(subsections) else len(text)
        subsection["end"] = end
        subsection["content"] = text[subsection["start"] : end]

    return subsections


def clean_latex_inline(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("\n", " ").replace("\t", " ")
    cleaned = re.sub(r"\\\\+", " ", cleaned)

    replacements = {
        r"\~": " ",
        "~": " ",
        "ø": "o",
        "Ø": "O",
        "å": "a",
        "Å": "A",
        "ä": "a",
        "Ä": "A",
        "ö": "o",
        "Ö": "O",
        "ü": "u",
        "Ü": "U",
        "é": "e",
        "É": "E",
        "è": "e",
        "È": "E",
        r"\&": "&",
        r"\%": "%",
        r"\_": "_",
        r"\#": "#",
        r"\$": "$",
        r"\LaTeX": "LaTeX",
        r"\Cpp": "C++",
        r"\Csharp": "C#",
        r"{\o}": "o",
        r"\o": "o",
        r"{\O}": "O",
        r"\O": "O",
        r"{\aa}": "aa",
        r"\aa": "aa",
        r"\ss": "ss",
        r"\'a": "a",
        r"\'e": "e",
        r"\'i": "i",
        r"\'o": "o",
        r"\'u": "u",
    }

    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    command_with_arg = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}")
    while True:
        updated = command_with_arg.sub(r"\1", cleaned)
        if updated == cleaned:
            break
        cleaned = updated

    cleaned = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", cleaned)
    cleaned = cleaned.replace("{", " ").replace("}", " ")
    cleaned = cleaned.replace("``", '"').replace("''", '"')

    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"\(\s+", "(", cleaned)
    cleaned = re.sub(r"\s+\)", ")", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:-")

    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_sentence(text: str) -> str:
    cleaned = clean_latex_inline(text)
    if not cleaned:
        return ""
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_key(text: str) -> str:
    cleaned = normalize_sentence(text).lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_items(block: str, include_fallback: bool = True) -> list[str]:
    items: list[str] = []
    token = "\\item"
    index = 0

    while True:
        found = block.find(token, index)
        if found == -1:
            break

        token_end = found + len(token)
        if token_end < len(block) and re.match(r"[A-Za-z@]", block[token_end]):
            index = token_end
            continue

        cursor = token_end
        while cursor < len(block) and block[cursor].isspace():
            cursor += 1

        if cursor < len(block) and block[cursor] == "{":
            body, cursor = parse_braced(block, cursor)
            cleaned = normalize_sentence(body)
            if cleaned:
                items.append(cleaned)
            index = cursor
            continue

        next_item = block.find(token, cursor)
        raw = block[cursor : next_item if next_item != -1 else len(block)]
        cleaned = normalize_sentence(raw)
        if cleaned:
            items.append(cleaned)
        index = next_item if next_item != -1 else len(block)

    if items or not include_fallback:
        return items

    fallback = normalize_sentence(block)
    return [fallback] if fallback else []


def extract_itemunit_items(block: str) -> list[str]:
    """Extract nested itemunit-like entries that may not use \\item."""
    items: list[str] = []
    macro_names = sorted(set(re.findall(r"\\([A-Za-z@]*itemunit)\b", block)))

    for macro in macro_names:
        for args in find_macro_calls(block, macro, min_args=1, max_args=6):
            cleaned_args = [normalize_sentence(arg) for arg in args if normalize_sentence(arg)]
            if not cleaned_args:
                continue

            nested_items: list[str] = []
            if args:
                nested_items = [
                    normalize_sentence(item)
                    for item in extract_items(args[-1], include_fallback=False)
                    if normalize_sentence(item)
                ]

            if nested_items and len(cleaned_args) > 1:
                label = cleaned_args[0]
                for nested_item in nested_items:
                    items.append(f"{label}: {nested_item}")
                continue

            if len(cleaned_args) > 1:
                items.append(f"{cleaned_args[0]}: {cleaned_args[-1]}")
            else:
                items.append(cleaned_args[0])

    return dedupe_list(items)


def parse_time_entries(section_text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    macro_pattern = re.compile(r"\\(timeunit|shorttimeunit)\*?(?![A-Za-z@])")

    for match in macro_pattern.finditer(section_text):
        macro = match.group(1)
        min_args = 4 if macro == "timeunit" else 3
        max_args = 6

        cursor = match.end()
        args: list[str] = []
        parse_failed = False

        while len(args) < max_args:
            cursor, ok = skip_optional_bracket_args(section_text, cursor)
            if not ok:
                parse_failed = True
                break

            if cursor >= len(section_text) or section_text[cursor] != "{":
                break

            try:
                arg, cursor = parse_braced(section_text, cursor)
            except ValueError:
                parse_failed = True
                break
            args.append(arg.strip())

        if parse_failed:
            continue

        if len(args) < min_args:
            continue

        detail_blocks = args[3:] if len(args) > 3 else []
        detail_text = " ".join(detail_blocks)

        raw_items: list[str] = []
        for block in detail_blocks:
            raw_items.extend(extract_items(block, include_fallback=False))
            raw_items.extend(extract_itemunit_items(block))

        items = [normalize_sentence(item) for item in raw_items if normalize_sentence(item)]
        if not items:
            fallback = normalize_sentence(detail_text)
            if fallback:
                items = [fallback]

        entries.append(
            {
                "kind": macro,
                "title": normalize_sentence(args[0]),
                "organization": normalize_sentence(args[1]),
                "period": normalize_sentence(args[2]),
                "items": items,
                "body": normalize_sentence(detail_text),
                "marker": match.start(),
            }
        )

    entries.sort(key=lambda entry: entry.get("marker", 0))
    return entries


def get_year(period: str) -> str:
    matches = re.findall(r"(19\d{2}|20\d{2})", period)
    return matches[-1] if matches else normalize_sentence(period)


def get_year_span(period: str) -> str:
    matches = re.findall(r"(19\d{2}|20\d{2})", period)
    if not matches:
        return ""
    if len(matches) == 1:
        return matches[0]
    return f"{matches[0]}-{matches[-1]}"


def period_end_year(period: str) -> int | None:
    matches = re.findall(r"(19\d{2}|20\d{2})", period)
    if not matches:
        return None
    return int(matches[-1])


def is_current_period(period: str) -> bool:
    key = normalize_key(period)
    if any(term in key for term in ["present", "current", "ongoing", "now", "today"]):
        return True

    end_year = period_end_year(period)
    if end_year is None:
        return False

    return end_year >= datetime.datetime.now().year


def normalize_degree_label(label: str) -> str:
    cleaned = normalize_sentence(label)
    degree_key = normalize_key(cleaned)

    if degree_key.startswith("ph d"):
        return re.sub(r"^ph\.?\s*d\.?", "PhD", cleaned, flags=re.IGNORECASE)
    if degree_key.startswith("m sc"):
        return re.sub(r"^m\.?\s*sc\.?", "MSc", cleaned, flags=re.IGNORECASE)
    if degree_key.startswith("b sc"):
        return re.sub(r"^b\.?\s*sc\.?", "BSc", cleaned, flags=re.IGNORECASE)

    return cleaned


def build_entry_role_label(entry: dict[str, Any], source: str) -> str:
    title = normalize_sentence(entry.get("title", ""))
    if source == "education":
        title = normalize_degree_label(title)

    organization = normalize_sentence(entry.get("organization", ""))
    period_text = normalize_sentence(entry.get("period", ""))
    span = get_year_span(period_text)

    display_period = ""
    if period_text and any(term in normalize_key(period_text) for term in ["present", "current", "ongoing", "now", "today"]):
        display_period = period_text
    else:
        display_period = span

    label = f"{title} at {organization}" if title and organization else (title or organization)
    if display_period and label and display_period not in label:
        label = f"{label} ({display_period})"

    return label


def select_current_entry(
    work_entries: list[dict[str, Any]],
    education_entries: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]] | None:
    candidates: list[tuple[str, dict[str, Any]]] = []
    candidates.extend(("work", entry) for entry in work_entries)
    candidates.extend(("education", entry) for entry in education_entries)

    if not candidates:
        return None

    ongoing = [item for item in candidates if is_current_period(item[1].get("period", ""))]
    if ongoing:
        for source, entry in ongoing:
            if source == "work":
                return source, entry
        return ongoing[0]

    def rank(item: tuple[str, dict[str, Any]]) -> tuple[int, int]:
        _, entry = item
        end_year = period_end_year(entry.get("period", ""))
        marker = entry.get("marker", 0)
        return (end_year if end_year is not None else -1, marker)

    return max(candidates, key=rank)


def extract_group_name_from_entry(entry: dict[str, Any] | None) -> str:
    if not entry:
        return ""

    texts: list[str] = []
    texts.extend(entry.get("items", []))
    if entry.get("body"):
        texts.append(entry["body"])

    for text in texts:
        cleaned = normalize_sentence(text)
        if not cleaned:
            continue

        match = re.search(r"\bgroup\s*:\s*([^.;|]+)", cleaned, flags=re.IGNORECASE)
        if match:
            group_name = normalize_sentence(match.group(1))
            if group_name:
                return group_name

    return ""


def select_latest_completed_education(education: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not education:
        return None

    completed = [entry for entry in education if not is_current_period(entry.get("period", ""))]
    pool = completed if completed else education

    def rank(entry: dict[str, Any]) -> tuple[int, str]:
        end_year = period_end_year(entry.get("period", ""))
        return (end_year if end_year is not None else -1, normalize_key(entry.get("degree", "")))

    return max(pool, key=rank)


def guess_location(organization: str) -> str:
    org = normalize_key(organization)

    for hint_key, location in ORGANIZATION_LOCATION_HINTS.items():
        if hint_key and hint_key in org:
            return location

    return ""


def combine_summary(items: list[str], fallback: str, max_items: int = 3) -> list[str]:
    selected = [normalize_sentence(item) for item in items if normalize_sentence(item)][:max_items]
    if selected:
        return selected

    cleaned_fallback = normalize_sentence(fallback)
    return [cleaned_fallback] if cleaned_fallback else []


def dedupe_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        cleaned = normalize_sentence(item)
        if not cleaned:
            continue

        key = cleaned.lower()
        if key in seen:
            continue

        seen.add(key)
        output.append(cleaned)

    return output


def dedupe_mixed(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    output: list[Any] = []

    for item in items:
        if isinstance(item, dict):
            key = json.dumps(item, sort_keys=True, ensure_ascii=True)
        else:
            key = normalize_sentence(str(item)).lower()

        if not key or key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output


def ensure_period(text: str) -> str:
    cleaned = normalize_sentence(text)
    if not cleaned:
        return ""
    if cleaned.endswith((".", "!", "?")):
        return cleaned
    return f"{cleaned}."


def normalize_authors(text: str) -> list[str]:
    cleaned = normalize_sentence(text)
    if not cleaned:
        return []

    if " et al" in cleaned.lower():
        surname_match = re.search(r"([A-Za-z][A-Za-z\-']+)\s*,", cleaned)
        if surname_match:
            surname_key = normalize_key(surname_match.group(1))
            lead = SURNAME_TO_NAME.get(surname_key, surname_match.group(1))
            return [lead, "et al."]
        return [cleaned]

    pair_pattern = re.compile(r"([A-Za-z][A-Za-z\-']+)\s*,\s*([A-Za-z](?:\.[A-Za-z])*\.?)")
    pairs = pair_pattern.findall(cleaned)
    if pairs:
        authors: list[str] = []
        for surname, initials in pairs:
            surname_key = normalize_key(surname)
            if surname_key in SURNAME_TO_NAME:
                authors.append(SURNAME_TO_NAME[surname_key])
            else:
                authors.append(f"{surname} {initials}".strip())
        return dedupe_list(authors)

    fallback_parts = [part.strip() for part in re.split(r"\s*(?:,|&| and )\s*", cleaned) if part.strip()]
    return dedupe_list(fallback_parts) if fallback_parts else [cleaned]


def extract_title_and_trailing(item_text: str, fallback_title: str = "", fallback_venue: str = "") -> tuple[str, str]:
    cleaned = normalize_sentence(item_text)
    cleaned = re.sub(r"^\((?:Poster|Under review)\)\s*", "", cleaned, flags=re.IGNORECASE)

    quote_match = re.search(r'"([^"]+)"\s*(.*)$', cleaned)
    if quote_match:
        title = normalize_sentence(quote_match.group(1))
        trailing = normalize_sentence(quote_match.group(2))
        if trailing.startswith("(") and trailing.endswith(")"):
            trailing = normalize_sentence(trailing[1:-1])
        return title, trailing

    if cleaned:
        return cleaned, normalize_sentence(fallback_venue)

    return normalize_sentence(fallback_title), normalize_sentence(fallback_venue)


def shorten_venue(raw_venue: str) -> str:
    venue = normalize_sentence(raw_venue)
    if not venue:
        return ""

    key = normalize_key(venue)
    for alias_key, alias_value in VENUE_ALIASES.items():
        if alias_key in key:
            return alias_value

    return venue


def dedupe_publications(publications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for publication in publications:
        key = "|".join(
            [
                normalize_key(publication.get("title", "")),
                normalize_key(publication.get("venue", "")),
                normalize_key(publication.get("year", "")),
                normalize_key(publication.get("status", "")),
            ]
        )
        if not key.strip("|") or key in seen:
            continue

        seen.add(key)
        output.append(publication)

    return output


def dedupe_presentations(presentations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for presentation in presentations:
        key = "|".join(
            [
                normalize_key(presentation.get("title", "")),
                normalize_key(presentation.get("event", "")),
                normalize_key(presentation.get("year", "")),
            ]
        )
        if not key.strip("|") or key in seen:
            continue

        seen.add(key)
        output.append(presentation)

    return output


def section_by_keywords(sections: list[dict[str, Any]], keywords: list[str]) -> dict[str, Any] | None:
    for section in sections:
        key = normalize_key(section["title"])
        if any(keyword in key for keyword in keywords):
            return section
    return None


def is_mapped_section_title(title: str) -> bool:
    key = normalize_key(title)
    return any(keyword in key for keyword in MAPPED_SECTION_KEYWORDS)


def slugify_section_id(title: str, used_ids: set[str]) -> str:
    base = normalize_key(title).replace(" ", "-").strip("-")
    if not base:
        base = "section"

    candidate = base
    suffix = 2
    while candidate in used_ids or candidate in RESERVED_SECTION_IDS:
        candidate = f"{base}-{suffix}"
        suffix += 1

    used_ids.add(candidate)
    return candidate


def summarize_time_entry(entry: dict[str, Any]) -> list[str]:
    title = normalize_sentence(entry.get("title", ""))
    organization = normalize_sentence(entry.get("organization", ""))
    period = normalize_sentence(entry.get("period", ""))
    items = combine_summary(entry.get("items", []), entry.get("body", ""), max_items=2)

    lead_parts = [part for part in [title, organization] if part]
    lead = " - ".join(lead_parts)
    if period:
        lead = f"{lead} ({period})" if lead else period

    output: list[str] = []

    if items:
        first = ensure_period(f"{lead}: {items[0]}" if lead else items[0])
        output.append(first)
        for extra in items[1:]:
            output.append(ensure_period(extra))
        return output

    if lead:
        output.append(ensure_period(lead))

    return output


def extract_simpleunit_items(section_text: str) -> list[str]:
    items: list[str] = []
    for args in find_macro_calls(section_text, "simpleunit", min_args=2, max_args=2):
        label = normalize_sentence(args[0])
        label_key = normalize_key(label)

        # Keep references out of generic sections (especially Misc).
        if label_key == "references" or label_key.startswith("references "):
            continue

        raw_items = extract_items(args[1], include_fallback=False)
        if not raw_items:
            raw_items = extract_itemunit_items(args[1])

        cleaned_items = [normalize_sentence(item) for item in raw_items if normalize_sentence(item)]

        if cleaned_items:
            for item in cleaned_items:
                items.append(ensure_period(f"{label}: {item}" if label else item))
        elif label:
            items.append(ensure_period(label))

    return items


def extract_generic_section_items(section_text: str, section_title: str = "", max_items: int = 18) -> list[str]:
    items: list[str] = []

    subsections = extract_subsections(section_text)
    if subsections:
        for subsection in subsections:
            subsection_title = normalize_sentence(subsection.get("title", ""))
            subsection_items = extract_generic_section_items(
                subsection.get("content", ""),
                section_title=section_title,
                max_items=max_items,
            )

            for sub_item in subsection_items:
                if subsection_title:
                    items.append(ensure_period(f"{subsection_title}: {normalize_sentence(sub_item)}"))
                else:
                    items.append(ensure_period(sub_item))

        if items:
            if normalize_key(section_title) == "misc":
                items = [item for item in items if not normalize_key(item).startswith("references")]
            return dedupe_list(items)[:max_items]

    entries = parse_time_entries(section_text)
    if entries:
        for entry in entries:
            items.extend(summarize_time_entry(entry))

    if not items:
        items.extend(extract_simpleunit_items(section_text))

    if not items:
        fallback = [ensure_period(item) for item in extract_items(section_text) if normalize_sentence(item)]
        nested = [ensure_period(item) for item in extract_itemunit_items(section_text) if normalize_sentence(item)]
        items.extend(fallback)
        items.extend(nested)

    # Explicitly remove references from Misc when present in the source CV.
    if normalize_key(section_title) == "misc":
        items = [item for item in items if not normalize_key(item).startswith("references")]

    return dedupe_list(items)[:max_items]


def build_custom_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    custom_sections: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    for section in sections:
        title = normalize_sentence(section.get("title", ""))
        title_key = normalize_key(title)

        if not title or is_mapped_section_title(title):
            continue

        if title_key in EXCLUDED_UNMAPPED_SECTION_KEYS:
            continue

        section_items = extract_generic_section_items(section.get("content", ""), title)
        if not section_items:
            continue

        custom_sections.append(
            {
                "id": slugify_section_id(title, used_ids),
                "title": title,
                "items": section_items,
            }
        )

    return custom_sections


def cv_site_ids_for_section(section_title: str, custom_title_to_id: dict[str, str]) -> list[str]:
    key = normalize_key(section_title)

    if key in EXCLUDED_UNMAPPED_SECTION_KEYS:
        return []

    if "work experience" in key:
        return ["experience"]

    if key == "education":
        return ["education"]

    if "publications talks and posters" in key:
        return ["publications", "presentations"]

    if any(keyword in key for keyword in SERVICE_SECTION_KEYWORDS):
        return ["service"]

    custom_id = custom_title_to_id.get(key)
    if custom_id:
        return [custom_id]

    return []


def build_cv_order_ids(sections: list[dict[str, Any]], custom_sections: list[dict[str, Any]]) -> list[str]:
    custom_title_to_id = {
        normalize_key(section.get("title", "")): section.get("id", "")
        for section in custom_sections
        if section.get("id")
    }

    ordered: list[str] = []
    seen: set[str] = set()

    for section in sections:
        for section_id in cv_site_ids_for_section(section.get("title", ""), custom_title_to_id):
            if section_id in seen:
                continue
            seen.add(section_id)
            ordered.append(section_id)

    return ordered


def build_navigation_items(cv_order_ids: list[str], custom_sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    custom_id_to_title = {
        section.get("id", ""): normalize_sentence(section.get("title", ""))
        for section in custom_sections
        if section.get("id")
    }

    navigation_items: list[dict[str, str]] = [
        {"id": "about", "label": STATIC_NAV_LABELS["about"]},
        {"id": "research", "label": STATIC_NAV_LABELS["research"]},
    ]

    for section_id in cv_order_ids:
        label = STATIC_NAV_LABELS.get(section_id) or custom_id_to_title.get(section_id)
        if not label:
            continue
        navigation_items.append({"id": section_id, "label": label})

    navigation_items.append({"id": "contact", "label": STATIC_NAV_LABELS["contact"]})
    return navigation_items


def location_from_address(address: str) -> str:
    cleaned = normalize_sentence(address)
    if not cleaned:
        return ""

    parts = [normalize_sentence(part) for part in cleaned.split(",") if normalize_sentence(part)]
    if len(parts) < 2:
        return cleaned

    city_part = re.sub(r"^\d+\s*", "", parts[-2]).strip()
    country = parts[-1]

    if city_part and country:
        return f"{city_part}, {country}"

    return cleaned


def publication_metadata_for_title(title: str) -> dict[str, Any]:
    key = normalize_key(title)
    for raw_title, metadata in PUBLICATION_METADATA_RAW.items():
        if normalize_key(raw_title) == key:
            return metadata
    return {}


def build_publications_and_presentations(publication_section: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not publication_section:
        return [], []

    publications: list[dict[str, Any]] = []
    presentations: list[dict[str, Any]] = []

    subsections = extract_subsections(publication_section["content"])
    if not subsections:
        subsections = [{"title": "", "content": publication_section["content"]}]

    for subsection in subsections:
        subsection_key = normalize_key(subsection["title"])
        entries = parse_time_entries(subsection["content"])

        for entry in entries:
            first_item = entry["items"][0] if entry["items"] else entry["body"]
            title_text, trailing = extract_title_and_trailing(
                first_item,
                fallback_title=entry["title"],
                fallback_venue=entry["organization"],
            )
            year = get_year(entry["period"])
            status_tag_match = re.search(r"^\(([^)]+)\)", normalize_sentence(first_item))
            status_tag = normalize_sentence(status_tag_match.group(1)) if status_tag_match else ""

            if "invited talks" in subsection_key or "invited talk" in subsection_key or "panels" in subsection_key:
                presentations.append(
                    {
                        "title": title_text,
                        "event": normalize_sentence(re.sub(r"\s+(19\d{2}|20\d{2})$", "", entry["title"])),
                        "year": year,
                        "type": normalize_sentence(entry["organization"]) or "Talk",
                        "url": "",
                    }
                )
                continue

            if "others" in subsection_key:
                presentations.append(
                    {
                        "title": title_text,
                        "event": shorten_venue(trailing or entry["organization"] or entry["title"]),
                        "year": year,
                        "type": status_tag or "Poster",
                        "url": "",
                    }
                )
                continue

            if "peer reviewed abstracts" in subsection_key:
                status = "Abstract"
            elif "peer reviewed publications" in subsection_key:
                status = "Conference"
            else:
                org_key = normalize_key(entry["organization"])
                if "invited speaker" in org_key or "oral presentation" in org_key:
                    presentations.append(
                        {
                            "title": title_text,
                            "event": normalize_sentence(re.sub(r"\s+(19\d{2}|20\d{2})$", "", entry["title"])),
                            "year": year,
                            "type": normalize_sentence(entry["organization"]) or "Presentation",
                            "url": "",
                        }
                    )
                    continue
                status = ""

            publication = {
                "title": title_text,
                "venue": shorten_venue(trailing or entry["organization"] or "Research"),
                "year": year,
                "status": status,
                "authors": normalize_authors(entry["title"]),
                "url": "",
            }

            metadata = publication_metadata_for_title(publication["title"])
            if metadata:
                publication["url"] = metadata.get("url", publication["url"])
                publication["venue"] = metadata.get("venue", publication["venue"])
                publication["status"] = metadata.get("status", publication["status"])
                if metadata.get("sources"):
                    publication["sources"] = metadata["sources"]

            publications.append(publication)

    publications = dedupe_publications(publications)
    presentations = dedupe_presentations(presentations)
    return publications, presentations


def make_service_item(entry: dict[str, Any]) -> str:
    title = normalize_sentence(entry.get("title", ""))
    org = normalize_sentence(entry.get("organization", ""))
    period = normalize_sentence(entry.get("period", ""))

    item_text = ""
    if entry.get("items"):
        item_text = normalize_sentence(entry["items"][0])

    segments = [segment for segment in [title, org] if segment]
    lead = " - ".join(segments)
    if period:
        lead = f"{lead} ({period})" if lead else period

    if item_text:
        return f"{lead}: {item_text}" if lead else item_text
    return lead


def pick_service_bucket(entry: dict[str, Any], section_title: str) -> str:
    title_key = normalize_key(entry.get("title", ""))
    org_key = normalize_key(entry.get("organization", ""))
    section_key = normalize_key(section_title)
    item_keys = [normalize_key(item) for item in entry.get("items", []) if normalize_sentence(item)]
    corpus = " ".join([title_key, org_key, section_key, *item_keys])

    if any(keyword in section_key for keyword in ["public outreach", "scholarships", "grants"]):
        return "outreach"

    if any(keyword in corpus for keyword in ["mentor", "supervis", "advisor", "advising", "teaching assistant"]):
        return "mentoring"

    if any(
        keyword in corpus
        for keyword in [
            "review",
            "reviewer",
            "committee",
            "session chair",
            "moderation",
            "organization",
            "organizing",
            "workshop",
            "conference",
            "association",
        ]
    ):
        return "community"

    if any(
        keyword in corpus
        for keyword in [
            "outreach",
            "grant",
            "scholarship",
            "travel",
            "volunteer",
            "public engagement",
            "speaker",
            "panel",
        ]
    ):
        return "outreach"

    return "appointments"


def summarize_service_entry(entry: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    head = ensure_period(make_service_item(entry))
    if head:
        lines.append(head)

    extra_items = [ensure_period(item) for item in entry.get("items", [])[1:3] if normalize_sentence(item)]
    lines.extend(extra_items)

    if not lines:
        fallback = normalize_sentence(entry.get("body", ""))
        if fallback:
            lines.append(ensure_period(fallback))

    return dedupe_list(lines)


def bucket_for_generic_service_text(text: str, section_title: str) -> str:
    key = normalize_key(f"{section_title} {text}")

    if any(keyword in key for keyword in ["mentor", "supervis", "advisor", "teaching assistant"]):
        return "mentoring"
    if any(keyword in key for keyword in ["review", "committee", "organization", "association", "conference"]):
        return "community"
    if any(keyword in key for keyword in ["outreach", "grant", "scholarship", "travel", "speaker", "panel"]):
        return "outreach"

    return "appointments"


def build_service(sections: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[Any]] = {
        "appointments": [],
        "mentoring": [],
        "community": [],
        "outreach": [],
    }

    for section in sections:
        section_title = normalize_sentence(section.get("title", ""))
        section_key = normalize_key(section_title)
        if not any(keyword in section_key for keyword in SERVICE_SECTION_KEYWORDS):
            continue

        entries = parse_time_entries(section.get("content", ""))
        if entries:
            for entry in entries:
                bucket = pick_service_bucket(entry, section_title)
                grouped[bucket].extend(summarize_service_entry(entry))
            continue

        generic_items = extract_generic_section_items(
            section.get("content", ""),
            section_title=section_title or "Service",
            max_items=24,
        )
        for item in generic_items:
            bucket = bucket_for_generic_service_text(item, section_title)
            grouped[bucket].append(ensure_period(item))

    return {
        "appointments": dedupe_mixed(grouped["appointments"]),
        "mentoringAndSupervision": dedupe_mixed(grouped["mentoring"]),
        "community": dedupe_mixed(grouped["community"]),
        "outreachAndGrants": dedupe_mixed(grouped["outreach"]),
    }


def dedupe_casefold(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        cleaned = normalize_sentence(item)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(cleaned)

    return output


def normalize_url(url: str) -> str:
    cleaned = normalize_sentence(url)
    if not cleaned:
        return ""

    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned):
        return cleaned

    if cleaned.startswith("www."):
        return f"https://{cleaned}"

    return cleaned


def profile_label_from_url(url: str) -> str:
    lowered = normalize_url(url).lower()
    host = re.sub(r"^https?://", "", lowered).split("/")[0]

    if "github.com" in host:
        return "GitHub"
    if "linkedin.com" in host:
        return "LinkedIn"
    if "scholar.google" in host:
        return "Google Scholar"
    if "orcid.org" in host:
        return "ORCID"
    if "openreview.net" in host:
        return "OpenReview"

    if host.startswith("www."):
        host = host[4:]

    return host or "Profile"


def build_contact_links(urls: list[str]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw_url in urls:
        href = normalize_url(raw_url)
        if not href:
            continue

        key = href.lower()
        if key in seen:
            continue
        seen.add(key)

        links.append(
            {
                "label": profile_label_from_url(href),
                "handle": re.sub(r"^https?://", "", href),
                "href": href,
            }
        )

    return links


def extract_skills_from_text(text: str) -> list[str]:
    cleaned = normalize_sentence(text)
    if not cleaned:
        return []

    cleaned = re.sub(r"^[A-Za-z][A-Za-z\s&/+\-]{0,40}:\s*", "", cleaned)
    cleaned = re.sub(
        r"^(advanced|intermediate|beginner|expert|proficient)\s*:?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    parts = [normalize_sentence(part) for part in re.split(r"[,;/]", cleaned) if normalize_sentence(part)]
    skills: list[str] = []

    for part in parts:
        normalized = re.sub(
            r"^(advanced|intermediate|beginner|expert|proficient)\s*:?",
            "",
            part,
            flags=re.IGNORECASE,
        )
        normalized = normalize_sentence(normalized)
        if not normalized:
            continue
        if len(normalized) > 40:
            continue
        skills.append(normalized)

    return dedupe_casefold(skills)


def build_about_skills(sections: list[dict[str, Any]]) -> list[str]:
    skills_section = section_by_keywords(sections, ["computer skills", "technical skills", "skills"])
    if not skills_section:
        return []

    candidates: list[str] = []
    for args in find_macro_calls(skills_section.get("content", ""), "simpleunit", min_args=2, max_args=2):
        nested_items = extract_items(args[1], include_fallback=False)
        if not nested_items:
            nested_items = extract_itemunit_items(args[1])
        if not nested_items:
            nested_items = [args[1]]

        for item in nested_items:
            candidates.extend(extract_skills_from_text(item))

    if not candidates:
        for generic_item in extract_generic_section_items(skills_section.get("content", ""), "computer skills", max_items=40):
            candidates.extend(extract_skills_from_text(generic_item))

    return dedupe_casefold(candidates)[:24]


def build_dynamic_research_items(
    publications: list[dict[str, Any]],
    presentations: list[dict[str, Any]],
    experience: list[dict[str, Any]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []

    for publication in publications:
        if len(items) >= 6:
            break

        title = normalize_sentence(publication.get("title", ""))
        if not title:
            continue

        venue = normalize_sentence(publication.get("venue", ""))
        year = normalize_sentence(publication.get("year", ""))
        if venue and year:
            description = f"Published at {venue} ({year})."
        elif venue:
            description = f"Published at {venue}."
        elif year:
            description = f"Published in {year}."
        else:
            description = "Peer-reviewed research output."

        items.append({"title": title, "description": description})

    for presentation in presentations:
        if len(items) >= 6:
            break

        title = normalize_sentence(presentation.get("title", ""))
        if not title:
            continue

        event = normalize_sentence(presentation.get("event", ""))
        year = normalize_sentence(presentation.get("year", ""))
        desc_base = f"Presented at {event}" if event else "Presented work"
        description = f"{desc_base} ({year})." if year else ensure_period(desc_base)
        items.append({"title": title, "description": description})

    for entry in experience:
        if len(items) >= 6:
            break

        role = normalize_sentence(entry.get("role", ""))
        organization = normalize_sentence(entry.get("organization", ""))
        if not role:
            continue

        title = f"{role} at {organization}" if organization else role
        highlights = entry.get("highlights", [])
        highlight = normalize_sentence(highlights[0]) if highlights else ""
        description = ensure_period(highlight) if highlight else "Applied research and engineering experience."
        items.append({"title": title, "description": description})

    deduped: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    for item in items:
        title_key = normalize_key(item.get("title", ""))
        if not title_key or title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        deduped.append(item)

    return deduped


def build_about_paragraphs(
    name: str,
    current_role: str,
    experience: list[dict[str, Any]],
    publications: list[dict[str, Any]],
    presentations: list[dict[str, Any]],
) -> list[str]:
    paragraphs: list[str] = []

    if current_role:
        paragraphs.append(f"{name} currently works as {current_role}.")

    organizations = dedupe_casefold([entry.get("organization", "") for entry in experience])
    if organizations:
        top_orgs = organizations[:3]
        if len(top_orgs) == 1:
            paragraphs.append(f"Recent experience includes work at {top_orgs[0]}.")
        else:
            paragraphs.append(f"Recent experience includes work at {', '.join(top_orgs[:-1])}, and {top_orgs[-1]}.")

    return dedupe_casefold(paragraphs)


def build_data(cv_text: str) -> dict[str, Any]:
    content = strip_latex_comments(cv_text)
    sections = extract_sections(content)

    header_calls = find_macro_calls(content, "headerinfo", min_args=4, max_args=10)
    header = header_calls[0] if header_calls else [DEFAULT_NAME, "", "", "", "", ""]

    name = clean_latex_inline(header[0]) if len(header) > 0 else DEFAULT_NAME
    address = clean_latex_inline(header[1]) if len(header) > 1 else ""
    phone = clean_latex_inline(header[2]) if len(header) > 2 else ""
    email = clean_latex_inline(header[3]) if len(header) > 3 else ""

    profile_urls = [
        normalize_url(clean_latex_inline(arg))
        for arg in header[4:]
        if normalize_url(clean_latex_inline(arg))
    ]
    github = next((url for url in profile_urls if "github.com" in url.lower()), "")
    linkedin = next((url for url in profile_urls if "linkedin.com" in url.lower()), "")
    extra_profile_urls = [url for url in profile_urls if url not in {github, linkedin}]

    if not name:
        name = DEFAULT_NAME

    work_section = section_by_keywords(sections, ["work experience"])
    education_section = section_by_keywords(sections, ["education"])
    publication_section = section_by_keywords(sections, ["publications talks and posters"])

    work_entries = parse_time_entries(work_section["content"]) if work_section else []
    education_entries = parse_time_entries(education_section["content"]) if education_section else []

    experience: list[dict[str, Any]] = []
    for entry in work_entries:
        location = guess_location(entry["organization"])
        highlights = combine_summary(entry["items"], entry["body"], max_items=3)
        experience.append(
            {
                "role": entry["title"],
                "organization": entry["organization"],
                "location": location,
                "period": entry["period"],
                "highlights": highlights,
            }
        )

    education: list[dict[str, Any]] = []
    for entry in education_entries:
        note = " ".join(combine_summary(entry["items"], entry["body"], max_items=2))
        degree = entry["title"]
        degree_key = normalize_key(degree)

        if "ph d" in degree_key or "phd" in degree_key:
            degree = re.sub(r"^ph\.?\s*d\.?", "PhD", degree, flags=re.IGNORECASE)
        elif degree_key.startswith("m sc"):
            degree = re.sub(r"^m\.?\s*sc\.?", "MSc", degree, flags=re.IGNORECASE)
        elif degree_key.startswith("b sc"):
            degree = re.sub(r"^b\.?\s*sc\.?", "BSc", degree, flags=re.IGNORECASE)

        education.append(
            {
                "degree": degree,
                "school": entry["organization"],
                "period": entry["period"],
                "note": note,
            }
        )

    publications, presentations = build_publications_and_presentations(publication_section)
    custom_sections = build_custom_sections(sections)
    location = location_from_address(address)

    current_selection = select_current_entry(work_entries, education_entries)
    current_source = current_selection[0] if current_selection else ""
    current_entry = current_selection[1] if current_selection else None

    primary_institution = ""
    if current_entry and current_entry.get("organization"):
        primary_institution = normalize_sentence(current_entry["organization"])
    elif experience and experience[0].get("organization"):
        primary_institution = normalize_sentence(experience[0]["organization"])
    elif education and education[0].get("school"):
        primary_institution = normalize_sentence(education[0]["school"])

    if current_entry:
        current_role_value = build_entry_role_label(current_entry, current_source)
    elif experience:
        current_role_value = f"{experience[0]['role']} at {experience[0]['organization']}"
    else:
        current_role_value = DEFAULT_ROLE

    if not location:
        location = guess_location(primary_institution) or DEFAULT_LOCATION

    current_group_value = extract_group_name_from_entry(current_entry)

    quick_facts: list[dict[str, Any]] = [
        {
            "key": "Current Role",
            "value": current_role_value,
        }
    ]

    if primary_institution:
        quick_facts.append(
            {
                "key": "Primary Organization",
                "value": primary_institution,
            }
        )

    latest_completed_education = select_latest_completed_education(education)
    if latest_completed_education:
        degree_text = normalize_sentence(latest_completed_education.get("degree", ""))
        if degree_text:
            span = get_year_span(latest_completed_education.get("period", ""))
            summary = f"{degree_text} ({span})" if span else degree_text
            quick_facts.append({"key": "Latest Degree", "value": summary})

    if location:
        quick_facts.append({"key": "Location", "value": location})
    if email:
        quick_facts.append({"key": "Email", "value": email})
    if phone:
        quick_facts.append({"key": "Phone", "value": phone})

    contact_links = build_contact_links([github, linkedin, *extra_profile_urls])

    about_skills = build_about_skills(sections)
    if not about_skills:
        about_skills = [
            "Python",
            "PyTorch",
            "Machine Learning",
            "Data Analysis",
            "Research",
        ]

    research_items = build_dynamic_research_items(publications, presentations, experience)
    if not research_items:
        research_items = RESEARCH_FALLBACK_ITEMS

    about_paragraphs = build_about_paragraphs(name, current_role_value, experience, publications, presentations)

    hero_summary = "Profile generated directly from the provided LaTeX CV."
    if current_group_value:
        hero_summary = ensure_period(f"Group: {current_group_value}")
    elif current_entry and current_entry.get("items"):
        hero_summary = ensure_period(current_entry["items"][0])
    elif experience and experience[0].get("highlights"):
        hero_summary = ensure_period(experience[0]["highlights"][0])
    elif publications or presentations:
        hero_summary = (
            f"This profile includes {len(publications)} publications and {len(presentations)} talks or posters."
        )

    hero_eyebrow_parts = [part for part in [current_role_value, location] if normalize_sentence(part)]
    hero_eyebrow = " | ".join(hero_eyebrow_parts) if hero_eyebrow_parts else name

    hero_actions: list[dict[str, str]] = []
    if email:
        hero_actions.append({"label": "Email", "href": f"mailto:{email}", "style": "primary"})
    if github:
        hero_actions.append({"label": "GitHub", "href": github, "style": "outline"})
    if linkedin:
        hero_actions.append({"label": "LinkedIn", "href": linkedin, "style": "outline"})
    if not hero_actions and contact_links:
        hero_actions.append({"label": contact_links[0]["label"], "href": contact_links[0]["href"], "style": "primary"})
    if not hero_actions:
        hero_actions.append({"label": "Contact", "href": "#contact", "style": "primary"})

    service = build_service(sections)
    cv_order_ids = build_cv_order_ids(sections, custom_sections)
    navigation_items = build_navigation_items(cv_order_ids, custom_sections)

    data: dict[str, Any] = {
        "seo": {
            "title": f"{name} | Professional Profile",
            "description": f"Professional profile website for {name}, generated from a LaTeX CV source.",
        },
        "identity": {
            "name": name,
            "initials": "".join(part[0].upper() for part in name.split()[:2]) if name else "NA",
        },
        "navigation": navigation_items,
        "hero": {
            "eyebrow": hero_eyebrow,
            "role": current_role_value,
            "summary": hero_summary,
            "actions": hero_actions,
        },
        "quickFacts": quick_facts,
        "about": {
            "paragraphs": about_paragraphs,
            "skills": about_skills,
        },
        "research": research_items,
        "publications": publications,
        "presentations": presentations,
        "experience": experience,
        "education": education,
        "service": service,
        "customSections": custom_sections,
        "contact": {
            "title": "Open to collaboration opportunities.",
            "intro": "Use the contact methods below to get in touch.",
            "email": email,
            "links": contact_links,
        },
        "footer": {
            "institution": primary_institution or DEFAULT_ROLE,
            "location": location,
        },
    }

    validate_payload(data)
    return data


def validate_payload(payload: dict[str, Any]) -> None:
    required_keys = {
        "seo",
        "identity",
        "navigation",
        "hero",
        "quickFacts",
        "about",
        "research",
        "publications",
        "presentations",
        "experience",
        "education",
        "service",
        "customSections",
        "contact",
        "footer",
    }

    missing = sorted(key for key in required_keys if key not in payload)
    if missing:
        raise ValueError(f"Generated payload is missing keys: {', '.join(missing)}")

    for list_key in ["navigation", "publications", "presentations", "experience", "education", "customSections"]:
        if not isinstance(payload.get(list_key), list):
            raise ValueError(f"Generated payload field '{list_key}' must be a list")


def custom_sections_runtime_js() -> str:
    return """(function () {
    if (typeof window === \"undefined\" || typeof document === \"undefined\") {
        return;
    }

    function getData() {
        return window.siteData || window.testSiteData || null;
    }

    function ensureNavLinks(customSections) {
        var navList = document.getElementById(\"navList\");
        if (!navList) {
            return;
        }

        customSections.forEach(function (section) {
            if (!section || !section.id) {
                return;
            }

            if (navList.querySelector('a[href=\"#' + section.id + '\"]')) {
                return;
            }

            var li = document.createElement(\"li\");
            var a = document.createElement(\"a\");
            a.href = \"#\" + section.id;
            a.textContent = section.title || section.id;
            li.appendChild(a);
            navList.appendChild(li);
        });
    }

    function buildSectionNode(section) {
        var node = document.createElement(\"section\");
        node.id = section.id;

        var container = document.createElement(\"div\");
        container.className = \"container\";

        var header = document.createElement(\"div\");
        header.className = \"section-header\";

        var number = document.createElement(\"div\");
        number.className = \"section-num\";
        number.textContent = \"00\";

        var heading = document.createElement(\"h2\");
        heading.textContent = section.title || section.id;

        var line = document.createElement(\"div\");
        line.className = \"section-line\";

        header.appendChild(number);
        header.appendChild(heading);
        header.appendChild(line);

        var card = document.createElement(\"article\");
        card.className = \"research-card fade-in visible\";

        var list = document.createElement(\"ul\");
        list.className = \"service-list\";

        var items = Array.isArray(section.items) ? section.items : [];
        items.forEach(function (itemText) {
            var li = document.createElement(\"li\");
            li.textContent = itemText;
            list.appendChild(li);
        });

        if (!items.length) {
            var li = document.createElement(\"li\");
            li.textContent = \"No content extracted for this section yet.\";
            list.appendChild(li);
        }

        card.appendChild(list);
        container.appendChild(header);
        container.appendChild(card);
        node.appendChild(container);
        return node;
    }

    function getDesiredOrder(data) {
        var ordered = [\"hero\"];
        var nav = Array.isArray(data && data.navigation) ? data.navigation : [];

        nav.forEach(function (item) {
            if (item && item.id) {
                ordered.push(item.id);
            }
        });

        var deduped = [];
        ordered.forEach(function (id) {
            if (deduped.indexOf(id) === -1) {
                deduped.push(id);
            }
        });

        return deduped;
    }

    function appendMissingCustomSections(data) {
        if (!Array.isArray(data.customSections) || !data.customSections.length) {
            return;
        }

        var footer = document.querySelector(\"footer\");
        var body = document.body;

        data.customSections.forEach(function (section) {
            if (!section || !section.id) {
                return;
            }

            if (document.getElementById(section.id)) {
                return;
            }

            var node = buildSectionNode(section);
            if (footer) {
                body.insertBefore(node, footer);
            } else {
                body.appendChild(node);
            }
        });
    }

    function reorderSections(data) {
        var footer = document.querySelector(\"footer\");
        var body = document.body;
        var desiredOrder = getDesiredOrder(data);

        desiredOrder.forEach(function (sectionId) {
            var section = document.getElementById(sectionId);
            if (!section || section.tagName.toLowerCase() !== \"section\") {
                return;
            }

            if (footer) {
                body.insertBefore(section, footer);
            } else {
                body.appendChild(section);
            }
        });

        var counter = 1;
        desiredOrder.forEach(function (sectionId) {
            if (sectionId === \"hero\") {
                return;
            }

            var section = document.getElementById(sectionId);
            if (!section || section.tagName.toLowerCase() !== \"section\") {
                return;
            }

            var num = section.querySelector(\".section-num\");
            if (num) {
                num.textContent = String(counter).padStart(2, \"0\");
            }
            counter += 1;
        });
    }

    function renderCustomSections() {
        var data = getData();
        if (!data) {
            return;
        }

        if (Array.isArray(data.customSections) && data.customSections.length) {
            ensureNavLinks(data.customSections);
            appendMissingCustomSections(data);
        }

        reorderSections(data);
    }

    if (document.readyState === \"loading\") {
        document.addEventListener(\"DOMContentLoaded\", function () {
            setTimeout(renderCustomSections, 0);
        });
    } else {
        setTimeout(renderCustomSections, 0);
    }
})();
"""


def resolve_project_path(path_arg: str, project_root: Path) -> Path:
    path = Path(path_arg).expanduser()
    if path.is_absolute():
        return path
    return project_root / path


def write_js_data(output_path: Path, payload: dict[str, Any], variable_name: str = "window.siteData") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, ensure_ascii=True)
    output = f"{variable_name} = {serialized};\n\n{custom_sections_runtime_js()}"
    output_path.write_text(output, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate website site-data.js from a LaTeX CV source.")
    parser.add_argument(
        "--cv",
        default="CV/latex_tamplate.tex",
        help="Path to LaTeX CV file (default: CV/latex_tamplate.tex)",
    )
    parser.add_argument(
        "--output",
        default="code/assets/js/site-data.js",
        help="Output JS file path (default: code/assets/js/site-data.js)",
    )
    parser.add_argument(
        "--variable",
        default="window.siteData",
        help="JS variable assignment target (default: window.siteData)",
    )
    parser.add_argument(
        "--overrides",
        default="code/scripts/site-data.overrides.json",
        help=(
            "Optional JSON file with metadata aliases and parser hints "
            "(default: code/scripts/site-data.overrides.json)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    project_root = Path(__file__).resolve().parents[2]

    overrides_path = resolve_project_path(args.overrides, project_root)
    load_overrides(overrides_path)

    cv_path = resolve_project_path(args.cv, project_root)
    if not cv_path.exists():
        raise FileNotFoundError(f"CV file not found: {cv_path}")

    cv_text = cv_path.read_text(encoding="utf-8", errors="ignore")
    payload = build_data(cv_text)

    output_path = resolve_project_path(args.output, project_root)
    write_js_data(output_path, payload, variable_name=args.variable)

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
