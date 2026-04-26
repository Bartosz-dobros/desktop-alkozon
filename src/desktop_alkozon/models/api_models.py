from pydantic import BaseModel, EmailStr
from typing import Optional
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


class WorkLogStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: Optional[str] = None
    tokenType: str = "Bearer"
    expiresIn: int


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


class RawMaterial(BaseModel):
    id: int
    name: str
    unit: str
    quantity: int
    lastUpdatedAt: Optional[datetime] = None


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


class DeliveryAnnouncement(BaseModel):
    id: int
    title: str
    content: str
    publishedAt: Optional[datetime] = None
    createdBy: Optional[int] = None
    createdAt: Optional[datetime] = None


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


class WorkLogSummary(BaseModel):
    employeeId: int
    totalHours: float
    totalBreaks: float
    entries: list[WorkLog]


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
