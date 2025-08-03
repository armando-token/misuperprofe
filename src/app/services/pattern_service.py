from .deco_patterns import DECO_PATTERNS
from typing import Dict, Any

class PatternService:
    def __init__(self):
        self._patterns = None

    def load_patterns(self):
        """Carga los patrones en memoria."""
        print("Cargando patrones DECO en memoria...")
        self._patterns = DECO_PATTERNS
        print("Patrones cargados exitosamente.")

    def get_pattern(self, area: str, subject: str) -> Dict[str, Any]:
        """
        Obtiene el patrón para un área y materia específica.
        Si la materia no tiene un patrón específico, devuelve el default para esa área.
        """
        if not self._patterns:
            self.load_patterns()
        
        area_patterns = self._patterns.get(area, {})
        subject_pattern = area_patterns.get(subject, area_patterns.get('default', {}))
        print(f"Patrón encontrado para Area='{area}', Subject='{subject}': {subject_pattern}")
        return subject_pattern

# Instancia única (Singleton) del servicio
pattern_service = PatternService()

def get_pattern_service() -> PatternService:
    return pattern_service 