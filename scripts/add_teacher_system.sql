-- Script seguro para agregar sistema de roles de profesor y asignaciones

-- Tabla de roles de usuario (profesor, admin, estudiante)
CREATE TABLE IF NOT EXISTS teacher_roles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    role_type VARCHAR(50) NOT NULL DEFAULT 'student',
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_teacher_roles_user_id ON teacher_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_teacher_roles_type ON teacher_roles(role_type);

-- Tabla de asignaciones estudiante-profesor
CREATE TABLE IF NOT EXISTS student_assignments (
    id SERIAL PRIMARY KEY,
    teacher_user_id VARCHAR(255) NOT NULL,
    student_user_id VARCHAR(255) NOT NULL,
    assigned_date TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT unique_teacher_student UNIQUE (teacher_user_id, student_user_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_teacher ON student_assignments(teacher_user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_student ON student_assignments(student_user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_active ON student_assignments(is_active);

-- Insertar datos de ejemplo para pruebas
INSERT INTO teacher_roles (user_id, role_type) VALUES 
('teacher_demo', 'teacher'),
('admin_demo', 'admin')
ON CONFLICT (user_id) DO UPDATE SET 
    role_type = EXCLUDED.role_type,
    is_active = TRUE;

-- Comentarios para documentación
COMMENT ON TABLE teacher_roles IS 'Roles de usuarios en el sistema educativo';
COMMENT ON TABLE student_assignments IS 'Asignaciones de estudiantes a profesores específicos'; 