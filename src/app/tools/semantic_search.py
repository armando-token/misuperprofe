import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.capitulo import Capitulo
from app.models.curso import Curso
from config import settings
import config
import db
import asyncio
import re
import unicodedata
import string
from app.db.session import get_session

class SemanticSearch:
    def __init__(self, capitulos, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.45):
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.capitulos = capitulos
        self.titulos = [c.titulo for c in capitulos]
        self.embeddings = None
        self.index = None
        self._load_data()

    def _load_data(self):
        textos = [c.contenido_html or c.contenido_md or "" for c in self.capitulos]
        if textos:
            self.embeddings = self.model.encode(textos, show_progress_bar=False, device="cpu")
            self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
            self.index.add(np.array(self.embeddings, dtype=np.float32))

    def normalize_text(self, text):
        # Convierte a minúsculas, elimina tildes y signos de puntuación
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text

    def buscar(self, pregunta: str):
        if not self.capitulos:
            return None
        pregunta_norm = self.normalize_text(pregunta)

        # --- Nueva lógica: extracción de término clave en preguntas de definición o lista ---
        patrones_definicion = [
            r'que es (.+)', r'qué es (.+)', r'definicion de (.+)', r'definición de (.+)', r'describe (.+)', r'que son (.+)', r'qué son (.+)',
            r'cuales son (.+)', r'cuáles son (.+)', r'nombra (.+)', r'menciona (.+)', r'lista (.+)', r'enumera (.+)'
        ]
        termino_clave = None
        for patron in patrones_definicion:
            match = re.match(patron, pregunta_norm)
            if match:
                termino_clave = match.group(1).strip()
                break
        # Eliminar artículos y preposiciones comunes del término clave para mejorar el match
        if termino_clave:
            stopwords_titulos = set(['el', 'la', 'los', 'las', 'de', 'del', 'un', 'una', 'en', 'al', 'por', 'para', 'y', 'a'])
            termino_clave = ' '.join([w for w in termino_clave.split() if w not in stopwords_titulos])
            for cap in self.capitulos:
                titulo_norm = self.normalize_text(cap.titulo)
                titulo_norm_simple = ' '.join([w for w in titulo_norm.split() if w not in stopwords_titulos])
                if termino_clave == titulo_norm_simple or termino_clave in titulo_norm_simple or titulo_norm_simple in termino_clave:
                    # Si el capítulo no tiene contenido, buscar el primer subcapítulo relevante
                    if not (cap.contenido_html or cap.contenido_md):
                        subcap = self._buscar_subcapitulo_contenido(cap.titulo)
                        if subcap:
                            print(f"[SemanticSearch] Match en subcapítulo por término clave: '{subcap.titulo}'")
                            return {
                                "titulo": subcap.titulo,
                                "contenido": subcap.contenido_html or subcap.contenido_md,
                                "tipo": "match_subcapitulo"
                            }
                    print(f"[SemanticSearch] Match directo por término clave en título: '{cap.titulo}'")
                    return {
                        "titulo": cap.titulo,
                        "contenido": cap.contenido_html or cap.contenido_md,
                        "tipo": "match_termino_clave"
                    }

        # 1. Búsqueda directa por coincidencia exacta o parcial en títulos/subtítulos
        for cap in self.capitulos:
            titulo_norm = self.normalize_text(cap.titulo)
            if titulo_norm == pregunta_norm or titulo_norm in pregunta_norm or pregunta_norm in titulo_norm:
                # Si el capítulo no tiene contenido, buscar el primer subcapítulo relevante
                if not (cap.contenido_html or cap.contenido_md):
                    subcap = self._buscar_subcapitulo_contenido(cap.titulo)
                    if subcap:
                        print(f"[SemanticSearch] Match en subcapítulo por coincidencia en título: '{subcap.titulo}'")
                        return {
                            "titulo": subcap.titulo,
                            "contenido": subcap.contenido_html or subcap.contenido_md,
                            "tipo": "match_subcapitulo"
                        }
                print(f"[SemanticSearch] Match directo en título: '{cap.titulo}'")
                return {
                    "titulo": cap.titulo,
                    "contenido": cap.contenido_html or cap.contenido_md,
                    "tipo": "match_titulo"
                }

        # 2. Búsqueda semántica
        if self.index:
            pregunta_emb = self.model.encode([pregunta], show_progress_bar=False, device="cpu")
            D, I = self.index.search(np.array(pregunta_emb, dtype=np.float32), k=1)
            idx = int(I[0][0])
            score = 1 - D[0][0] / 4  # L2 a similitud aproximada
            print(f"[SemanticSearch] Score de similitud: {score:.3f} para pregunta: '{pregunta}'")
            if score >= self.threshold:
                cap = self.capitulos[idx]
                print(f"[SemanticSearch] Match semántico: '{cap.titulo}' (score: {score:.3f})")
                return {
                    "titulo": cap.titulo,
                    "contenido": cap.contenido_html or cap.contenido_md,
                    "tipo": "semantic"
                }

        # 3. Fallbacks existentes
        # Fallback: búsqueda clásica por substring exacto en títulos
        for cap in self.capitulos:
            if self.normalize_text(cap.titulo) in pregunta_norm:
                print(f"[SemanticSearch] Fallback por substring en título: '{cap.titulo}'")
                return {
                    "titulo": cap.titulo,
                    "contenido": cap.contenido_html or cap.contenido_md,
                    "tipo": "substring"
                }
        # Fallback: búsqueda por palabras clave individuales del título
        for cap in self.capitulos:
            if any(word in pregunta_norm for word in self.normalize_text(cap.titulo).split()):
                print(f"[SemanticSearch] Fallback por palabra clave en título: '{cap.titulo}'")
                return {
                    "titulo": cap.titulo,
                    "contenido": cap.contenido_html or cap.contenido_md,
                    "tipo": "keyword"
                }
        # Fallback: búsqueda por score de palabras clave en el contenido
        stopwords = set([
            'que', 'en', 'el', 'la', 'los', 'las', 'de', 'del', 'y', 'a', 'un', 'una', 'su', 'por', 'con', 'para', 'se', 'al', 'como', 'es', 'lo', 'sus', 'más', 'o', 'e', 'u', 'sobre', 'sin', 'ya', 'pero', 'si', 'le', 'les', 'donde', 'cuando', 'cual', 'cuales', 'cuyo', 'cuyos', 'cuyas', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'mi', 'mis', 'tu', 'tus', 'nuestro', 'nuestra', 'vuestro', 'vuestra', 'vosotros', 'vosotras', 'ellos', 'ellas', 'nosotros', 'nosotras', 'yo', 'tú', 'él', 'ella', 'nos', 'os', 'me', 'te', 'se', 'sí', 'mío', 'mía', 'tuyo', 'tuya', 'suyo', 'suya', 'nuestro', 'nuestra', 'vuestro', 'vuestra', 'suyos', 'suyas', 'nuestros', 'nuestras', 'vuestros', 'vuestras', 'este', 'ese', 'aquel', 'esto', 'eso', 'aquello', 'cada', 'cualquiera', 'quien', 'quienes', 'alguien', 'nadie', 'algo', 'nada', 'mucho', 'poco', 'demasiado', 'bastante', 'tanto', 'tan', 'tal', 'casi', 'siempre', 'nunca', 'jamás', 'todavía', 'aún', 'ya', 'antes', 'después', 'luego', 'entonces', 'mientras', 'aquí', 'allí', 'allá', 'acá', 'arriba', 'abajo', 'cerca', 'lejos', 'dentro', 'fuera', 'encima', 'debajo', 'delante', 'detrás', 'frente', 'tras', 'pronto', 'tarde', 'temprano', 'hoy', 'mañana', 'ayer', 'pasado', 'presente', 'futuro', 'primero', 'segundo', 'tercero', 'nuevo', 'viejo', 'gran', 'grande', 'pequeño', 'menor', 'mayor', 'mejor', 'peor', 'igual', 'distinto', 'diferente', 'varios', 'algunos', 'ninguno', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez'
        ])
        palabras = [w for w in re.findall(r'\w+', pregunta_norm) if w not in stopwords and len(w) > 2]
        best_score = 0
        best_cap = None
        for cap in self.capitulos:
            contenido = self.normalize_text(cap.contenido_html or cap.contenido_md or "")
            score = sum(1 for w in palabras if w in contenido)
            if score > best_score:
                best_score = score
                best_cap = cap
        # Umbral mínimo de matches relevantes (ajustable)
        if best_score >= 2 and best_cap:
            print(f"[SemanticSearch] Fallback por score de palabras clave en contenido: '{best_cap.titulo}' (score: {best_score})")
            return {
                "titulo": best_cap.titulo,
                "contenido": best_cap.contenido_html or best_cap.contenido_md,
                "tipo": "contenido_score"
            }
        # Fallback final: primer capítulo
        cap = self.capitulos[0]
        print(f"[SemanticSearch] Fallback por defecto: '{cap.titulo}'")
        return {
            "titulo": cap.titulo,
            "contenido": cap.contenido_html or cap.contenido_md,
            "tipo": "default"
        }

    def _buscar_subcapitulo_contenido(self, titulo_principal):
        # 1. Prioriza subcapítulo cuyo título sea exactamente 'Definición de biología' (o termine así)
        for cap in self.capitulos:
            titulo_norm = self.normalize_text(cap.titulo)
            if (
                cap.titulo.startswith(titulo_principal)
                and (cap.contenido_html or cap.contenido_md)
                and (titulo_norm.endswith('definicion de biologia') or titulo_norm == 'definicion de biologia')
            ):
                return cap
        # 2. Luego prioriza subcapítulo con 'definición de biología' en el título
        for cap in self.capitulos:
            if (
                cap.titulo.startswith(titulo_principal)
                and (cap.contenido_html or cap.contenido_md)
                and 'definicion de biologia' in self.normalize_text(cap.titulo)
            ):
                return cap
        # 3. Si no hay, devuelve el primer subcapítulo con contenido
        for cap in self.capitulos:
            if cap.titulo.startswith(titulo_principal) and (cap.contenido_html or cap.contenido_md):
                return cap
        return None

# Instancia global y lock para inicialización segura
_semantic_search_instance = None
_semantic_search_lock = asyncio.Lock()

async def get_semantic_search():
    global _semantic_search_instance
    if _semantic_search_instance is not None:
        return _semantic_search_instance
    async with _semantic_search_lock:
        if _semantic_search_instance is not None:
            return _semantic_search_instance
        from db.session import get_session
        async for session in get_session():
            result = await session.execute(select(Capitulo).order_by(Capitulo.orden))
            capitulos = result.scalars().all()
            break
        _semantic_search_instance = SemanticSearch(capitulos)
        return _semantic_search_instance 