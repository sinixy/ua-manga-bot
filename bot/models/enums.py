from enum import Enum


class Role(Enum):
    USER = "user"
    ADMIN = "admin"


class RequestStatus(Enum):
    PENDING = "pending"  # the user confirmed team creation and sent it for approval
    APPROVED = "approved"  # team creation has been approved by an admin
    DECLINED = "declined"  # team creation has been declined by an admin


class ReminderType(Enum):
    MINOR = "minor"
    MAJOR = "major"
    CONFIRM_MINOR = "confirm_minor"
    CONFIRM_MAJOR = "confirm_major"

    @classmethod
    def to_ukr(cls, type) -> str:
        type_to_str = {
            cls.MINOR: "звичайне",
            cls.MAJOR: "повне",
            cls.CONFIRM_MINOR: "підтвердження (звичайне)",
            cls.CONFIRM_MAJOR: "підтвердження (повне)"
        }
        return type_to_str[type]