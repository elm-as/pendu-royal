class DoubleOrNothing():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._double_or_nothing = {
            "event_name": "double_or_nothing",
            "type": "bonus",
            "rarity": "epic",
            "description": "Double ton score ou perd tout",
            "activate": None
        }