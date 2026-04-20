import re
from typing import List, Optional, Dict, Any
from rapidfuzz import fuzz

from app.models.sku import WineSKUInput, ParsedSKU, SearchQuery
from app.core.constants import BURGUNDY_GRAND_CRUS, SYNONYM_MAPPINGS


class WineParser:
    CLASSIFICATION_PATTERNS = [
        r'\b(Grand Cru Class\u00e9)\b',
        r'\b(Grand Cru)\b',
        r'\b(Premier Cru|1er Cru|1er-Cru)\b',
        r'\b(1er|Premier)\s*Cru\b',
        r'\b(Villages?)\b',
        r'\b(Vendanges Tardives|VT)\b',
        r'\b(S\u00e9lection de Grains Nobles|SGN)\b',
    ]
    
    VINTAGE_PATTERN = r'\b(19\d{2}|20\d{2})\b'
    FORMAT_PATTERN = r'(\d+)\s*(ml|mL|ML|cl|cL|CL|L|l)\b'
    
    COMMON_PRODUCER_PREFIXES = [
        'domaine', 'chateau', 'ch\u00e2teau', 'mas', 'clos', 'cellier',
        'cave', 'maison', 'weingut', 'bodega', 'tenuta', 'cantina',
        'quinta', 'ernst', 'weinbach', 'arnot', 'roberts', 'poderi'
    ]

    GRAPE_VARIETIES = {
        'riesling', 'chardonnay', 'pinot', 'noir', 'noirs', 'blanc', 'blancs', 'gris', 'grigio',
        'cabernet', 'sauvignon', 'franc', 'merlot', 'syrah', 'shiraz',
        'grenache', 'tempranillo', 'nebbiolo', 'sangiovese', 'barbera',
        'malbec', 'zinfandel', 'viognier', 'roussanne', 'marsanne',
        'semillon', 'gewurztraminer', 'pinotage', 'carmenere', 'cinsault',
        'mourvedre', 'monastrell', 'corvina', 'rondinella', 'garganega',
        'albarino', 'albari\u00f1o', 'verdejo', 'godello', 'treixadura',
        'furmint', 'h\u00e1rslevel\u00fa', 'blaufr\u00e4nkisch', 'zweigelt',
        'st-laurent', 'sylvaner', 'traminer', 'm\u00fcller-thurgau',
        'silvaner', 'scheurebe', 'sp\u00e4tburgunder', 'grauburgunder',
        'weisburgunder', 'cornalin', 'humagne', 'petite', 'arvine',
        'amigne', 'heida', 'paien', 'chasselas', 'auxerrois',
        'trousseau',
    }
    
    BURGUNDY_APPELLATIONS = [
        'chablis', 'gevrey-chambertin', 'morey-st-denis', 'morey-saint-denis',
        'chambolle-musigny', 'vosne-roman\u00e9e', 'nuits-st-georges',
        'nuits-saint-georges', 'aloxe-corton', 'beaune', 'pommard',
        'volnay', 'meursault', 'puligny-montrachet', 'chassagne-montrachet',
        'santenay', 'maranges', 'rully', 'mercurey', 'givry', 'montagny',
        'bouzeron', 'ratafia', 'bourgogne', 'saint-\u00e9milion', 'st-\u00e9milion',
        'c\u00f4te de nuits', 'c\u00f4te de beaune', 'c\u00f4te chalonnaise',
        'm\u00e2connais', 'hautes-c\u00f4tes de nuits', 'hautes-c\u00f4tes de beaune',
        'cornas', 'barolo',
    ]
    
    def __init__(self):
        self.classification_regexes = [re.compile(p, re.IGNORECASE) for p in self.CLASSIFICATION_PATTERNS]
        self.vintage_regex = re.compile(self.VINTAGE_PATTERN)
        self.format_regex = re.compile(self.FORMAT_PATTERN, re.IGNORECASE)
    
    def parse(self, input_data: WineSKUInput) -> ParsedSKU:
        raw_name = input_data.wine_name

        classification = self._extract_classification(raw_name)
        vintage = input_data.vintage or self._extract_vintage(raw_name)
        format_ml = self._extract_format(input_data.format) if input_data.format else None

        name_without_classification = self._remove_classification(raw_name, classification)
        # Strip surrounding single quotes from cuvée names (e.g. 'Monts Luisants')
        name_without_classification = re.sub(r"'([^']+)'", r'\1', name_without_classification)
        producer = self._extract_producer(name_without_classification)
        appellation = self._extract_appellation(name_without_classification)
        vineyard = self._extract_vineyard(name_without_classification, producer, appellation)
        
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
            vintage=vintage,
            format_ml=format_ml,
            region=input_data.region,
            normalized_tokens=normalized_tokens
        )
    
    def _extract_classification(self, name: str) -> Optional[str]:
        for regex in self.classification_regexes:
            match = regex.search(name)
            if match:
                return match.group(1)
        return None
    
    def _extract_vintage(self, name: str) -> Optional[str]:
        match = self.vintage_regex.search(name)
        if match:
            return match.group(1)
        return None
    
    def _extract_format(self, format_str: str) -> Optional[int]:
        match = self.format_regex.search(format_str)
        if match:
            amount = int(match.group(1))
            unit = match.group(2).lower()
            if unit in ['l', 'L']:
                return amount * 1000
            elif unit in ['cl', 'cL', 'CL']:
                return amount * 10
            else:
                return amount
        return None
    
    def _remove_classification(self, name: str, classification: Optional[str]) -> str:
        if not classification:
            return name
        return re.sub(r'\b' + re.escape(classification) + r'\b', '', name, flags=re.IGNORECASE).strip()
    
    def _extract_producer(self, name: str) -> Optional[str]:
        parts = name.split()
        if not parts:
            return None

        prefix_set = set(p.lower() for p in self.COMMON_PRODUCER_PREFIXES)

        # Build a set of all known appellation/Grand Cru words for fast lookup
        appellation_words = set()
        for a in self.BURGUNDY_APPELLATIONS:
            appellation_words.update(a.lower().replace('-', ' ').split())
        for gc in BURGUNDY_GRAND_CRUS:
            appellation_words.update(gc.lower().replace('-', ' ').split())

        producer_parts = []
        in_prefix = True

        for i, part in enumerate(parts):
            lower_part = part.lower().rstrip(',;')
            cleaned = part.rstrip(',;')
            # For hyphenated words like "Latricieres-Chambertin", check both halves
            lower_halves = lower_part.split('-')

            # Stop at grape varieties
            if lower_part.rstrip("'") in self.GRAPE_VARIETIES:
                break

            # Stop at vineyard/estate indicators (they signal a cru name, not producer)
            if lower_part in ('vineyard', 'estate', 'ranch', 'winery'):
                break

            # Stop if any half of a hyphenated word is a known appellation word
            # AND the full hyphenated word isn't a known producer compound (like "Rossignol-Trapet")
            if any(h in appellation_words for h in lower_halves) and lower_part not in prefix_set:
                # Only stop if we already have at least a prefix + name
                if producer_parts:
                    break

            if in_prefix and lower_part in prefix_set:
                producer_parts.append(cleaned)
            elif in_prefix and i == 0:
                # No prefix on first word — treat first 2 title-case words as producer
                producer_parts.append(cleaned)
                in_prefix = False
            elif in_prefix:
                # First non-prefix word after prefix(es) — include it then stop prefix mode
                producer_parts.append(cleaned)
                in_prefix = False
            else:
                # After the non-prefix word, include one more if it's also title-case
                # (e.g. "Rossignol-Trapet", "du Tunnel", "Arlaud")
                # BUT: if the NEXT word is a vineyard/estate indicator, stop —
                # the current word belongs to the vineyard name, not the producer.
                next_lower = parts[i + 1].lower().rstrip(',;') if i + 1 < len(parts) else ''
                if next_lower in ('vineyard', 'estate', 'ranch', 'winery'):
                    break
                if i <= len(producer_parts) + 1 and (cleaned[0].isupper() or lower_part in ('du', 'de', 'des', 'le', 'la', 'di', 'del', 'della', 'von', 'van')):
                    producer_parts.append(cleaned)
                    if lower_part not in ('du', 'de', 'des', 'le', 'la', 'di', 'del', 'della', 'von', 'van'):
                        break
                else:
                    break

        if producer_parts:
            return ' '.join(producer_parts)
        return parts[0] if parts else None
    
    def _extract_appellation(self, name: str) -> Optional[str]:
        name_lower = name.lower()

        # Check Burgundy appellations (longest first to avoid partial matches)
        for appellation in sorted(self.BURGUNDY_APPELLATIONS, key=len, reverse=True):
            if appellation.lower() in name_lower:
                return appellation

        # Check Grand Crus (longest first — e.g. "latricieres-chambertin" before "chambertin")
        for gc in sorted(BURGUNDY_GRAND_CRUS, key=len, reverse=True):
            if gc.lower() in name_lower:
                return gc.replace('-', ' ').title()

        # Non-Burgundy: extract upper-case words after producer
        parts = name.split()
        producer = self._extract_producer(name)
        producer_words = set(producer.lower().split()) if producer else set()

        skip_words = {'vineyard', 'estate', 'ranch', 'winery'}
        appellation_parts = []
        for i, part in enumerate(parts):
            cleaned = part.rstrip(',;')
            if cleaned.lower().rstrip("'") in self.GRAPE_VARIETIES:
                continue
            if cleaned.lower() in skip_words:
                continue
            # Skip words that are followed by vineyard/estate/ranch indicators
            # (they're part of the vineyard name, not appellation)
            next_lower = parts[i + 1].lower().rstrip(',;') if i + 1 < len(parts) else ''
            if next_lower in ('vineyard', 'estate', 'ranch', 'winery'):
                continue
            if cleaned.lower() not in producer_words and cleaned and cleaned[0].isupper():
                appellation_parts.append(cleaned)

        if appellation_parts:
            return ' '.join(appellation_parts[:3])

        return None
    
    def _extract_vineyard(self, name: str, producer: Optional[str], appellation: Optional[str]) -> Optional[str]:
        if not producer:
            return None

        name_clean = name
        for item in [producer, appellation]:
            if item:
                # Use word-boundary-aware replacement to avoid partial removal
                # (e.g. removing "Chambertin" should not leave "Latricieres-" dangling)
                name_clean = re.sub(r'\b' + re.escape(item) + r'\b', '', name_clean, flags=re.IGNORECASE)

        name_clean = re.sub(r'\b(Grand Cru|Premier Cru|1er Cru)\b', '', name_clean, flags=re.IGNORECASE)
        # Remove dangling hyphens left by partial removal
        name_clean = re.sub(r'\s*-\s*$', '', name_clean)
        name_clean = re.sub(r'^\s*-\s*', '', name_clean)
        name_clean = name_clean.strip(',; ')

        # Strip single-quoted segments (e.g. 'Monts Luisants' → Monts Luisants)
        name_clean = re.sub(r"'([^']+)'", r'\1', name_clean)

        # Filter out standalone grape variety names from vineyard parts
        # (but allow them in compound names like "Vin Noir")
        parts = [p for p in name_clean.split() if p and p[0].isupper()]
        # Remove trailing grape variety names (they're not part of vineyard)
        # BUT: keep them if preceded by a non-grape word that forms a compound name
        # (e.g. "Vin Noir" — "Vin" is not a grape, so "Noir" stays)
        while parts and parts[-1].lower().rstrip(",'") in self.GRAPE_VARIETIES:
            if len(parts) >= 2 and parts[-2].lower().rstrip(",'") not in self.GRAPE_VARIETIES:
                break  # Keep the compound name together
            parts.pop()
        # Also remove leading grape variety names
        while parts and parts[0].lower().rstrip(",'") in self.GRAPE_VARIETIES:
            parts.pop(0)

        if parts:
            vineyard = ' '.join(parts[:4])
            # Avoid duplicating the appellation as vineyard
            app_norm = (appellation or '').lower().replace('-', ' ')
            vyn_norm = vineyard.lower().replace('-', ' ')
            if vyn_norm == app_norm or vyn_norm.startswith(app_norm + ' '):
                # If vineyard is just appellation + grape variety words, skip it
                remainder = vyn_norm[len(app_norm):].strip()
                remainder_words = set(remainder.split())
                if remainder_words <= self.GRAPE_VARIETIES:
                    return None
            return vineyard

        return None
    
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
        queries.append(SearchQuery(
            query=f'{exact_base} bottle',
            query_type='exact',
            priority=1
        ))
        queries.append(SearchQuery(
            query=f'{exact_base} wine',
            query_type='exact',
            priority=2
        ))
        queries.append(SearchQuery(
            query=f'{exact_base} label',
            query_type='exact',
            priority=3
        ))
        
        relaxed_base = self._build_relaxed_base(parsed_sku)
        queries.append(SearchQuery(
            query=f'{relaxed_base} bottle',
            query_type='relaxed',
            priority=4
        ))
        queries.append(SearchQuery(
            query=f'{relaxed_base}',
            query_type='relaxed',
            priority=5
        ))
        
        if parsed_sku.vintage:
            without_vintage = relaxed_base.replace(parsed_sku.vintage, '').strip()
            queries.append(SearchQuery(
                query=f'{without_vintage} bottle',
                query_type='vintage_fallback',
                priority=6
            ))
        
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
            simple_producer = parsed_sku.producer.replace('Domaine ', '').replace('Chateau ', '').replace('Château ', '')
            parts.append(simple_producer)
        if parsed_sku.vineyard:
            parts.append(parsed_sku.vineyard)
        if parsed_sku.appellation:
            parts.append(parsed_sku.appellation)
        if parsed_sku.vintage:
            parts.append(parsed_sku.vintage)
        
        return ' '.join(parts)
