from pydantic import BaseModel
from typing import List

class Courier(BaseModel):
    id: int
    name: str
    status: str
    vehicle: str

class Delivery(BaseModel):
    id: int
    courier_name: str
    destination: str
    status: str
    announcement: str

class DeliveriesService:
    """Single Responsibility: mock deliveries + couriers data."""

    def __init__(self):
        self.couriers = [
            Courier(id=1, name="Jan Kowalski", status="Dostępny", vehicle="Fiat Ducato"),
            Courier(id=2, name="Anna Nowak", status="W drodze", vehicle="Mercedes Sprinter"),
            Courier(id=3, name="Piotr Wiśniewski", status="Dostępny", vehicle="VW Transporter"),
        ]
        self.deliveries = [
            Delivery(id=101, courier_name="Jan Kowalski", destination="Warszawa Centrum", status="W drodze", announcement="Pilna dostawa piwa"),
        ]

    def get_couriers(self) -> List[Courier]:
        return self.couriers

    def get_deliveries(self) -> List[Delivery]:
        return self.deliveries

    def create_announcement(self, courier_name: str, destination: str, announcement: str) -> Delivery:
        new_id = max(d.id for d in self.deliveries) + 1 if self.deliveries else 101
        new_delivery = Delivery(
            id=new_id,
            courier_name=courier_name,
            destination=destination,
            status="Nowa",
            announcement=announcement
        )
        self.deliveries.append(new_delivery)
        return new_delivery