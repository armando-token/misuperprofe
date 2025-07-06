from sqlalchemy.types import TypeDecorator, DateTime
from sqlalchemy.engine.interfaces import Dialect
from datetime import datetime, timezone
import logging
from typing import Any

logger = logging.getLogger(__name__)

class NaiveDateTime(TypeDecorator):
    """
    Almacena y recupera datetimes como naive UTC.
    Asegura que cualquier datetime enviado a la base de datos sea naive (UTC).
    Asume que los datetimes leídos de la base de datos son UTC naive.
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is not None:
            # Solo loguear si el valor no es None, para evitar problemas con expresiones SQL como func.now()
            if isinstance(value, datetime):
                logger.info(f"NaiveDateTime.process_bind_param llamado con datetime: {value} (tzinfo: {value.tzinfo})")
                if value.tzinfo is not None:
                    logger.warning(f"NaiveDateTime procesando un datetime CON timezone: {value}. Se convertirá a UTC y se eliminará tzinfo.")
                    value = value.astimezone(timezone.utc)
                value = value.replace(tzinfo=None)
            # Si es una expresión SQL (como func.now()), no intentar acceder a tzinfo
            # y simplemente dejar que SQLAlchemy/la BBDD la manejen.
        return value

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        if value is not None and isinstance(value, datetime):
            # logger.info(f"NaiveDateTime.process_result_value llamado con: {value} (tzinfo: {value.tzinfo})")
            # Los valores de la BBDD (TIMESTAMP WITHOUT TIME ZONE) no deberían tener tzinfo.
            # Si lo tuvieran por alguna razón, se elimina para asegurar que sean naive.
            value = value.replace(tzinfo=None)
        return value 