class TaxeEvent():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._taxe_event = {
            "event_name": "taxe_event",
            "type": "penality",
            "rarity": "rare",
            "description": "Une erreure retire X points. Persiste jusqu'à ce que vous validez X lettres",
            "activate": None
        }