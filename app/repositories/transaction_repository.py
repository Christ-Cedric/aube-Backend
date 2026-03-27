from app.repositories.base_repository import BaseRepository
from app.models.transaction import Transaction
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, Transaction)

    async def get_by_user(self, user_id: UUID, limit: int = 50, skip: int = 0) -> List[Transaction]:
        """Récupère toutes les transactions d'un utilisateur"""
        docs = await self.collection.find(
            {"user_id": str(user_id)}
        ).sort("date_de_transaction", -1).skip(skip).limit(limit).to_list(None)
        
        return [Transaction(**doc) for doc in docs]

    async def get_by_user_and_date_range(
        self, 
        user_id: UUID, 
        date_debut: datetime, 
        date_fin: datetime
    ) -> List[Transaction]:
        """Récupère les transactions d'un utilisateur sur une période"""
        docs = await self.collection.find({
            "user_id": str(user_id),
            "date_de_transaction": {
                "$gte": date_debut,
                "$lte": date_fin
            }
        }).sort("date_de_transaction", -1).to_list(None)
        
        return [Transaction(**doc) for doc in docs]

    async def get_by_filters(self, filters: dict) -> List[Transaction]:
        """Récupère les transactions selon des filtres"""
        query = {}
        
        if filters.get("user_id"):
            query["user_id"] = str(filters["user_id"])
        
        if filters.get("type_de_transaction"):
            query["type_de_transaction"] = filters["type_de_transaction"]
        
        if filters.get("operateur"):
            query["operateur"] = filters["operateur"]
        
        if filters.get("date_debut") or filters.get("date_fin"):
            query["date_de_transaction"] = {}
            if filters.get("date_debut"):
                query["date_de_transaction"]["$gte"] = filters["date_debut"]
            if filters.get("date_fin"):
                query["date_de_transaction"]["$lte"] = filters["date_fin"]
        
        if filters.get("montant_min") or filters.get("montant_max"):
            query["montant"] = {}
            if filters.get("montant_min"):
                query["montant"]["$gte"] = filters["montant_min"]
            if filters.get("montant_max"):
                query["montant"]["$lte"] = filters["montant_max"]
        
        limit = filters.get("limit", 50)
        skip = filters.get("skip", 0)
        
        docs = await self.collection.find(query).sort(
            "date_de_transaction", -1
        ).skip(skip).limit(limit).to_list(None)
        
        return [Transaction(**doc) for doc in docs]

    async def get_stats_by_user(self, user_id: UUID) -> dict:
        """Calcule les statistiques pour un utilisateur"""
        pipeline = [
            {"$match": {"user_id": str(user_id)}},
            {
                "$group": {
                    "_id": "$type_de_transaction",
                    "count": {"$sum": 1},
                    "total_montant": {"$sum": "$montant"}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        
        stats = {
            "total_transactions": 0,
            "total_retraits": 0,
            "total_depots": 0,
            "total_transferts": 0,
            "montant_total_retraits": 0.0,
            "montant_total_depots": 0.0,
            "montant_total_transferts": 0.0,
        }
        
        for result in results:
            type_trans = result["_id"]
            count = result["count"]
            montant = result["total_montant"]
            
            stats["total_transactions"] += count
            
            if type_trans == "Retrait":
                stats["total_retraits"] = count
                stats["montant_total_retraits"] = montant
            elif type_trans == "Dépot":
                stats["total_depots"] = count
                stats["montant_total_depots"] = montant
            elif type_trans == "Transfert":
                stats["total_transferts"] = count
                stats["montant_total_transferts"] = montant
        
        # Statistiques par opérateur
        pipeline_op = [
            {"$match": {"user_id": str(user_id)}},
            {
                "$group": {
                    "_id": "$operateur",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        op_results = await self.collection.aggregate(pipeline_op).to_list(None)
        stats["transactions_par_operateur"] = {
            r["_id"]: r["count"] for r in op_results
        }
        
        # Dernière transaction
        last_trans = await self.collection.find_one(
            {"user_id": str(user_id)},
            sort=[("date_de_transaction", -1)]
        )
        
        if last_trans:
            stats["derniere_transaction"] = last_trans["date_de_transaction"]
        
        return stats

    async def bulk_create(self, transactions: List[Transaction]) -> int:
        """
        Crée plusieurs transactions en une seule opération.
        Vérifie l'existence (basée sur numero_de_piece + date_de_transaction) pour éviter les doublons.
        """
        if not transactions:
            return 0
        
        inserted_count = 0
        
        # Pour chaque transaction, on vérifie si elle existe déjà
        for trans in transactions:
            # Critère d'unicité : numero_de_piece + date_de_transaction
            exists = await self.collection.find_one({
                "user_id": str(trans.user_id),
                "numero_de_piece": trans.numero_de_piece,
                "date_de_transaction": trans.date_de_transaction
            })
            
            if not exists:
                await self.collection.insert_one(trans.model_dump(mode='json'))
                inserted_count += 1
                
        return inserted_count

    async def count_by_user(self, user_id: UUID) -> int:
        """Compte le nombre de transactions d'un utilisateur"""
        return await self.collection.count_documents({"user_id": str(user_id)})