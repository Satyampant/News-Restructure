# Fuzzy matching, validation
import re
from typing import List, Optional, Set
from src.domain.models.entities import (
    EntityExtractionSchema, 
    CompanyEntity, 
    RegulatorEntity, 
    EventEntity
)

# Optional dependency for fuzzy matching
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

class EntityNormalizer:
    """
    Domain service for entity normalization, validation, and deduplication.
    Handles business logic for cleaning up extracted entities.
    """
    
    def __init__(
        self,
        reference_companies: Optional[List[str]] = None,
        reference_sectors: Optional[List[str]] = None,
        reference_regulators: Optional[List[str]] = None
    ):
        self.reference_companies = reference_companies or self._load_default_companies()
        self.reference_sectors = reference_sectors or self._load_default_sectors()
        self.reference_regulators = reference_regulators or self._load_default_regulators()
        
    def normalize(self, raw_schema: EntityExtractionSchema) -> EntityExtractionSchema:
        """
        Main entry point to normalize and deduplicate entities in the schema.
        """
        # Normalize Companies
        validated_companies = []
        seen_companies = set()
        
        for company in raw_schema.companies:
            normalized_name = self._normalize_company_name(company.name)
            
            if normalized_name.lower() in seen_companies:
                continue
            seen_companies.add(normalized_name.lower())
            
            # Validate Ticker
            if company.ticker_symbol:
                if self._validate_ticker_symbol(company.ticker_symbol):
                    company.ticker_symbol = company.ticker_symbol.upper()
                else:
                    company.ticker_symbol = None
            
            # Normalize Sector
            if company.sector:
                company.sector = self._normalize_sector(company.sector)
            
            company.name = normalized_name
            validated_companies.append(company)
        
        # Normalize Sectors
        validated_sectors = []
        seen_sectors = set()
        
        for sector in raw_schema.sectors:
            normalized_sector = self._normalize_sector(sector)
            if normalized_sector and normalized_sector.lower() not in seen_sectors:
                validated_sectors.append(normalized_sector)
                seen_sectors.add(normalized_sector.lower())
        
        # Normalize Regulators
        validated_regulators = []
        seen_regulators = set()
        
        for regulator in raw_schema.regulators:
            normalized_name = self._normalize_regulator_name(regulator.name)
            
            if normalized_name.lower() in seen_regulators:
                continue
            seen_regulators.add(normalized_name.lower())
            
            regulator.name = normalized_name
            validated_regulators.append(regulator)
        
        # Deduplicate People (simple list)
        validated_people = list(set(raw_schema.people))
        
        # Deduplicate Events (by event type)
        validated_events = []
        seen_events = set()
        
        for event in raw_schema.events:
            if event.event_type.lower() not in seen_events:
                validated_events.append(event)
                seen_events.add(event.event_type.lower())
        
        # Update Schema
        raw_schema.companies = validated_companies
        raw_schema.sectors = validated_sectors
        raw_schema.regulators = validated_regulators
        raw_schema.people = validated_people
        raw_schema.events = validated_events
        
        return raw_schema

    def _normalize_company_name(self, name: str) -> str:
        """Strip prefixes and perform fuzzy matching against reference list."""
        if not name:
            return name
        
        normalized = name.strip()
        for prefix in ["The ", "the ", "THE "]:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        # Fuzzy match against reference list if available
        if RAPIDFUZZ_AVAILABLE and self.reference_companies:
            match = process.extractOne(
                normalized,
                self.reference_companies,
                scorer=fuzz.ratio,
                score_cutoff=85
            )
            if match:
                return match[0]
        
        return normalized

    def _normalize_sector(self, sector: str) -> Optional[str]:
        """Normalize sector name against reference list."""
        if not sector:
            return None
        
        # Direct match check
        for ref_sector in self.reference_sectors:
            if sector.lower() == ref_sector.lower():
                return ref_sector
        
        # Fuzzy match
        if RAPIDFUZZ_AVAILABLE:
            match = process.extractOne(
                sector,
                self.reference_sectors,
                scorer=fuzz.ratio,
                score_cutoff=80
            )
            if match:
                return match[0]
        
        return sector

    def _normalize_regulator_name(self, regulator_name: str) -> str:
        """Normalize regulator name."""
        if not regulator_name:
            return regulator_name
        
        if regulator_name in self.reference_regulators:
            return regulator_name
        
        if RAPIDFUZZ_AVAILABLE:
            match = process.extractOne(
                regulator_name,
                self.reference_regulators,
                scorer=fuzz.ratio,
                score_cutoff=85
            )
            if match:
                return match[0]
        
        return regulator_name

    def _validate_ticker_symbol(self, ticker: str) -> bool:
        """Validate ticker symbol format using regex."""
        if not ticker or len(ticker) < 1:
            return False
        # Ensures uppercase alphanumeric, usually 1-12 chars
        pattern = r'^(?=.*[A-Z])[A-Z0-9]{1,12}$'
        return bool(re.match(pattern, ticker))

    # --- Default Data Loaders (Preserved from legacy) ---
    
    def _load_default_companies(self) -> List[str]:
        return [
            "HDFC Bank", "ICICI Bank", "State Bank of India", "Reliance Industries",
            "TCS", "Infosys", "Wipro", "Adani Green Energy", "Mahindra & Mahindra",
            "Bharti Airtel", "Sun Pharmaceutical", "Maruti Suzuki", "Power Grid",
            "UltraTech Cement", "Tata Motors", "Tech Mahindra", "HUL", "ITC",
            "Asian Paints", "Bajaj Finance", "Axis Bank", "Kotak Mahindra Bank",
            "NTPC", "Coal India", "Larsen & Toubro", "HCL Technologies"
        ]
    
    def _load_default_sectors(self) -> List[str]:
        return [
            "Banking", "Finance", "NBFC", "Insurance", "IT", "Energy", "Oil & Gas",
            "Auto", "Telecom", "Pharma", "Healthcare", "Cement", "Utilities",
            "Steel", "Semiconductors", "Rubber", "Logistics", "Mining", "Coal",
            "Construction", "Infrastructure", "Real Estate", "Agriculture", "FMCG",
            "Textiles", "Aviation", "Chemicals", "Retail", "Consumer Durables",
            "Media", "E-commerce", "Railways", "Defense"
        ]
    
    def _load_default_regulators(self) -> List[str]:
        return [
            "RBI", "SEBI", "IRDAI", "CCI", "TRAI", "DOT", "DGCA", "RERA", "FSSAI",
            "US FDA", "Federal Reserve", "Ministry of Finance", "Ministry of Commerce"
        ]