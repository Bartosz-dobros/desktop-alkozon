from desktop_alkozon.features.deliveries.service import DeliveriesService

class DeliveriesController:
    """Single Responsibility: logic between view and service."""

    def __init__(self):
        self.service = DeliveriesService()

    def get_couriers(self):
        return self.service.get_couriers()

    def get_deliveries(self):
        return self.service.get_deliveries()

    def create_new_announcement(self, courier_name: str, destination: str, announcement: str):
        return self.service.create_announcement(courier_name, destination, announcement)