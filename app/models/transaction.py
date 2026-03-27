from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class Transaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID  # Lien vers l'utilisateur
    nom: str
    prenom: str
    type_de_piece: str
    numero_de_piece: str
    date_de_peremption: datetime
    type_de_transaction: str  # Retrait, Dépot, Transfert
    montant: float
    operateur: str  # orange, moov, telecel, coris, sank
    numero_de_telephone: str
    date_de_transaction: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    synced_at: Optional[datetime] = None  # Quand la transaction a été synchronisée
    is_synced: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "nom": "DIALLO",
                "prenom": "Ahmed",
                "type_de_piece": "CNIB",
                "numero_de_piece": "B1234567",
                "date_de_peremption": "2034-01-15T00:00:00",
                "type_de_transaction": "Retrait",
                "montant": 25000.0,
                "operateur": "orange",
                "numero_de_telephone": "+22670123456",
                "date_de_transaction": "2025-02-09T14:30:00"
            }
        }