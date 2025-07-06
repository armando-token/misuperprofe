from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, cast
from app.models.teacher import TeacherRole, StudentAssignment
from typing import List, Dict, Any
from datetime import datetime

class TeacherAnalyticsService:
    @staticmethod
    def is_teacher_or_admin(db: Session, user_id: str) -> bool:
        role = db.query(TeacherRole).filter(
            TeacherRole.user_id == user_id,
            TeacherRole.role_type.in_(['teacher', 'admin']),
            TeacherRole.is_active == True
        ).first()
        return role is not None

    @staticmethod
    def get_assigned_students(db: Session, teacher_id: str) -> List[str]:
        assignments = db.query(StudentAssignment.student_user_id).filter(
            StudentAssignment.teacher_user_id == teacher_id,
            StudentAssignment.is_active == True
        ).all()
        return [a.student_user_id for a in assignments]

    @staticmethod
    def get_all_active_students(db: Session) -> List[str]:
        result = db.execute('SELECT DISTINCT user_id_hash FROM attempts')
        return [row[0] for row in result]

    @staticmethod
    def calculate_course_analytics(db: Session, student_list: List[str]) -> Dict[str, Any]:
        if not student_list:
            return {}
        placeholders = ','.join(['%s'] * len(student_list))
        query = f'''
            SELECT course,
                   COUNT(*) AS total_questions,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct_count,
                   COUNT(DISTINCT user_id_hash) AS student_count
            FROM attempts
            WHERE user_id_hash IN ({placeholders})
            GROUP BY course
        '''
        result = db.execute(query, tuple(student_list))
        analytics = {}
        for row in result:
            course, total_questions, correct_count, student_count = row
            success_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
            analytics[course] = {
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'success_rate': round(success_percentage, 2),
                'participating_students': student_count,
                'performance_level': 'Excelente' if success_percentage >= 85 else \
                                   'Bueno' if success_percentage >= 70 else \
                                   'Regular' if success_percentage >= 60 else 'Necesita Refuerzo'
            }
        return analytics

    @staticmethod
    def generate_student_report(db: Session, student_id: str) -> Dict[str, Any]:
        query = '''
            SELECT course, topic, COUNT(*) AS attempts, SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct
            FROM attempts
            WHERE user_id_hash = %s
            GROUP BY course, topic
        '''
        result = db.execute(query, (student_id,))
        report = {
            'student_id': student_id,
            'course_breakdown': {},
            'overall_performance': {
                'total_attempts': 0,
                'total_correct': 0,
                'overall_success_rate': 0
            },
            'recommendations': []
        }
        total_attempts = 0
        total_correct = 0
        for row in result:
            course, topic, attempts, correct = row
            if course not in report['course_breakdown']:
                report['course_breakdown'][course] = {
                    'topics': {},
                    'course_totals': {
                        'attempts': 0,
                        'correct': 0,
                        'success_rate': 0
                    }
                }
            topic_success_rate = (correct / attempts * 100) if attempts > 0 else 0
            report['course_breakdown'][course]['topics'][topic] = {
                'attempts': attempts,
                'correct': correct,
                'success_rate': round(topic_success_rate, 2),
                'status': 'Fortaleza' if topic_success_rate >= 80 else
                         'Satisfactorio' if topic_success_rate >= 60 else
                         'Necesita Práctica'
            }
            report['course_breakdown'][course]['course_totals']['attempts'] += attempts
            report['course_breakdown'][course]['course_totals']['correct'] += correct
            total_attempts += attempts
            total_correct += correct
        for course_data in report['course_breakdown'].values():
            course_attempts = course_data['course_totals']['attempts']
            course_correct = course_data['course_totals']['correct']
            if course_attempts > 0:
                course_data['course_totals']['success_rate'] = round(
                    (course_correct / course_attempts) * 100, 2
                )
        report['overall_performance']['total_attempts'] = total_attempts
        report['overall_performance']['total_correct'] = total_correct
        if total_attempts > 0:
            report['overall_performance']['overall_success_rate'] = round(
                (total_correct / total_attempts) * 100, 2
            )
        report['recommendations'] = TeacherAnalyticsService._generate_recommendations(report)
        return report

    @staticmethod
    def _generate_recommendations(report: Dict[str, Any]) -> List[str]:
        recommendations = []
        overall_rate = report['overall_performance']['overall_success_rate']
        if overall_rate < 60:
            recommendations.append("Requiere atención inmediata y refuerzo en conceptos básicos")
        elif overall_rate < 75:
            recommendations.append("Necesita práctica adicional y seguimiento cercano")
        for course, data in report['course_breakdown'].items():
            course_rate = data['course_totals']['success_rate']
            if course_rate < 50:
                recommendations.append(f"Curso {course}: Requiere refuerzo intensivo")
            elif course_rate < 70:
                recommendations.append(f"Curso {course}: Necesita práctica adicional")
            weak_topics = [
                topic for topic, stats in data['topics'].items() 
                if stats['success_rate'] < 60
            ]
            if weak_topics:
                recommendations.append(
                    f"Curso {course}: Enfocar en temas {', '.join(weak_topics[:3])}"
                )
        return recommendations[:5]

    @staticmethod
    def identify_critical_areas(db: Session, student_list: List[str], threshold: float = 50.0) -> List[Dict[str, Any]]:
        if not student_list:
            return []
        placeholders = ','.join(['%s'] * len(student_list))
        query = f'''
            SELECT course, topic, COUNT(*) AS attempts, SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct
            FROM attempts
            WHERE user_id_hash IN ({placeholders})
            GROUP BY course, topic
            HAVING COUNT(*) >= 10
        '''
        result = db.execute(query, tuple(student_list))
        critical_areas = []
        for row in result:
            course, topic, attempts, correct = row
            success_rate = (correct / attempts * 100) if attempts > 0 else 0
            if success_rate < threshold:
                critical_areas.append({
                    'course': course,
                    'topic': topic,
                    'success_rate': round(success_rate, 2),
                    'total_attempts': attempts,
                    'priority': 'Alta' if success_rate < 30 else 'Media',
                    'recommendation': 'Refuerzo inmediato' if success_rate < 30 else 'Práctica adicional'
                })
        return sorted(critical_areas, key=lambda x: x['success_rate']) 