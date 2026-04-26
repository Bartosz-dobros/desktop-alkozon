from desktop_alkozon.features.deliveries.service import DeliveriesService, Delivery


class DeliveriesController:

    def __init__(self):
        self.service = DeliveriesService()

    async def get_couriers(self):
        return await self.service.get_couriers()

    async def get_deliveries(self, status: str | None = None):
        return await self.service.get_deliveries(status)

    async def create_new_announcement(self, title: str, content: str):
        return await self.service.create_announcement(title, content)

    async def get_announcements(self):
        return await self.service.get_announcements()

    async def update_delivery_status(self, delivery_id: int, status: str):
        return await self.service.update_delivery_status(delivery_id, status)

    async def assign_courier(self, delivery_id: int, courier_id: int):
        return await self.service.assign_courier(delivery_id, courier_id)

    def get_couriers_sync(self):
        return self.service.get_couriers_sync()

    def get_deliveries_sync(self):
        return self.service.get_deliveries_sync()
