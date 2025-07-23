import os
import pickle
import asyncio
import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.models.capitulo import Capitulo
import time
import hashlib
import json

logger = logging.getLogger(__name__)

class SerializedSemanticSearch:
    def __init__(self, cache_dir: str = "embeddings_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.model = None
        self.index = None
        self.chapters = []
        self.is_initialized = False
        self.model_name = "all-MiniLM-L6-v2"
        
        # Archivos de caché
        self.embeddings_file = self.cache_dir / "embeddings.npy"
        self.index_file = self.cache_dir / "faiss_index.bin"
        self.chapters_file = self.cache_dir / "chapters.pkl"
        self.metadata_file = self.cache_dir / "metadata.json"
        
    def _calculate_data_hash(self, chapters: List) -> str:
        content = []
        for ch in chapters:
            content.append(f"{ch.id}_{ch.titulo}_{(ch.contenido_html or ch.contenido_md or '')[:100]}")
        content_str = "||".join(sorted(content))
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _load_metadata(self) -> Optional[Dict]:
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando metadatos: {e}")
        return None
    
    def _save_metadata(self, data_hash: str, chapter_count: int):
        metadata = {
            'data_hash': data_hash,
            'chapter_count': chapter_count,
            'model_name': self.model_name,
            'created_at': time.time()
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)
    
    def _cache_is_valid(self, chapters: List) -> bool:
        try:
            required_files = [
                self.embeddings_file,
                self.index_file, 
                self.chapters_file,
                self.metadata_file
            ]
            if not all(f.exists() for f in required_files):
                logger.info("Archivos de caché faltantes")
                return False
            metadata = self._load_metadata()
            if not metadata:
                logger.info("Metadatos de caché inválidos")
                return False
            current_hash = self._calculate_data_hash(chapters)
            if metadata.get('data_hash') != current_hash:
                logger.info("Datos cambiaron, caché obsoleto")
                return False
            if metadata.get('chapter_count') != len(chapters):
                logger.info("Cantidad de capítulos cambió")
                return False
            logger.info("Caché válido encontrado")
            return True
        except Exception as e:
            logger.warning(f"Error validando caché: {e}")
            return False
    
    def _load_from_cache(self) -> bool:
        try:
            logger.info("Cargando desde caché serializado...")
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name)
            embeddings = np.load(self.embeddings_file)
            logger.info(f"Embeddings cargados: {embeddings.shape}")
            self.index = faiss.read_index(str(self.index_file))
            logger.info(f"Índice FAISS cargado: {self.index.ntotal} vectores")
            with open(self.chapters_file, 'rb') as f:
                self.chapters = pickle.load(f)
            logger.info(f"Capítulos cargados: {len(self.chapters)}")
            load_time = time.time() - start_time
            logger.info(f"Caché cargado en {load_time:.2f} segundos")
            return True
        except Exception as e:
            logger.error(f"Error cargando caché: {e}")
            return False
    
    def _save_to_cache(self, embeddings: np.ndarray):
        try:
            logger.info("Guardando en caché serializado...")
            np.save(self.embeddings_file, embeddings)
            faiss.write_index(self.index, str(self.index_file))
            with open(self.chapters_file, 'wb') as f:
                pickle.dump(self.chapters, f)
            data_hash = self._calculate_data_hash(self.chapters)
            self._save_metadata(data_hash, len(self.chapters))
            logger.info("Caché guardado exitosamente")
        except Exception as e:
            logger.error(f"Error guardando caché: {e}")
    
    async def _load_chapters_from_db(self) -> List:
        async for session in get_session():
            result = await session.execute(
                select(Capitulo).order_by(Capitulo.id)
            )
            return result.scalars().all()
    
    def _calculate_embeddings(self, chapters: List) -> np.ndarray:
        logger.info(f"Calculando embeddings para {len(chapters)} capítulos...")
        texts = []
        for ch in chapters:
            text = f"{ch.titulo}. {(ch.contenido_html or ch.contenido_md or '')[:300]}"
            texts.append(text)
        batch_size = 8
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.info(f"Procesando lote {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            batch_embeddings = self.model.encode(
                batch,
                batch_size=len(batch),
                show_progress_bar=False,
                convert_to_numpy=True
            )
            all_embeddings.extend(batch_embeddings)
        return np.array(all_embeddings, dtype=np.float32)
    
    async def initialize(self, force_rebuild: bool = False):
        if self.is_initialized and not force_rebuild:
            logger.info("Motor ya inicializado")
            return
        start_time = time.time()
        logger.info(">>> [SEMANTIC_SEARCH_INIT] Iniciando inicialización del motor semántico optimizado...")
        try:
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 1: Cargando capítulos desde DB...")
            chapters = await self._load_chapters_from_db()
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Paso 1.1: Capítulos cargados desde DB: {len(chapters) if chapters else 'None'}")
            
            self.chapters = chapters
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 1.2: self.chapters asignado.")

            if not chapters:
                logger.warning(">>> [SEMANTIC_SEARCH_INIT] No hay capítulos en la base de datos. El motor semántico no se inicializará completamente.")
                self.is_initialized = False # Asegurarse que no se considere inicializado
                return # Salir de la inicialización si no hay capítulos
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Cargados {len(chapters)} capítulos desde DB (confirmación).")
            
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 2: Validando caché...")
            cache_is_valid_result = self._cache_is_valid(chapters)
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Paso 2.1: Resultado de _cache_is_valid: {cache_is_valid_result}")

            if not force_rebuild and cache_is_valid_result:
                logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 3: Caché válido, intentando cargar desde caché...")
                if self._load_from_cache():
                    self.is_initialized = True
                    total_time = time.time() - start_time
                    logger.info(f">>> [SEMANTIC_SEARCH_INIT] Inicialización desde caché completada en {total_time:.2f}s")
                    return
                else:
                    logger.warning(">>> [SEMANTIC_SEARCH_INIT] Fallo al cargar desde un caché que se consideraba válido. Reconstruyendo...")
            
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 4: Generando embeddings desde cero (o porque el caché no es válido/falló)...")
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 4.1: Cargando modelo SentenceTransformer...")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Paso 4.2: Modelo SentenceTransformer ({self.model_name}) cargado.")
            
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 4.3: Calculando embeddings...")
            embeddings = self._calculate_embeddings(chapters)
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Paso 4.4: Embeddings calculados. Shape: {embeddings.shape if embeddings is not None else 'None'}")
            
            dimension = embeddings.shape[1]
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Paso 4.5: Dimensión de embeddings: {dimension}")
            
            self.index = faiss.IndexFlatIP(dimension)
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 4.6: Índice FAISS (IndexFlatIP) creado.")
            
            faiss.normalize_L2(embeddings)
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 4.7: Embeddings normalizados (L2).")
            
            self.index.add(embeddings)
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Paso 4.8: Embeddings añadidos al índice FAISS. Total vectores: {self.index.ntotal}")
            
            self._save_to_cache(embeddings)
            logger.info(">>> [SEMANTIC_SEARCH_INIT] Paso 4.9: Caché guardado.")
            
            self.is_initialized = True
            total_time = time.time() - start_time
            logger.info(f">>> [SEMANTIC_SEARCH_INIT] Inicialización completa desde cero en {total_time:.2f}s")
        except Exception as e:
            logger.error(f">>> [SEMANTIC_SEARCH_INIT] Error en inicialización: {e}", exc_info=True)
            raise
    
    async def search(self, query: str, k: int = 3) -> List[Tuple]:
        if not self.is_initialized:
            await self.initialize()
        try:
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            query_embedding = query_embedding.astype(np.float32)
            faiss.normalize_L2(query_embedding)
            scores, indices = self.index.search(query_embedding, min(k, len(self.chapters)))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.chapters):
                    results.append((self.chapters[idx], float(score)))
            return results
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

# Singleton para el motor de búsqueda semántica
_semantic_search_instance = None

async def get_semantic_search() -> SerializedSemanticSearch:
    """
    Obtiene la instancia singleton del motor de búsqueda semántica (OPTIMIZADO)
    """
    global _semantic_search_instance
    
    if _semantic_search_instance is None:
        logger.info("Inicializando motor de búsqueda semántica...")
        _semantic_search_instance = SerializedSemanticSearch()
        await _semantic_search_instance.initialize()
        logger.info("Motor de búsqueda semántica inicializado")
    
    return _semantic_search_instance 