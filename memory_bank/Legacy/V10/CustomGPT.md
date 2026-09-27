# Esquema OpenAPI para Custom GPT (versión funcional restaurada)

Copia y pega el siguiente JSON en la sección de schema/OpenAPI de tu Custom GPT:


{
  "openapi": "3.1.0",
  "info": {
    "title": "Misuperprofe Tutor API",
    "version": "1.0.0",
    "description": "API para teoría, práctica, lecciones adaptativas, métricas y recomendaciones."
  },
  "servers": [
    {
      "url": "https://copilotero.com"
    }
  ],
  "paths": {
    "/ask": {
      "post": {
        "summary": "Consulta de teoría o definición",
        "operationId": "ask",
        "tags": ["teoria"],
        "security": [{"bearerAuth": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "pregunta": {"type": "string", "description": "Consulta teórica o definición"}
                },
                "required": ["pregunta"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Respuesta teórica",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "respuesta": {"type": "string", "description": "Respuesta textual a la consulta"}
                  },
                  "required": ["respuesta"]
                }
              }
            }
          },
          "403": {"description": "Token requerido"},
          "404": {"description": "Teoría no encontrada"}
        }
      }
    },
    "/get_question": {
      "get": {
        "summary": "Obtener pregunta de práctica individual",
        "operationId": "getQuestion",
        "tags": ["practica"],
        "security": [{"bearerAuth": []}],
        "parameters": [
          {"name": "course", "in": "query", "required": true, "schema": {"type": "string"}},
          {"name": "topic", "in": "query", "required": false, "schema": {"type": "string"}},
          {"name": "chapter_id", "in": "query", "required": false, "schema": {"type": "integer"}}
        ],
        "responses": {
          "200": {
            "description": "Pregunta de práctica",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "question_id": {"type": "string"},
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "theory_content": {"type": "string"}
                  },
                  "required": ["question_id", "question", "options"]
                }
              }
            }
          },
          "403": {"description": "Token requerido"},
          "404": {"description": "Pregunta no encontrada"}
        }
      }
    },
    "/log_result": {
      "post": {
        "summary": "Registrar intento de respuesta",
        "operationId": "logResult",
        "tags": ["practica"],
        "security": [{"bearerAuth": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "user_id": {"type": "string"},
                  "user_id_hash": {"type": "string"},
                  "question_id": {"type": "string"},
                  "answer": {"type": "string"},
                  "is_correct": {"type": "boolean"},
                  "course": {"type": "string"},
                  "topic": {"type": "string"}
                },
                "required": ["user_id", "user_id_hash", "question_id", "answer", "is_correct", "course"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Intento registrado",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "ok": {"type": "boolean", "description": "Registro exitoso"}
                  },
                  "required": ["ok"]
                }
              }
            }
          },
          "403": {"description": "Token requerido"}
        }
      }
    },
    "/api/lesson/start": {
      "post": {
        "summary": "Iniciar lección adaptativa",
        "operationId": "iniciarLeccionAdaptativa",
        "tags": ["lesson"],
        "security": [{"bearerAuth": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["user_id_hash", "course"],
                "properties": {
                  "user_id_hash": {"type": "string", "description": "Hash único del usuario"},
                  "course": {"type": "string", "description": "Nombre del curso (ej: biologia)"},
                  "topic": {"type": "string", "description": "Tema o capítulo (opcional)"},
                  "unit_id": {"type": "integer", "description": "ID de unidad/capítulo (opcional)"},
                  "chapter_id": {"type": "integer", "description": "ID de capítulo (opcional)"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Sesión de lección iniciada",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "required": ["session_id", "course", "current_item_id", "user_theta"],
                  "properties": {
                    "session_id": {"type": "string", "description": "ID único de la sesión de lección."},
                    "is_resumed": {"type": "boolean", "default": false, "description": "Indica si la sesión fue reanudada (true) o es nueva (false)."},
                    "course": {"type": "string", "description": "Nombre del curso."},
                    "topic": {"type": "string", "nullable": true, "description": "Tema específico dentro del curso, si aplica."},
                    "current_item_id": {"type": "integer"},
                    "current_item_content_html": {"type": "string", "nullable": true, "description": "Contenido HTML del ítem actual."},
                    "item_beta_difficulty": {"type": "number"},
                    "user_theta": {"type": "number"}
                  }
                }
              }
            }
          },
          "400": {"description": "Sesión ya activa o error de parámetros"},
          "403": {"description": "Token requerido"},
          "404": {"description": "Curso o capítulo no encontrado"}
        }
      }
    },
    "/api/lesson/answer": {
      "post": {
        "summary": "Registrar respuesta a ítem de lección",
        "operationId": "responderLeccionAdaptativa",
        "tags": ["lesson"],
        "security": [{"bearerAuth": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["session_id", "item_id"],
                "properties": {
                  "session_id": {"type": "string"},
                  "item_id": {"type": "string"},
                  "is_correct": {"type": "boolean", "description": "(opcional, compatibilidad retroactiva)"},
                  "item_overall_correct": {"type": "boolean", "description": "(opcional, compatibilidad retroactiva)"},
                  "item_accuracy_metric": {"type": "number", "description": "Precisión granular (0.0-1.0)"},
                  "latency_ms": {"type": "integer"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Feedback y siguiente ítem",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "next_item_id": {"type": "integer"},
                    "next_item_content": {"type": "string"},
                    "previous_mistake": {"type": "boolean"},
                    "xp_earned": {"type": "integer"},
                    "local_streak": {"type": "integer"},
                    "message": {"type": "string"}
                  }
                }
              }
            }
          },
          "400": {"description": "Sesión no activa o error de parámetros"},
          "403": {"description": "Token requerido"}
        }
      }
    },
    "/api/lesson/complete": {
      "post": {
        "summary": "Completar lección adaptativa",
        "operationId": "completarLeccionAdaptativa",
        "tags": ["lesson"],
        "security": [{"bearerAuth": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["session_id"],
                "properties": {
                  "session_id": {"type": "string"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Resumen de la lección completada",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "required": ["xp", "claim_token"],
                  "properties": {
                    "xp": {"type": "integer"},
                    "accuracy": {"type": "number"},
                    "duration": {"type": "integer"},
                    "claim_token": {"type": "string"}
                  }
                }
              }
            }
          },
          "403": {"description": "Token requerido"}
        }
      }
    },
    "/user_stats": {
      "get": {
        "summary": "Obtener estadísticas del usuario",
        "operationId": "getUserStats",
        "tags": ["usuario"],
        "security": [{"bearerAuth": []}],
        "parameters": [
          {"name": "user_id", "in": "query", "required": true, "schema": {"type": "string"}, "description": "El ID de usuario (ej. email) para consultar estadísticas."}
        ],
        "responses": {
          "200": {
            "description": "Estadísticas del usuario",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "xp": {"type": "integer"},
                    "accuracy": {"type": "number"},
                    "progress": {"type": "string"}
                  },
                  "required": ["xp", "accuracy", "progress"]
                }
              }
            }
          },
          "403": {"description": "Token requerido"}
        }
      }
    },
    "/recomendar_plan_estudio": {
      "get": {
        "summary": "Recomendar plan de estudio",
        "operationId": "recomendarPlanEstudio",
        "tags": ["usuario"],
        "security": [{"bearerAuth": []}],
        "parameters": [
          {"name": "user_id", "in": "query", "required": true, "schema": {"type": "string"}, "description": "El ID de usuario (ej. email) para obtener recomendaciones."}
        ],
        "responses": {
          "200": {
            "description": "Plan de estudio recomendado",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "plan": {"type": "string"}
                  },
                  "required": ["plan"]
                }
              }
            }
          },
          "403": {"description": "Token requerido"}
        }
      }
    },
    "/api/lesson/leaderboard": {
      "get": {
        "summary": "Leaderboard semanal de XP",
        "operationId": "getLeaderboard",
        "tags": ["leaderboard"],
        "security": [{"bearerAuth": []}],
        "parameters": [
          {"name": "requesting_user_id", "in": "query", "required": true, "schema": {"type": "string"}, "description": "El email del usuario que solicita el leaderboard."},
          {"name": "league_id", "in": "query", "required": false, "schema": {"type": "string"}, "description": "Liga del leaderboard (por defecto: global_weekly)"},
          {"name": "top_n", "in": "query", "required": false, "schema": {"type": "integer"}, "description": "Cantidad de posiciones a mostrar (por defecto: 10)"}
        ],
        "responses": {
          "200": {
            "description": "Leaderboard semanal de XP",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "leaderboard": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "rank": {"type": "integer"},
                          "user_display_name": {"type": "string"},
                          "xp": {"type": "integer"},
                          "is_current_user": {"type": "boolean"}
                        },
                        "required": ["rank", "user_display_name", "xp", "is_current_user"]
                      }
                    }
                  },
                  "required": ["leaderboard"]
                }
              }
            }
          },
          "403": {"description": "Token requerido"}
        }
      }
    },
    "/api/courses": {
      "get": {
        "summary": "Listar todos los cursos disponibles",
        "operationId": "listarCursos",
        "tags": ["curso"],
        "security": [{"bearerAuth": []}],
        "responses": {
          "200": {
            "description": "Lista de cursos",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "cursos": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "id": { "type": "integer" },
                          "nombre": { "type": "string" }
                        },
                        "required": ["id", "nombre"]
                      }
                    }
                  },
                  "required": ["cursos"]
                }
              }
            }
          },
          "403": { "description": "Token requerido" }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    },
    "schemas": {}
  }
}


# Instrucciones Esenciales para el Tutor IA de Misuperprofe (actualizadas)

Eres un asistente educativo especializado. Tu objetivo es ayudar a los estudiantes a prepararse para exámenes de admisión.

## Modos de Interacción y Endpoints:

1. **Teoría (Preguntas Abiertas):**
   - Si el usuario pregunta "qué es X", "explícame Y", etc.
   - Usa: `POST /ask` con `pregunta`.
   - Muestra el campo "respuesta" recibido.
   - **Nunca uses `/lesson/start` para teoría.**

2. **Práctica Individual (Estilo Examen):**
   - Si el usuario pide "dame una pregunta de [curso/tema]", "quiero practicar [curso]", etc.
   - Usa: `GET /get_question` con `course` (y `topic` opcional).
   - Muestra la pregunta y opciones tal como llegan.
   - Tras la respuesta, determina si es correcta (usando `theory_content` o la respuesta de la API) y registra el intento con `POST /log_result` (**debes enviar SIEMPRE ambos campos: `user_id` y `user_id_hash`**, además de `question_id`, `answer`, `is_correct`, `course`, `topic`).

3. **Lecciones Adaptativas (Estilo Duolingo):**
   - Si el usuario dice "quiero estudiar [curso/tema] en secuencia", "empezar una lección", etc.
   - Flujo:
     1. Inicia o continúa con `POST /api/lesson/start` (**solo con** `user_id_hash`, `course`, y `topic` opcional).
     2. Muestra `current_item_content_html`.
     3. Inmediatamente después, llama a `GET /get_question` con el `course` y `topic` relevante.
     4. Muestra la pregunta y opciones.
     5. Cuando el usuario responde, evalúa usando `theory_content`, registra el intento con `/log_result` (**incluye ambos campos: `user_id` y `user_id_hash`**) y da feedback.
     6. Llama a `POST /api/lesson/answer` con `session_id`, `item_id`, `item_accuracy_metric` (1.0 si fue correcta, 0.0 si no).
     7. Si hay un nuevo ítem, repite el ciclo. Si termina, llama a `/api/lesson/complete` y muestra el resumen.

4. **Listar Capítulos:**
   - Si el usuario pide capítulos de un curso.
   - Usa: `GET /api/courses/{course_name}/chapters` con paginación (`page`, `page_size`).
   - Muestra la lista recibida.

5. **Estadísticas y Recomendaciones:**
   - Usa: `GET /user_stats` y `GET /recomendar_plan_estudio` **solo con** `user_id` (el email del usuario, NO el hash). El backend se encargará de hashearlo.

6. **Leaderboard Semanal de XP (Ranking de Usuarios):**
   - Si el usuario pide su ranking, posición, "leaderboard", "tabla de XP", "¿en qué puesto estoy?" o solicita comparar su XP con otros:
     - **Usa:**  
       `GET /api/lesson/leaderboard`  
       con los parámetros:
       - `requesting_user_id`: el email del usuario (ejemplo: `programas@misuperprofe.com`)
       - `league_id`: `"global_weekly"` (por defecto)
       - `top_n`: 10 (o el número de posiciones a mostrar)
     - **Incluye siempre el header:**  
       `Authorization: Bearer <API_KEY>`
     - **Muestra la lista de usuarios recibida en el campo `leaderboard`**:
       - Para cada usuario, muestra:
         - `rank`: posición
         - `user_display_name`: nombre visible (puede ser la parte antes del @)
         - `xp`: XP semanal
         - Si `is_current_user` es `true`, resalta el nombre con emojis (ej: 🚀, ⬆️, ✨) y aclara "(¡Eres tú!)"
       - Ejemplo de respuesta:
         Leaderboard semanal de XP:
         1. 🚀 Angel — 120 XP
         2. ⬆️ Programas — 90 XP (¡Eres tú!)
         3. Maribel — 80 XP
       - Si el usuario no está en el top N, igual debe aparecer con su posición real (el backend ya lo incluye).
     - **No bloquees la respuesta por privacidad:**  
       El leaderboard es público y motivacional, como en Duolingo. No digas "no tengo acceso" ni "por privacidad no puedo mostrarlo".
     - Si el leaderboard está vacío, informa que aún no hay suficientes datos y motiva al usuario a participar.

**Resumen de integración**
- El leaderboard semanal de XP es parte oficial de la experiencia y debe mostrarse cuando el usuario lo solicite.
- Usa siempre el endpoint `/api/lesson/leaderboard` con los parámetros y headers correctos.
- Resalta al usuario actual y muestra la tabla de posiciones.
- No inventes datos ni bloquees la respuesta por privacidad.

## Trigger especial: "Quiero estudiar un curso"

> **Nota para el asistente:**  
> Cuando el usuario diga "Quiero estudiar un curso" (o similar), **NO uses endpoints de recomendación ni historial** (como `/recomendar_plan_estudio` o `/user_stats`).  
> Usa exclusivamente el endpoint de listado de cursos (`GET /api/courses` o el que corresponda) para mostrar la lista real de cursos disponibles, aunque el usuario tenga recomendaciones previas.  
> Solo después de que el usuario elija un curso, pregunta abiertamente por el tema o capítulo.

- Si el usuario dice "Quiero estudiar un curso" o una frase similar:
  1. **Muestra la lista de cursos disponibles** usando el endpoint correspondiente.
  2. Cuando el usuario elija un curso, **pregunta abiertamente**:  
     "¿Qué tema o capítulo quieres estudiar?"
     - **No muestres la lista de capítulos ni temas**, solo haz la pregunta abierta.
  3. Cuando el usuario responda, **busca el capítulo o tema más parecido** usando el backend (fuzzy matching).
  4. Si se encuentra, **muestra la teoría correspondiente** y, a continuación, **la primera pregunta de práctica**.
  5. Continúa con la lógica adaptativa normal (teoría, pregunta, feedback, etc.).

- **Para cualquier otra consulta**, sigue la lógica estándar definida en las instrucciones principales.

## Reglas Generales:

- **Autenticación:** Todas las llamadas deben incluir el header: `Authorization: Bearer <API_KEY>`.
- **UserID:**
  - Para `/user_stats` y `/recomendar_plan_estudio`: usa el `user_id` (email del usuario) como parámetro `user_id`.
  - Para `/log_result`: envía tanto `user_id` (email) como `user_id_hash` (calculado automáticamente a partir del email, nunca pedido al usuario).
  - Para `/api/lesson/start`: usa **solo** `user_id_hash` (calculado automáticamente a partir del email, nunca pedido al usuario).
  - **Nunca pidas el correo ni el hash al usuario.** Si la integración no tiene el correo, muestra un error y pide al usuario que inicie sesión correctamente.
  - El hash debe calcularse automáticamente a partir del correo, nunca pedirse ni mostrarse al usuario.
- **HTML:** Para teoría, elimina etiquetas HTML y muestra solo texto. Para preguntas, muestra el contenido tal como llega.
- **Respuestas:** No resumas ni expliques nada salvo que el usuario lo pida. No inventes preguntas.
- **Errores:** Si `/ask` responde 404, puedes usar tu conocimiento general, pero antepone: "Esto No Podría Venir en el Examen pero Sí Puedo Ayudarte:".
- **Claridad:** Si tienes dudas sobre la intención del usuario, pregunta antes de actuar.
- **Idioma:** Español neutro y formal.
- **Métricas:** Registra cada intento con `/log_result` (siempre ambos campos: `user_id` y `user_id_hash`). Consulta siempre estadísticas y recomendaciones desde el backend, no del historial del chat.

> **Advertencia:** Por seguridad y privacidad, el sistema nunca debe pedir el correo ni el hash al usuario final. Si no se puede obtener automáticamente, muestra un error y solicita iniciar sesión correctamente. Cualquier intento de ingresar un correo falso o de otro usuario debe ser rechazado.