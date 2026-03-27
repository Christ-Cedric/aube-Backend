from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate, 
    TransactionOut, 
    TransactionBulkCreate,
    TransactionStats,
    TransactionFilter
)
from app.repositories.transaction_repository import TransactionRepository
from fastapi import HTTPException, status
from datetime import datetime, timezone
from typing import List
import uuid

class TransactionService:
    def __init__(self, db):
        self.transaction_repo = TransactionRepository(db["transactions"])

    async def create_transaction(
        self, 
        user_id: uuid.UUID, 
        transaction_in: TransactionCreate
    ) -> TransactionOut:
        """Crée une seule transaction"""
        transaction = Transaction(
            id=transaction_in.id or uuid.uuid4(),
            user_id=user_id,
            **transaction_in.model_dump(exclude={'id'}),
            created_at=datetime.now(timezone.utc),
            synced_at=datetime.now(timezone.utc),
            is_synced=True
        )
        
        await self.transaction_repo.create(transaction)
        return TransactionOut(**transaction.model_dump())

    async def bulk_create_transactions(
        self, 
        user_id: uuid.UUID, 
        bulk_data: TransactionBulkCreate
    ) -> dict:
        """Synchronise plusieurs transactions en une fois"""
        transactions = []
        for trans_data in bulk_data.transactions:
            transaction = Transaction(
                id=trans_data.id or uuid.uuid4(),
                user_id=user_id,
                **trans_data.model_dump(exclude={'id'}),
                created_at=datetime.now(timezone.utc),
                synced_at=datetime.now(timezone.utc),
                is_synced=True
            )
            transactions.append(transaction)
        
        count = await self.transaction_repo.bulk_create(transactions)
        
        return {
            "message": f"{count} transactions synchronisées avec succès",
            "count": count,
            "synced_at": datetime.now(timezone.utc)
        }

    async def get_user_transactions(
        self, 
        user_id: uuid.UUID, 
        limit: int = 50, 
        skip: int = 0
    ) -> List[TransactionOut]:
        """Récupère les transactions d'un utilisateur"""
        transactions = await self.transaction_repo.get_by_user(user_id, limit, skip)
        return [TransactionOut(**t.model_dump()) for t in transactions]

    async def get_user_stats(self, user_id: uuid.UUID) -> TransactionStats:
        """Récupère les statistiques d'un utilisateur"""
        stats = await self.transaction_repo.get_stats_by_user(user_id)
        return TransactionStats(**stats)

    async def get_transactions_by_filters(
        self, 
        filters: TransactionFilter
    ) -> List[TransactionOut]:
        """Récupère les transactions selon des filtres (pour admin)"""
        filter_dict = filters.model_dump(exclude_unset=True)
        transactions = await self.transaction_repo.get_by_filters(filter_dict)
        return [TransactionOut(**t.model_dump()) for t in transactions]

    async def get_all_users_stats(self) -> dict:
        """Statistiques globales (pour admin)"""
        # À implémenter selon vos besoins
        pass

async def get_transaction_service():
    from app.core.database import get_database
    db = await get_database()
    return TransactionService(db)