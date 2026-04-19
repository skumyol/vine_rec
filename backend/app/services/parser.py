import re
from typing import List, Optional, Dict, Any
from rapidfuzz import fuzz

from app.models.sku import WineSKUInput, ParsedSKU, SearchQuery
from app.core.constants import BURGUNDY_GRAND_CRUS, SYNONYM_MAPPINGS


class WineParser:
    CLASSIFICATION_PATTERNS = [
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
        'quinta', 'ernst', 'weinbach', 'arnot', 'roberts'
    ]
    
    BURGUNDY_APPELLATIONS = [
        'chablis', 'gevrey-chambertin', 'morey-st-denis', 'morey-saint-denis',
        'chambolle-musigny', 'vosne-roman\u00e9e', 'nuits-st-georges',
        'nuits-saint-georges', 'aloxe-corton', 'beaune', 'pommard',
        'volnay', 'meursault', 'puligny-montrachet', 'chassagne-montrachet',
        'santenay', 'maranges', 'rully', 'mercurey', 'givry', 'montagny',
        'bouzeron', 'ratafia', 'bourgogne', 'c\u00f4te de nuits',
        'c\u00f4te de beaune', 'c\u00f4te chalonnaise', 'm\u00e2connais',
        'hautes-c\u00f4tes de nuits', 'hautes-c\u00f4tes de beaune',
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
        
        producer_parts = []
        for i, part in enumerate(parts):
            lower_part = part.lower().rstrip(',;')
            if lower_part in [p.lower() for p in self.COMMON_PRODUCER_PREFIXES] or i == 0:
                producer_parts.append(part.rstrip(',;'))
                if lower_part not in [p.lower() for p in self.COMMON_PRODUCER_PREFIXES]:
                    break
            else:
                if i < 3:
                    producer_parts.append(part.rstrip(',;'))
                if i >= 1 and not part.islower():
                    break
        
        if producer_parts:
            return ' '.join(producer_parts)
        return parts[0] if parts else None
    
    def _extract_appellation(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        
        for appellation in self.BURGUNDY_APPELLATIONS:
            if appellation.lower() in name_lower:
                return appellation
        
        for gc in BURGUNDY_GRAND_CRUS:
            if gc.lower() in name_lower:
                return gc.replace('-', ' ').title()
        
        parts = name.split()
        producer = self._extract_producer(name)
        producer_words = set(producer.lower().split()) if producer else set()
        
        appellation_parts = []
        for part in parts:
            if part.lower().rstrip(',;') not in producer_words and part[0].isupper():
                appellation_parts.append(part.rstrip(',;'))
        
        if appellation_parts:
            return ' '.join(appellation_parts[:3])
        
        return None
    
    def _extract_vineyard(self, name: str, producer: Optional[str], appellation: Optional[str]) -> Optional[str]:
        if not producer or not appellation:
            return None
        
        name_clean = name
        for item in [producer, appellation]:
            if item:
                name_clean = name_clean.replace(item, '')
        
        name_clean = re.sub(r'\b(Grand Cru|Premier Cru|1er Cru)\b', '', name_clean, flags=re.IGNORECASE)
        name_clean = name_clean.strip(',; ')
        
        parts = [p for p in name_clean.split() if p and p[0].isupper()]
        if parts:
            return ' '.join(parts[:4])
        
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
