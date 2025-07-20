from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.services.teacher_analytics import TeacherAnalyticsService
from app.models.teacher import TeacherRole
from app.db.session import get_session as get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Función auxiliar para verificar autenticación (ajustar según tu sistema actual)
def verify_teacher_access(db: Session, user_id: str) -> bool:
    return TeacherAnalyticsService.is_teacher_or_admin(db, user_id)

@router.get("/teacher_dashboard")
async def teacher_dashboard_endpoint(
    teacher_id: str,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Token requerido")
    if not verify_teacher_access(db, teacher_id):
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere rol de profesor")
    assigned_students = TeacherAnalyticsService.get_assigned_students(db, teacher_id)
    teacher_role = db.query(TeacherRole).filter(TeacherRole.user_id == teacher_id).first()
    if teacher_role and teacher_role.role_type == 'admin':
        assigned_students = TeacherAnalyticsService.get_all_active_students(db)
    if not assigned_students:
        return {
            "teacher_id": teacher_id,
            "status": "sin_estudiantes",
            "message": "No hay estudiantes asignados",
            "data": {}
        }
    course_analytics = TeacherAnalyticsService.calculate_course_analytics(db, assigned_students)
    critical_areas = TeacherAnalyticsService.identify_critical_areas(db, assigned_students)
    return {
        "teacher_id": teacher_id,
        "status": "success",
        "summary": {
            "total_students": len(assigned_students),
            "active_courses": len(course_analytics),
            "critical_areas_count": len(critical_areas)
        },
        "course_performance": course_analytics,
        "critical_areas": critical_areas[:8],
        "student_list": assigned_students
    }

@router.get("/student_detailed_report")
async def student_detailed_report_endpoint(
    teacher_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Token requerido")
    if not verify_teacher_access(db, teacher_id):
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere rol de profesor")
    assigned_students = TeacherAnalyticsService.get_assigned_students(db, teacher_id)
    teacher_role = db.query(TeacherRole).filter(TeacherRole.user_id == teacher_id).first()
    if teacher_role and teacher_role.role_type == 'admin':
        assigned_students = TeacherAnalyticsService.get_all_active_students(db)
    if student_id not in assigned_students:
        raise HTTPException(status_code=403, detail="Estudiante no asignado a este profesor")
    detailed_report = TeacherAnalyticsService.generate_student_report(db, student_id)
    return {
        "teacher_id": teacher_id,
        "report": detailed_report,
        "generated_at": str(detailed_report.get('generated_at', ''))
    } 