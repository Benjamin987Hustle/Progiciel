"""
Modèles de données Pydantic pour validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SaleRecord(BaseModel):
    """Représente une ligne de vente"""
    row_id: int
    sales_order_number: str
    line_item: str
    sim_round: int
    sim_step: int
    material_number: str
    material_description: str
    distribution_channel: str
    area: str
    quantity: int
    quantity_delivered: int
    net_value: float
    cost: float
    currency: str = "EUR"

    @property
    def profit(self) -> float:
        return self.net_value - self.cost

    @property
    def margin_pct(self) -> float:
        if self.net_value == 0:
            return 0
        return (self.profit / self.net_value) * 100


class InventorySnapshot(BaseModel):
    """Snapshot inventaire"""
    material_number: str
    material_description: str
    storage_location: str
    stock: int
    restricted: int = 0

    @property
    def available(self) -> int:
        return max(0, self.stock - self.restricted)


class PurchaseOrder(BaseModel):
    """Commande fournisseur"""
    purchasing_order: str
    vendor: str
    material_number: str
    quantity: int
    status: str
    goods_receipt_round: Optional[int] = None
    goods_receipt_step: Optional[int] = None

    @property
    def is_delivered(self) -> bool:
        return self.status == "Delivered"


class ProductionOrder(BaseModel):
    """Ordre production"""
    production_order: str
    material_number: str
    target_quantity: int
    confirmed_quantity: int
    begin_round: int
    begin_step: int
    end_round: int
    end_step: int

    @property
    def is_complete(self) -> bool:
        return self.confirmed_quantity >= self.target_quantity

    @property
    def progress_pct(self) -> float:
        if self.target_quantity == 0:
            return 0
        return (self.confirmed_quantity / self.target_quantity) * 100


class MarketData(BaseModel):
    """Données marché"""
    sim_period: int
    material_description: str
    distribution_channel: str
    area: str
    sales_organization: str
    quantity: int
    average_price: float
    net_value: float


class PricingCondition(BaseModel):
    """Condition prix"""
    material_number: str
    distribution_channel: str
    price: float
    sim_round: int
    sim_step: int


class CompanyValuation(BaseModel):
    """Valorisation entreprise"""
    sim_round: int
    sim_step: int
    bank_cash_account: float
    accounts_receivable: float
    bank_loan: float
    accounts_payable: float
    profit: float
    company_valuation: float
    credit_rating: str
