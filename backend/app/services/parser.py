"""Structural wine name parser — no hardcoded region/producer lists.

Parsing strategy (structural signals only):

1. Extract vintage (regex: 4-digit year)
2. Extract format (regex: 750ml, 1.5L, etc.)
3. Extract classification (regex: Grand Cru, Premier Cru, Riserva, etc.)
4. Extract quoted segments → these are always cuvée/vineyard names
   (e.g. 'Monts Luisants', 'Vin Noir', 'Bussia Dardi Le Rose')
5. Producer: consecutive tokens from position 0, bounded by:
   - Prefix tokens (Domaine, Château, Weingut, etc.) — small universal set
   - Connector tokens (du, de, la, von, van) — grammatical
   - 1-2 proper-name tokens after that
   - Stop signals: grape varieties, cuvée-markers (Cuvée, Clos, Lieu-dit),
     vineyard indicators (Vineyard, Estate, Ranch)
6. Appellation/region = capitalized tokens between producer and quoted/cuvée section
7. Vineyard = first quoted segment if any, else trailing capitalized words
"""
import re
from typing import List, Optional, Set

from app.models.sku import WineSKUInput, ParsedSKU, SearchQuery
from app.core.constants import SYNONYM_MAPPINGS


# ── Universal linguistic constants (not hardcoded region lists) ──

# Producer prefixes — ~15 linguistic tokens used globally
PRODUCER_PREFIXES: Set[str] = {
    'domaine', 'chateau', 'château', 'mas', 'maison',
    'weingut', 'bodega', 'tenuta', 'cantina', 'quinta', 'poderi',
    'azienda', 'fattoria', 'cave', 'cellars',
}

# Grammatical connectors — universal, used in many languages
CONNECTORS: Set[str] = {
    'du', 'de', 'des', 'la', 'le', 'les', "l'", "d'",
    'di', 'del', 'della', 'delle', 'degli', 'dello',
    'von', 'van', 'der', 'und', 'af', 'of', 'the',
}

# Prefix markers — these words START a cuvée/vineyard description.
# When seen, everything from here on is non-producer content.
# (e.g. "Cuvée des Crayères", "Clos des Porrets", "Lieu-dit Foo")
PREFIX_MARKERS: Set[str] = {
    'cuvée', 'cuvee', 'clos', 'lieu-dit', 'climat',
    'selection', 'sélection',
}

# Suffix markers — these words FOLLOW a name word that is part of the
# vineyard/estate name. (e.g. "Graveyard Vineyard", "Watson Ranch")
# Note: 'estate' is intentionally NOT here — it's commonly part of producer
# names (e.g. "Roederer Estate").
SUFFIX_MARKERS: Set[str] = {
    'vineyard', 'vineyards', 'ranch', 'winery', 'block',
}

# Combined for general stop checks
NON_PRODUCER_MARKERS: Set[str] = PREFIX_MARKERS | SUFFIX_MARKERS

# Grape varieties — domain knowledge, but these are universal
# (not tied to specific regions). Used to detect end of producer name.
GRAPE_VARIETIES: Set[str] = {
    'riesling', 'chardonnay', 'pinot', 'noir', 'blanc', 'gris', 'grigio',
    'cabernet', 'sauvignon', 'franc', 'merlot', 'syrah', 'shiraz',
    'grenache', 'tempranillo', 'nebbiolo', 'sangiovese', 'barbera',
    'malbec', 'zinfandel', 'viognier', 'roussanne', 'marsanne',
    'semillon', 'sémillon', 'gewurztraminer', 'gewürztraminer',
    'pinotage', 'carmenere', 'cinsault', 'mourvedre', 'monastrell',
    'corvina', 'rondinella', 'garganega', 'albarino', 'albariño',
    'verdejo', 'godello', 'treixadura', 'furmint', 'blaufränkisch',
    'zweigelt', 'sylvaner', 'traminer', 'silvaner', 'chenin',
    'muscat', 'vermentino', 'falanghina', 'aglianico', 'dolcetto',
    'gamay', 'chasselas', 'trousseau', 'picpoul', 'arneis',
}

# Classification regex patterns — structural, not lists
CLASSIFICATION_PATTERNS = [
    r'\b(Grand Cru Class[eé])\b',
    r'\b(Grand Cru)\b',
    r'\b(Premier Cru|1er Cru|1er-Cru)\b',
    r'\b(Villages?)\b',
    r'\b(Vendanges Tardives|VT)\b',
    r'\b(Sélection de Grains Nobles|Selection de Grains Nobles|SGN)\b',
    r'\b(Riserva|Reserva)\b',
    r'\b(Gran Reserva|Gran Riserva)\b',
    r'\b(Auslese|Spätlese|Kabinett|Trockenbeerenauslese|Eiswein|Beerenauslese)\b',
    r'\b(Extra Brut|Brut Nature|Brut|Demi-Sec|Sec|Doux)\b',
    r'\b(Blanc de Blancs|Blanc de Noirs)\b',
]

VINTAGE_PATTERN = r'\b(19\d{2}|20\d{2})\b'
FORMAT_PATTERN = r'(\d+(?:\.\d+)?)\s*(ml|mL|ML|cl|cL|CL|L|l)\b'

# Pattern for single-quoted segments: 'Monts Luisants', ‘Cuvée X’, etc.
# Supports straight quotes and curly/typographic quotes
QUOTED_PATTERN = r"[''‘']([^''‘']+)[''’']|\"([^\"]+)\""


class WineParser:
    def __init__(self):
        self.classification_regexes = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in CLASSIFICATION_PATTERNS]
        self.vintage_regex = re.compile(VINTAGE_PATTERN)
        self.format_regex = re.compile(FORMAT_PATTERN, re.IGNORECASE)
        self.quoted_regex = re.compile(QUOTED_PATTERN)

    def parse(self, input_data: WineSKUInput) -> ParsedSKU:
        raw_name = input_data.wine_name

        # Step 1: extract structural elements
        vintage = input_data.vintage or self._extract_vintage(raw_name)
        format_ml = self._extract_format(input_data.format) if input_data.format else None
        classification = self._extract_classification(raw_name)

        # Step 2: extract quoted segments (cuvée/vineyard names)
        quoted_segments, name_sans_quotes = self._extract_quoted(raw_name)

        # Step 3: strip classification and vintage from the working name
        working = name_sans_quotes
        if classification:
            working = re.sub(r'\b' + re.escape(classification) + r'\b', '', working, flags=re.IGNORECASE)
        working = self.vintage_regex.sub('', working)
        # Remove format tokens (750ml etc.)
        working = self.format_regex.sub('', working)
        working = re.sub(r'\s+', ' ', working).strip(' ,;.')

        # Step 4: extract producer from the start of working name
        producer, after_producer = self._extract_producer(working)

        # Step 5: what's left after producer is appellation + possibly a tail
        # If we have quoted segments, the tail (non-quoted middle) is appellation
        # If no quotes, try to split: appellation = capitalized words, vineyard = grape-adjacent
        appellation = self._extract_appellation(after_producer)

        # Step 6: vineyard — prefer first quoted segment, else derive from remainder
        vineyard = None
        cuvee = None
        if quoted_segments:
            # The first quoted segment is typically the cuvée/vineyard
            vineyard = quoted_segments[0]
            # Additional quoted segments go into cuvee
            if len(quoted_segments) > 1:
                cuvee = quoted_segments[1]
        else:
            # No quotes — try to extract vineyard from trailing remainder
            vineyard = self._extract_vineyard_from_tail(after_producer, appellation)

        normalized_tokens = self._create_tokens(
            producer, appellation, vineyard, classification, vintage
        )

        return ParsedSKU(
            raw_name=raw_name,
            producer=producer,
            producer_normalized=self._normalize_text(producer) if producer else None,
            appellation=appellation,
            appellation_normalized=self._normalize_text(appellation) if appellation else None,
            vineyard=vineyard,
            vineyard_normalized=self._normalize_text(vineyard) if vineyard else None,
            classification=classification,
            classification_normalized=self._normalize_text(classification) if classification else None,
            cuvee=cuvee,
            cuvee_normalized=self._normalize_text(cuvee) if cuvee else None,
            vintage=vintage,
            format_ml=format_ml,
            region=input_data.region,
            normalized_tokens=normalized_tokens
        )

    # ── Extractors ──

    def _extract_vintage(self, name: str) -> Optional[str]:
        match = self.vintage_regex.search(name)
        return match.group(1) if match else None

    def _extract_format(self, format_str: str) -> Optional[int]:
        match = self.format_regex.search(format_str)
        if not match:
            return None
        amount = float(match.group(1))
        unit = match.group(2).lower()
        if unit == 'l':
            return int(amount * 1000)
        if unit == 'cl':
            return int(amount * 10)
        return int(amount)

    def _extract_classification(self, name: str) -> Optional[str]:
        for regex in self.classification_regexes:
            match = regex.search(name)
            if match:
                return match.group(1)
        return None

    def _extract_quoted(self, name: str) -> (List[str], str):
        """Extract single-quoted or double-quoted segments from the name.
        Returns (list of segments, name with quotes replaced by __QUOTE__ marker).

        The marker preserves the positional information so downstream parsing
        (producer/appellation split) knows where quoted content was.
        """
        segments = []

        def _replace(m):
            segment = m.group(1) or m.group(2)
            if segment:
                segments.append(segment.strip())
            return ' __QUOTE__ '

        cleaned = self.quoted_regex.sub(_replace, name)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return segments, cleaned

    def _extract_producer(self, name: str) -> (Optional[str], str):
        """Extract producer from start of name using conservative structural rules.

        Conservative strategy:
        - With prefix (Domaine, Château, ...): take prefix + connectors + 1 name token
          ("Domaine Rossignol-Trapet", "Domaine du Tunnel", "Domaine de la Romanee-Conti")
        - Without prefix: take 1-2 tokens
          ("Eric Rodez", "Opus One", "Arnot-Roberts", "Krug", "Brokenwood")

        Returns (producer, remainder).
        """
        if not name:
            return None, ''

        parts = name.split()
        producer_parts: List[str] = []
        i = 0

        # Phase 1: consume prefix tokens (Domaine, Château, etc.)
        while i < len(parts) and parts[i].lower().rstrip(',;.') in PRODUCER_PREFIXES:
            producer_parts.append(parts[i].rstrip(',;'))
            i += 1

        had_prefix = bool(producer_parts)

        # Phase 2: consume connector tokens (du, de, la, von ...)
        while i < len(parts) and parts[i].lower().rstrip(',;.') in CONNECTORS:
            producer_parts.append(parts[i].rstrip(',;'))
            i += 1

        # Phase 3: consume the producer's proper-name tokens
        # With prefix: 1 token (can be hyphenated compound)
        # Without prefix: up to 2 tokens
        max_name_words = 1 if had_prefix else 2
        name_word_count = 0

        while i < len(parts) and name_word_count < max_name_words:
            token = parts[i]
            lower = token.lower().rstrip(',;.')
            cleaned = token.rstrip(',;')

            # Stop at quote marker (quoted content follows — that's cuvée/vineyard)
            if token == '__QUOTE__':
                break
            # Stop at non-producer markers
            if lower in NON_PRODUCER_MARKERS:
                break
            # Stop at grape varieties
            if lower.rstrip("'") in GRAPE_VARIETIES:
                break
            # Stop at lowercase tokens that aren't connectors
            if cleaned[0:1] and not cleaned[0].isupper() and lower not in CONNECTORS:
                break

            # Lookahead: if the NEXT token is a SUFFIX marker (like "Vineyard"
            # or "Ranch"), the current token is part of the vineyard name, not
            # the producer. (e.g. "Graveyard" before "Vineyard" in
            # "Brokenwood Graveyard Vineyard"). This does NOT apply to prefix
            # markers like "Cuvée" which start their own content.
            next_lower = parts[i + 1].lower().rstrip(',;.') if i + 1 < len(parts) else ''
            if name_word_count >= 1 and next_lower in SUFFIX_MARKERS:
                break

            producer_parts.append(cleaned)
            name_word_count += 1
            i += 1

            if name_word_count >= max_name_words:
                break

            # If next token is a connector, consume it and one more name token
            next_lower = parts[i].lower().rstrip(',;.') if i < len(parts) else ''
            if next_lower in CONNECTORS and i < len(parts):
                producer_parts.append(parts[i].rstrip(',;'))
                i += 1
                if i < len(parts):
                    t = parts[i]
                    lo = t.lower().rstrip(',;.')
                    cl = t.rstrip(',;')
                    if (t != '__QUOTE__'
                        and lo not in NON_PRODUCER_MARKERS
                        and lo.rstrip("'") not in GRAPE_VARIETIES
                        and cl[0:1].isupper()):
                        producer_parts.append(cl)
                        i += 1
                break

        producer = ' '.join(producer_parts) if producer_parts else None
        remainder = ' '.join(parts[i:]).strip()
        return producer, remainder

    def _extract_appellation(self, remainder: str) -> Optional[str]:
        """Extract appellation from what remains after producer removal.

        Strategy: take consecutive capitalized tokens at the start, stopping at
        grape varieties, non-producer markers, or lowercase tokens.
        """
        if not remainder:
            return None

        parts = remainder.split()
        appellation_parts: List[str] = []
        for token in parts:
            # Skip quote markers — appellation can continue after quoted content
            if token == '__QUOTE__':
                if appellation_parts:
                    # Already started collecting — the quote breaks continuity, so stop
                    break
                # Haven't started yet — skip the quote and keep looking
                continue
            cleaned = token.rstrip(',;')
            lower = cleaned.lower().rstrip("'")

            if lower in GRAPE_VARIETIES:
                break
            if lower in NON_PRODUCER_MARKERS:
                break
            if not cleaned or not cleaned[0].isupper():
                # Allow connectors (de, du, la) mid-appellation
                if lower in CONNECTORS and appellation_parts:
                    appellation_parts.append(cleaned)
                    continue
                break
            appellation_parts.append(cleaned)
            # Bound appellation length to avoid grabbing everything
            if len(appellation_parts) >= 4:
                break

        if not appellation_parts:
            return None
        return ' '.join(appellation_parts)

    def _extract_vineyard_from_tail(self, remainder: str, appellation: Optional[str]) -> Optional[str]:
        """Extract vineyard from the tail of the remainder when no quoted
        segments are present. Everything after the appellation that isn't a
        grape variety is the vineyard candidate."""
        if not remainder:
            return None

        working = remainder
        if appellation:
            working = re.sub(r'\b' + re.escape(appellation) + r'\b', '', working, flags=re.IGNORECASE).strip()
        # Remove any remaining quote markers
        working = working.replace('__QUOTE__', '').strip()

        parts = [p.rstrip(',;') for p in working.split() if p and p[0].isupper()]

        # Strip trailing grape varieties (unless part of a compound like "Vin Noir"
        # where the preceding word is non-grape AND non-indicator)
        while parts and parts[-1].lower().rstrip(",'") in GRAPE_VARIETIES:
            if (len(parts) >= 2
                and parts[-2].lower().rstrip(",'") not in GRAPE_VARIETIES
                and parts[-2].lower().rstrip(",'") not in NON_PRODUCER_MARKERS):
                break
            parts.pop()
        # Strip leading grape varieties
        while parts and parts[0].lower().rstrip(",'") in GRAPE_VARIETIES:
            parts.pop(0)

        if not parts:
            return None
        return ' '.join(parts[:5])

    # ── Normalization ──

    def _normalize_text(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        normalized = text.lower()
        normalized = normalized.replace('-', ' ')
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        for key, synonyms in SYNONYM_MAPPINGS.items():
            for syn in synonyms:
                if normalized == syn or f' {syn} ' in f' {normalized} ':
                    normalized = key
                    break
        return normalized

    def _create_tokens(self, *fields) -> List[str]:
        tokens = set()
        for field in fields:
            if field:
                normalized = self._normalize_text(str(field))
                if normalized:
                    tokens.update(normalized.split())
        return sorted(list(tokens))


class QueryBuilder:
    def build_queries(self, parsed_sku: ParsedSKU) -> List[SearchQuery]:
        queries = []

        exact_base = self._build_exact_base(parsed_sku)
        queries.append(SearchQuery(query=f'{exact_base} bottle', query_type='exact', priority=1))
        queries.append(SearchQuery(query=f'{exact_base} wine', query_type='exact', priority=2))
        queries.append(SearchQuery(query=f'{exact_base} label', query_type='exact', priority=3))

        relaxed_base = self._build_relaxed_base(parsed_sku)
        queries.append(SearchQuery(query=f'{relaxed_base} bottle', query_type='relaxed', priority=4))
        queries.append(SearchQuery(query=f'{relaxed_base}', query_type='relaxed', priority=5))

        if parsed_sku.vintage:
            without_vintage = relaxed_base.replace(parsed_sku.vintage, '').strip()
            queries.append(SearchQuery(query=f'{without_vintage} bottle', query_type='vintage_fallback', priority=6))

        return queries[:6]

    def _build_exact_base(self, parsed_sku: ParsedSKU) -> str:
        parts = []
        if parsed_sku.producer:
            parts.append(parsed_sku.producer)
        if parsed_sku.vineyard:
            parts.append(parsed_sku.vineyard)
        if parsed_sku.appellation:
            parts.append(parsed_sku.appellation)
        if parsed_sku.classification:
            parts.append(parsed_sku.classification)
        if parsed_sku.vintage:
            parts.append(parsed_sku.vintage)
        return ' '.join(parts)

    def _build_relaxed_base(self, parsed_sku: ParsedSKU) -> str:
        parts = []
        if parsed_sku.producer:
            simple = parsed_sku.producer
            # Strip all known producer prefixes for relaxed search
            for prefix in PRODUCER_PREFIXES:
                simple = re.sub(r'^' + re.escape(prefix) + r'\s+', '', simple, flags=re.IGNORECASE)
            parts.append(simple)
        if parsed_sku.vineyard:
            parts.append(parsed_sku.vineyard)
        if parsed_sku.appellation:
            parts.append(parsed_sku.appellation)
        if parsed_sku.vintage:
            parts.append(parsed_sku.vintage)
        return ' '.join(parts)
