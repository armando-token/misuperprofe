-- Script seguro para agregar la tabla de profesores máster
CREATE TABLE IF NOT EXISTS master_teacher_flags (
    teacher_id VARCHAR(255) PRIMARY KEY, -- Coincide con el ID de profesor usado en student_assignments y teacher_roles
    is_master BOOLEAN DEFAULT TRUE NOT NULL,
    assigned_by_admin_id VARCHAR(255) NOT NULL, -- ID del admin que otorgó el rol
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_master_teacher_flags_teacher_id ON master_teacher_flags(teacher_id);
CREATE INDEX IF NOT EXISTS idx_master_teacher_flags_is_master ON master_teacher_flags(is_master);

COMMENT ON TABLE master_teacher_flags IS 'Marca explícitamente a los profesores máster para dashboards globales.'; 