class GoldRun():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._gold_run = {
            "event_name": "gold_run",
            "type": "bonus",
            "rarity": "epic",
            "description": "Chaque lettre correcte vaut X points",
            "activate": None
        }