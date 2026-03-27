from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class TransactionBase(BaseModel):
    nom: str
    prenom: str
    type_de_piece: str
    numero_de_piece: str
    date_de_peremption: datetime
    type_de_transaction: str
    montant: float
    operateur: str
    numero_de_telephone: str
    date_de_transaction: datetime

class TransactionCreate(TransactionBase):
    """Schéma pour créer une transaction depuis le mobile"""
    id: Optional[UUID] = None

class TransactionBulkCreate(BaseModel):
    """Pour synchroniser plusieurs transactions en une seule requête"""
    transactions: List[TransactionCreate]

class TransactionOut(TransactionBase):
    """Schéma de sortie pour une transaction"""
    id: UUID
    user_id: UUID
    created_at: datetime
    synced_at: Optional[datetime] = None
    is_synced: bool

    class Config:
        from_attributes = True

class TransactionStats(BaseModel):
    """Statistiques des transactions d'un utilisateur"""
    total_transactions: int
    total_retraits: int
    total_depots: int
    total_transferts: int
    montant_total_retraits: float
    montant_total_depots: float
    montant_total_transferts: float
    transactions_par_operateur: dict[str, int]
    derniere_transaction: Optional[datetime] = None

class TransactionFilter(BaseModel):
    """Filtres pour la recherche de transactions"""
    user_id: Optional[UUID] = None
    type_de_transaction: Optional[str] = None
    operateur: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    montant_min: Optional[float] = None
    montant_max: Optional[float] = None
    limit: int = 50
    skip: int = 0