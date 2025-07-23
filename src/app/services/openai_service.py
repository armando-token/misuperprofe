"""
Servicio básico de OpenAI para el motor DECO
"""

import os
from typing import Optional
from openai import OpenAI
from app.config import settings


def get_openai_client() -> OpenAI:
    """
    Obtiene una instancia del cliente de OpenAI
    """
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Si no hay API key, crear un cliente mock para desarrollo
        class MockOpenAIClient:
            def __init__(self):
                self.chat = MockChatCompletions()
        
        class MockChatCompletions:
            def create(self, **kwargs):
                # Retornar respuesta mock para desarrollo
                class MockResponse:
                    def __init__(self):
                        self.choices = [MockChoice()]
                
                class MockChoice:
                    def __init__(self):
                        self.message = MockMessage()
                
                class MockMessage:
                    def __init__(self):
                        self.content = "Respuesta mock para desarrollo. Configura OPENAI_API_KEY para usar OpenAI real."
                
                return MockResponse()
        
        return MockOpenAIClient()
    
    return OpenAI(api_key=api_key)


def is_openai_available() -> bool:
    """
    Verifica si OpenAI está disponible
    """
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    return bool(api_key) 