from pydantic import BaseModel
 
class MetricasPorMateria(BaseModel):
    """Schema for subject-level metrics."""
    materia: str
    aciertos: int
    errores: int 