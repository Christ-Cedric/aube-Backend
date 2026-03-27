from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.transaction import (
    TransactionCreate,
    TransactionOut,
    TransactionBulkCreate,
    TransactionStats,
    TransactionFilter
)
from app.services.transaction_service import TransactionService, get_transaction_service
from app.core.security import get_current_user
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# ========== ROUTES UTILISATEUR ==========

@router.post("/", response_model=TransactionOut, status_code=201)
async def create_transaction(
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Crée une nouvelle transaction pour l'utilisateur connecté"""
    return await service.create_transaction(current_user.id, transaction_in)


@router.post("/sync", status_code=200)
async def sync_transactions(
    bulk_data: TransactionBulkCreate,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Synchronise plusieurs transactions en une fois.
    Utilisé pour uploader les transactions stockées localement.
    """
    return await service.bulk_create_transactions(current_user.id, bulk_data)


@router.get("/my-transactions", response_model=List[TransactionOut])
async def get_my_transactions(
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Récupère les transactions de l'utilisateur connecté"""
    return await service.get_user_transactions(current_user.id, limit, skip)


@router.get("/my-stats", response_model=TransactionStats)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """Récupère les statistiques de l'utilisateur connecté"""
    return await service.get_user_stats(current_user.id)


# ========== ROUTES ADMIN ==========

@router.get("/user/{user_id}", response_model=List[TransactionOut])
async def get_user_transactions_admin(
    user_id: UUID,
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    [ADMIN] Récupère les transactions d'un utilisateur spécifique
    """
    return await service.get_user_transactions(user_id, limit, skip)


@router.get("/user/{user_id}/stats", response_model=TransactionStats)
async def get_user_stats_admin(
    user_id: UUID,
    current_admin: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    [ADMIN] Récupère les statistiques d'un utilisateur spécifique
    """
    return await service.get_user_stats(user_id)


@router.post("/search", response_model=List[TransactionOut])
async def search_transactions(
    filters: TransactionFilter,
    current_admin: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    [ADMIN] Recherche de transactions avec filtres avancés
    """
    return await service.get_transactions_by_filters(filters)


@router.get("/all", response_model=List[TransactionOut])
async def get_all_transactions(
    limit: int = Query(100, le=500),
    skip: int = Query(0, ge=0),
    type_transaction: str = Query(None),
    operateur: str = Query(None),
    current_admin: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    [ADMIN] Récupère toutes les transactions avec pagination et filtres optionnels
    """
    filters = TransactionFilter(
        type_de_transaction=type_transaction,
        operateur=operateur,
        limit=limit,
        skip=skip
    )
    return await service.get_transactions_by_filters(filters)