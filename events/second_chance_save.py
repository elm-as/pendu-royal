class SecondChanceSave():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._second_chance_save = {
            "event_name": "second_chance_save",
            "type": "bonus",
            "rarity": "epic",
            "description": "La dernière erreur est annulée. Vous conservez votre plume.",
            "activate": None
        }