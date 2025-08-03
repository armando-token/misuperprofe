DECO_PATTERNS = {
    'Area_A': {
        'Biología': {
            'recommended_context': 'caso clínico',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'formal y técnico',
                'structure': 'Caso clínico/laboratorio seguido de pregunta directa.',
                'options_count': 5
            }
        },
        'Química': {
            'recommended_context': 'experimento',
            'recommended_cognitive_level': 'aplicación',
            'style_guidelines': {
                'tone': 'formal y técnico',
                'structure': 'Descripción de un experimento o fenómeno químico, seguido de un cálculo o inferencia.',
                'options_count': 5
            }
        },
        # Default para otras materias en Area A
        'default': {
            'recommended_context': 'caso persona (cotidiano)',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'formal',
                'structure': 'Presentación de un caso o situación, seguido de una pregunta de análisis.',
                'options_count': 5
            }
        }
    },
    'Area_B': {
        'Física': {
            'recommended_context': 'experimento',
            'recommended_cognitive_level': 'aplicación',
            'style_guidelines': {
                'tone': 'formal y técnico',
                'structure': 'Problema con datos numéricos y descripción de un fenómeno físico.',
                'options_count': 5
            }
        },
        'Química': {
            'recommended_context': 'experimento',
            'recommended_cognitive_level': 'aplicación',
            'style_guidelines': {
                'tone': 'formal y técnico',
                'structure': 'Descripción de un experimento de laboratorio, seguido de una pregunta sobre los resultados.',
                'options_count': 5
            }
        },
        'default': {
            'recommended_context': 'caso experimental/gráfico',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'formal y científico',
                'structure': 'Presentación de datos o un gráfico, seguido de una pregunta de interpretación.',
                'options_count': 5
            }
        }
    },
    'Area_C': {
        'Matemática': {
            'recommended_context': 'problema con personaje/nombre',
            'recommended_cognitive_level': 'aplicación',
            'style_guidelines': {
                'tone': 'formal y preciso',
                'structure': 'Problema aplicado con datos (ej. figuras, unidades) en un contexto cotidiano o de ingeniería.',
                'options_count': 5
            }
        },
        'Física': {
            'recommended_context': 'escenario con gráfico',
            'recommended_cognitive_level': 'aplicación',
            'style_guidelines': {
                'tone': 'formal y técnico',
                'structure': 'Descripción de una situación de ingeniería o un sistema físico, a menudo con un diagrama, seguido de un cálculo.',
                'options_count': 5
            }
        },
        'default': {
            'recommended_context': 'problema con datos',
            'recommended_cognitive_level': 'aplicación',
            'style_guidelines': {
                'tone': 'formal y técnico',
                'structure': 'Presentación de un problema con datos numéricos explícitos, seguido de un cálculo.',
                'options_count': 5
            }
        }
    },
    'Area_D': {
        'Economía': {
            'recommended_context': 'situación empresarial/financiera',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'formal y analítico',
                'structure': 'Descripción de un escenario económico, financiero o social, a menudo con datos o una gráfica, seguido de una pregunta sobre sus implicaciones.',
                'options_count': 5
            }
        },
        'default': {
            'recommended_context': 'texto + pregunta de análisis',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'formal',
                'structure': 'Presentación de un caso de estudio o un texto breve, seguido de una pregunta de inferencia o análisis.',
                'options_count': 5
            }
        }
    },
    'Area_E': {
        'Filosofía': {
            'recommended_context': 'dilema ético',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'académico reflexivo',
                'structure': 'Dilema o situación social, seguido de una pregunta de reflexión que requiere aplicar un concepto filosófico.',
                'options_count': 5
            }
        },
        'Historia': {
            'recommended_context': 'situación histórica',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'formal y descriptivo',
                'structure': 'Presentación de un evento o proceso histórico, seguido de una pregunta sobre causas, consecuencias o interpretaciones.',
                'options_count': 5
            }
        },
        'default': {
            'recommended_context': 'texto para analizar',
            'recommended_cognitive_level': 'análisis',
            'style_guidelines': {
                'tone': 'académico',
                'structure': 'Presentación de un texto o caso de estudio, seguido de una pregunta que requiere análisis crítico o inferencia.',
                'options_count': 5
            }
        }
    }
} 