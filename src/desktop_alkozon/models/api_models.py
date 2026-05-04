from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    GUEST = "GUEST"
    CUSTOMER = "CUSTOMER"
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"


class OrderStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    IN_PRODUCTION = "IN_PRODUCTION"
    IN_PACKING = "IN_PACKING"
    IN_DELIVERY = "IN_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class JobOfferStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    expiresInSeconds: int


class RefreshRequest(BaseModel):
    refreshToken: str


class User(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    isActive: bool = True
    ageConfirmedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class UserAdminResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    active: bool
    courier: bool
    ageConfirmedAt: Optional[datetime] = None


class Product(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    volumeMl: Optional[int] = None
    abv: Optional[float] = None
    imageUrl: Optional[str] = None
    isActive: bool = True
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class InventoryItem(BaseModel):
    id: int
    productId: Optional[int] = None
    rawMaterialId: Optional[int] = None
    quantity: int
    warehouseZone: Optional[str] = None
    lastUpdatedAt: Optional[datetime] = None
    product: Optional[Product] = None


class Order(BaseModel):
    id: int
    customerId: int
    status: OrderStatus
    deliveryAddress: str
    totalAmount: float
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None


class OrderItem(BaseModel):
    id: int
    orderId: int
    productId: int
    quantity: int
    unitPrice: float
    product: Optional[Product] = None


class Delivery(BaseModel):
    id: int
    orderId: int
    courierId: Optional[int] = None
    status: DeliveryStatus
    addressSnapshot: str
    startedAt: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    order: Optional[Order] = None
    courier: Optional[User] = None


class JobOffer(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: JobOfferStatus = JobOfferStatus.OPEN
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class WorkLog(BaseModel):
    id: int
    employeeId: int
    clockInAt: datetime
    clockOutAt: Optional[datetime] = None
    breakStartedAt: Optional[datetime] = None
    breakEndedAt: Optional[datetime] = None
    notes: Optional[str] = None


class JobOfferResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: JobOfferStatus
    createdAt: datetime
    updatedAt: datetime


class JobOfferRequest(BaseModel):
    title: str
    description: str


class InventoryProductRow(BaseModel):
    productId: int
    name: str
    quantity: int
    warehouseZone: Optional[str] = None


class InventoryRawRow(BaseModel):
    id: int
    name: str
    unit: str
    quantity: float


class InventoryOverviewResponse(BaseModel):
    products: List[InventoryProductRow]
    rawMaterials: List[InventoryRawRow]


class DeliveryResponse(BaseModel):
    id: int
    orderId: int
    courierId: Optional[int] = None
    courierEmail: Optional[str] = None
    status: DeliveryStatus
    addressSnapshot: str
    customerEmail: Optional[str] = None
    startedAt: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None


class PatchQuantityRequest(BaseModel):
    delta: int


class PatchDeliveryAssignRequest(BaseModel):
    courierId: int


class PatchDeliveryStatusRequest(BaseModel):
    status: DeliveryStatus


class DeliveryAnnouncement(BaseModel):
    id: int
    title: str
    content: str
    publishedAt: Optional[str] = None
    createdBy: Optional[int] = None
    createdAt: Optional[datetime] = None


class DeliveryAnnouncementRequest(BaseModel):
    title: str
    content: str


class DeliveryAnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    createdBy: Optional[int] = None
    createdAt: Optional[datetime] = None


class WorkLogResponse(BaseModel):
    id: int
    employeeId: int
    clockInAt: datetime
    clockOutAt: Optional[datetime] = None
    breakStartedAt: Optional[datetime] = None
    breakEndedAt: Optional[datetime] = None


class WorkSummaryResponse(BaseModel):
    totalHours: float
    totalBreaks: float
    entries: List[WorkLogResponse]


class SalesReport(BaseModel):
    totalOrders: int
    totalRevenue: float
    ordersByStatus: dict[str, int]
    period: str


class InventoryReport(BaseModel):
    lowStockItems: list[InventoryItem]
    totalProducts: int
    totalRawMaterials: int
    recentMovements: list[dict]


class WarehouseReplenishment(BaseModel):
    id: int
    status: str
    items: list[dict]
    createdAt: datetime
    createdBy: Optional[int] = None


class CreateReplenishmentRequest(BaseModel):
    items: list[dict]
