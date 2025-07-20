from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.adaptive import SpacedRepetition, Attempt
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Constants for SM-2 like algorithm (consider moving to config)
DEFAULT_EF = Decimal("2.5")
MIN_EF = Decimal("1.3")
INTERVAL_REPETITION_1_DAYS = 1
INTERVAL_REPETITION_2_DAYS = 6  # Or another suitable value like 3 or 4
MAX_INTERVAL_DAYS = 90
INTERVAL_AFTER_INCORRECT_DAYS = 1

logger = logging.getLogger(__name__)

def calculate_difficulty(ef: Decimal, repetition_number: int) -> str:
    if ef < Decimal("1.8") or repetition_number <= 1:
        return "hard"
    elif ef < Decimal("2.8") and repetition_number <= 3: # ef >= 1.8 implicit
        return "normal"
    else: # ef >= 2.8 and repetition_number > 3
        return "easy"

async def update_spaced_repetition_for_item(
    db: AsyncSession,
    user_id_hash: str,
    course: str,
    item_id: int,
    is_correct_response: bool
):
    result = await db.execute(select(SpacedRepetition).filter(
        SpacedRepetition.user_id_hash == user_id_hash,
        SpacedRepetition.item_id == item_id
    ))
    sr_item = result.scalars().first()

    now = datetime.utcnow()

    if not sr_item:
        sr_item = SpacedRepetition(
            user_id_hash=user_id_hash,
            course=course,
            item_id=item_id,
            last_seen=now,
            times_seen=1,
            easiness_factor=DEFAULT_EF,
            repetition_number=0,
            current_interval_days=0
        )
        if is_correct_response:
            sr_item.times_correct = 1
            sr_item.times_incorrect = 0
            sr_item.repetition_number = 1
            sr_item.current_interval_days = INTERVAL_REPETITION_1_DAYS
            sr_item.next_due = now + timedelta(days=INTERVAL_REPETITION_1_DAYS)
        else:
            sr_item.times_correct = 0
            sr_item.times_incorrect = 1
            sr_item.repetition_number = 0
            sr_item.current_interval_days = INTERVAL_AFTER_INCORRECT_DAYS
            sr_item.next_due = now + timedelta(days=INTERVAL_AFTER_INCORRECT_DAYS)
            sr_item.easiness_factor = max(MIN_EF, DEFAULT_EF - Decimal("0.8"))
        
        sr_item.difficulty = calculate_difficulty(sr_item.easiness_factor, sr_item.repetition_number)
        db.add(sr_item)

    else:
        sr_item.last_seen = now
        sr_item.times_seen += 1
        
        current_ef = Decimal(str(sr_item.easiness_factor))
        
        if is_correct_response:
            sr_item.times_correct += 1
            sr_item.repetition_number += 1

            new_ef = max(MIN_EF, current_ef + Decimal("0.1"))
            sr_item.easiness_factor = new_ef

            if sr_item.repetition_number == 1:
                next_interval_days = INTERVAL_REPETITION_1_DAYS
            elif sr_item.repetition_number == 2:
                next_interval_days = INTERVAL_REPETITION_2_DAYS
            else:
                next_interval_days = round(sr_item.current_interval_days * float(current_ef))
                if next_interval_days < 1:
                    next_interval_days = sr_item.repetition_number
            
            next_interval_days = min(next_interval_days, MAX_INTERVAL_DAYS)
            if next_interval_days < 1:
                 next_interval_days = 1

            sr_item.current_interval_days = next_interval_days
            sr_item.next_due = now + timedelta(days=next_interval_days)

        else:
            sr_item.times_incorrect += 1
            sr_item.repetition_number = 0

            new_ef = max(MIN_EF, current_ef - Decimal("0.4"))
            sr_item.easiness_factor = new_ef
            
            sr_item.current_interval_days = INTERVAL_AFTER_INCORRECT_DAYS
            sr_item.next_due = now + timedelta(days=INTERVAL_AFTER_INCORRECT_DAYS)

        sr_item.difficulty = calculate_difficulty(sr_item.easiness_factor, sr_item.repetition_number)
        db.add(sr_item)

    await db.commit()
    await db.refresh(sr_item)
    return sr_item 