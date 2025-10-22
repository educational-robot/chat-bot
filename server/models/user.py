class User:
    def __init__(self, username: str, is_moderator: bool, is_system_manager: bool,
                 is_fc_site: bool):
        self.username = username
        self.is_moderator = is_moderator
        self.is_system_manager = is_system_manager
        self.is_fc_site = is_fc_site