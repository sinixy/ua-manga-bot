class TeamAlreadyExistsException(Exception):

    def __init__(self, team_name, *args):
        super().__init__(*args)
        self.team_name = team_name

    def __str__(self):
        return f"{self.team_name} already exists!"
    

class UserAlreadyExistsException(Exception):

    def __init__(self, user_id, *args):
        super().__init__(*args)
        self.user_id = user_id

    def __str__(self):
        return f"user-{self.user_id} already exists!"
    

class TargetReminderTypeNotDefinedException(Exception):

    def __str__(self) -> str:
        return f"target_type must be defined"