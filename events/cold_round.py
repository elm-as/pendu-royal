class ColdRound():
    def __init__(self, event_manager, **kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._cold_round = {
            "event_name": "cold_round",
            "type": "penality",
            "rarity": "rare",
            "description": "Aucune aides pendant X secondes mais les pénalités sont permises.",
            "activate": None
        }