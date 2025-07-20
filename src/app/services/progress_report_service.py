"""
Servicio para reportes automáticos de avance de alumnos a profesores.
Inspirado en el sistema de reportes de Duolingo.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.profesor import Profesor
from app.models.clase import GrupoClase, GrupoClaseAlumnoAssociation
from app.models.adaptive import ProgressUnit, UserProgress
from app.models.external_user_map import ExternalUserMap
from app.models.capitulo import Capitulo

# TODO: Importar modelos y utilidades de correo cuando estén disponibles

class ProgressReportService:
    """
    Servicio para analizar el progreso de los alumnos y enviar reportes periódicos a los profesores responsables.
    """

    async def analizar_progreso_alumnos(self, db: AsyncSession) -> list[dict]:
        """
        Analiza el progreso de todos los alumnos y retorna una lista de resúmenes por profesor.
        Cada resumen contiene el email del profesor y una lista de alumnos con su avance.
        """
        reportes = []
        profesores_result = await db.execute(select(Profesor))
        profesores = profesores_result.scalars().all()
        for profesor in profesores:
            resumen_profesor = {
                "email_profesor": profesor.email,
                "nombre_profesor": f"{profesor.nombre} {profesor.apellido}",
                "clases": []
            }
            for clase in profesor.grupos_clase:
                resumen_clase = {
                    "nombre_clase": clase.nombre_clase,
                    "alumnos": []
                }
                for alumno_assoc in clase.alumnos_association:
                    user_id_hash = alumno_assoc.user_id_hash
                    # Buscar datos personales del alumno
                    alumno_map = await db.execute(
                        select(ExternalUserMap).filter(ExternalUserMap.internal_user_id_hash == user_id_hash)
                    )
                    alumno_map = alumno_map.scalars().first()
                    nombre_alumno = alumno_map.external_user_identifier if alumno_map else user_id_hash
                    # Buscar progreso global
                    progreso = await db.execute(
                        select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash)
                    )
                    progreso = progreso.scalars().first()
                    # Buscar progreso por capítulos
                    progress_units_result = await db.execute(
                        select(ProgressUnit).filter(ProgressUnit.user_id_hash == user_id_hash)
                    )
                    progress_units = progress_units_result.scalars().all()
                    total_capitulos = len(progress_units)
                    completados = sum(1 for pu in progress_units if pu.state.name == "COMPLETADO")
                    estrellas = sum(pu.stars for pu in progress_units)
                    porcentaje = int((completados / total_capitulos) * 100) if total_capitulos > 0 else 0
                    resumen_alumno = {
                        "nombre_alumno": nombre_alumno,
                        "user_id_hash": user_id_hash,
                        "porcentaje": porcentaje,
                        "capitulos_completados": completados,
                        "capitulos_totales": total_capitulos,
                        "estrellas": estrellas,
                        "racha": progreso.current_streak if progreso else 0,
                        "xp": progreso.total_xp if progreso else 0
                    }
                    resumen_clase["alumnos"].append(resumen_alumno)
                resumen_profesor["clases"].append(resumen_clase)
            reportes.append(resumen_profesor)
        return reportes

    def generar_resumen(self, progreso_profesor: dict) -> str:
        """
        Genera un resumen textual del avance de los alumnos de un profesor, agrupado por clase.
        """
        resumen = []
        resumen.append(f"Reporte de avance para: {progreso_profesor.get('nombre_profesor', '')} <{progreso_profesor.get('email_profesor', '')}>\n")
        for clase in progreso_profesor.get("clases", []):
            resumen.append(f"Clase: {clase['nombre_clase']}")
            resumen.append("Alumno                          %   Cap. Comp/Total  Estrellas  Racha  XP")
            resumen.append("--------------------------------------------------------------------------------")
            for alumno in clase.get("alumnos", []):
                nombre = alumno["nombre_alumno"][:28].ljust(30)
                porcentaje = str(alumno["porcentaje"]).rjust(3)
                cap = f"{alumno['capitulos_completados']}/{alumno['capitulos_totales']}".rjust(10)
                estrellas = str(alumno["estrellas"]).rjust(8)
                racha = str(alumno["racha"]).rjust(6)
                xp = str(alumno["xp"]).rjust(5)
                resumen.append(f"{nombre} {porcentaje}%   {cap}     {estrellas}   {racha}  {xp}")
            resumen.append("")
        return "\n".join(resumen)

    def enviar_reporte_profesor(self, email_profesor: str, resumen: str) -> None:
        """
        Envía el resumen de avance al correo del profesor responsable.
        Por ahora solo imprime el resumen por consola. La integración real de correo se hará más adelante.
        """
        print(f"\n--- Reporte para {email_profesor} ---\n{resumen}\n--- Fin del reporte ---\n")

    async def ejecutar_reporte_automatico(self, db: AsyncSession):
        """
        Ejecuta el flujo completo: analiza, genera y envía reportes a los profesores.
        Pensado para ser llamado por un cron job o background task.
        """
        reportes = await self.analizar_progreso_alumnos(db)
        for progreso_profesor in reportes:
            resumen = self.generar_resumen(progreso_profesor)
            email_profesor = progreso_profesor.get("email_profesor", "")
            self.enviar_reporte_profesor(email_profesor, resumen) 