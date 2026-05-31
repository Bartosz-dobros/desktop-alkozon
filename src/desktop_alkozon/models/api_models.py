from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, field_validator


class UserRole(StrEnum):
    GUEST = "GUEST"
    CUSTOMER = "CUSTOMER"
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"


class OrderStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    IN_PRODUCTION = "IN_PRODUCTION"
    IN_PACKING = "IN_PACKING"
    IN_DELIVERY = "IN_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class DeliveryStatus(StrEnum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class JobOfferStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str | None = None
    tokenType: str = "Bearer"
    expiresInSeconds: int


class RefreshRequest(BaseModel):
    refreshToken: str


class User(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    firstName: str | None = None
    lastName: str | None = None
    phone: str | None = None
    isActive: bool = True
    ageConfirmedAt: datetime | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class UserAdminResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    active: bool
    courier: bool
    ageConfirmedAt: datetime | None = None


class Product(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    price: float
    volumeMl: int | None = None
    abv: float | None = None
    imageUrl: str | None = None
    isActive: bool = True
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class InventoryItem(BaseModel):
    id: int
    productId: int | None = None
    rawMaterialId: int | None = None
    quantity: int
    warehouseZone: str | None = None
    lastUpdatedAt: datetime | None = None
    product: Product | None = None


class Order(BaseModel):
    id: int
    customerId: int
    status: OrderStatus
    deliveryAddress: str
    totalAmount: float
    createdAt: datetime | None = None
    updatedAt: datetime | None = None
    deliveredAt: datetime | None = None


class OrderItem(BaseModel):
    id: int
    orderId: int
    productId: int
    quantity: int
    unitPrice: float
    product: Product | None = None


class Delivery(BaseModel):
    id: int
    orderId: int
    courierId: int | None = None
    status: DeliveryStatus
    addressSnapshot: str
    startedAt: datetime | None = None
    deliveredAt: datetime | None = None
    order: Order | None = None
    courier: User | None = None


class JobOffer(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: JobOfferStatus = JobOfferStatus.OPEN
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class WorkLog(BaseModel):
    id: int
    employeeId: int
    clockInAt: datetime
    clockOutAt: datetime | None = None
    breakStartedAt: datetime | None = None
    breakEndedAt: datetime | None = None
    notes: str | None = None


class JobOfferResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: JobOfferStatus
    createdAt: datetime
    updatedAt: datetime


class JobOfferRequest(BaseModel):
    title: str
    description: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    firstName: str | None = None
    lastName: str | None = None
    ageConfirmed: bool = True
    adultConfirmed: bool = True


class CreateEmployeeRequest(BaseModel):
    email: str
    password: str
    firstName: str | None = None
    lastName: str | None = None
    courier: bool = False
    role: UserRole = UserRole.EMPLOYEE


class PatchUserRequest(BaseModel):
    role: UserRole
    active: bool
    courier: bool


class InventoryProductRow(BaseModel):
    productId: int
    name: str
    quantity: int
    warehouseZone: str | None = None


class InventoryRawRow(BaseModel):
    id: int
    name: str
    unit: str
    quantity: float


class InventoryOverviewResponse(BaseModel):
    products: list[InventoryProductRow]
    rawMaterials: list[InventoryRawRow]


class DeliveryDetails(BaseModel):
    recipientName: str | None = None
    streetAddress: str | None = None
    city: str | None = None
    postalCode: str | None = None
    country: str | None = None
    deliveryNotes: str | None = None
    paymentMethod: str | None = None


class DeliveryResponse(BaseModel):
    id: int
    orderId: int | None = None
    customOrderId: int | None = None
    customOrder: bool = False
    clientOrderNumber: str | None = None
    courierId: int | None = None
    courierEmail: str | None = None
    status: DeliveryStatus
    deliveryDetails: DeliveryDetails | None = None
    customerEmail: str | None = None
    startedAt: datetime | None = None
    deliveredAt: datetime | None = None

    @field_validator("startedAt", "deliveredAt", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


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
    publishedAt: str | None = None
    createdBy: int | None = None
    createdAt: datetime | None = None


class DeliveryAnnouncementRequest(BaseModel):
    title: str
    content: str


class DeliveryAnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    createdBy: int | None = None
    createdAt: datetime | None = None


class WorkLogResponse(BaseModel):
    id: int
    employeeId: int
    clockInAt: datetime
    clockOutAt: datetime | None = None
    breakStartedAt: datetime | None = None
    breakEndedAt: datetime | None = None


class WorkSummaryResponse(BaseModel):
    totalHours: float
    totalBreaks: float
    entries: list[WorkLogResponse]


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


class ReplenishmentLine(BaseModel):
    id: int
    productId: int | None = None
    rawMaterialId: int | None = None
    quantityDelta: int
    productName: str | None = None
    rawMaterialName: str | None = None


class WarehouseReplenishment(BaseModel):
    id: int
    status: str
    note: str | None = None
    createdAt: datetime
    lines: list[ReplenishmentLine] | None = None


class CreateReplenishmentRequest(BaseModel):
    lines: list[dict]
    note: str | None = None
