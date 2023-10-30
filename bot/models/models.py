from bson import ObjectId
from time import time
from datetime import datetime

from bot.db import db
from bot.config import Config
from bot.scheduler import scheduler
from .enums import Role, RequestStatus, ReminderType
from bot.exceptions import TeamAlreadyExistsException, UserAlreadyExistsException


class User:

    def __init__(self, id: int, role: Role, banned: bool, created_at: float):
        self._id: int = id  # telegram user/chat id; User.id = Team.id
        self._role: Role = role
        self._banned: bool = banned
        self._created_at: float = created_at

    async def get_team(self):
        return await Team.get(self._id)
    
    async def get_reminders(self):
        reminders = []
        async for reminder in db.reminders.find({"receiver_id": self._id}):
            reminders.append(Reminder.from_doc(reminder))
        return reminders
    
    async def change_role(self, role: Role):
        await db.users.update_one({"_id": self._id}, {"$set": {"role": role.value}})
        self._role = role

    async def ban(self):
        await db.users.update_one({"_id": self._id}, {"$set": {"banned": True}})
        self._banned = True

    async def unban(self):
        await db.users.update_one({"_id": self._id}, {"$set": {"banned": False}})
        self._banned = False

    async def find_requests(self, status: RequestStatus = RequestStatus.PENDING):
        requests = []
        async for request in db.requests.find({"status": status.value}):
            requests.append(Request.from_doc(request))
        return requests

    @classmethod
    async def get(cls, id: int):
        user = await db.users.find_one({"_id": id})
        if not user:
            return None
        
        return cls.from_doc(user)

    @classmethod
    async def find(cls, query: dict = {}):
        users = []
        async for doc in db.users.find(query):
            users.append(cls.from_doc(doc))
        return users

    @classmethod
    async def find_admins(cls):
        return await cls.find({"role": Role.ADMIN.value})
    
    @classmethod
    async def create(
        cls,
        id: int,
        role: Role = Role.USER,
        banned: bool = False,
        if_exists: str = "raise"
    ):
        user = await User.get(id)
        if user:
            if if_exists == "return":
                return user
            else:
                raise UserAlreadyExistsException(id)
            

        user_data = {"_id": id, "role": role.value, "banned": banned, "created_at": time()}
        await db.users.insert_one(user_data)

        return cls.from_doc(user_data)

    @classmethod
    def from_doc(cls, data: dict):
        return cls(
            id=data["_id"],
            role=Role[data["role"].upper()],
            banned=data["banned"],
            created_at=data["created_at"]
        )
    
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def role(self) -> Role:
        return self._role
    
    @property
    def banned(self) -> bool:
        return self._banned
    
    @property
    def created_at(self) -> float:
        return self._created_at


class Team:

    def __init__(self, id: int, name: str, created_at: float):
        self._id: int = id  # User.id = Team.id
        self._name: str = name
        self._created_at: float = created_at

    async def get_owner(self):
        return await User.get(self._id)
    
    async def change_name(self, new_name: str):
        await db.teams.update_one({"_id": self._id}, {"$set": {"name": new_name}})
        self._name = new_name

    async def delete(self):
        await db.teams.delete_one({"_id": self._id})

    @classmethod
    async def get(cls, id: int = -1, name: str = None):
        if name:
            team = await db.teams.find_one({"name": name})
        else:
            team = await db.teams.find_one({"_id": id})

        if not team:
            return None

        return cls.from_doc(team)
    
    @classmethod
    async def find(cls, query: dict = {}, page: int = 0, count: int = Config.ITEMS_PER_PAGE):
        teams = []
        async for doc in db.teams.find(query).skip(page * count).limit(count):
            teams.append(cls.from_doc(doc))
        return teams
    
    @classmethod
    async def create(cls, id: int, name: str):
        if await db.teams.find_one({"name": name}):
            raise TeamAlreadyExistsException(name)

        team = {"_id": id, "name": name, "created_at": time()}
        await db.teams.insert_one(team)

        return cls.from_doc(team)
    
    @classmethod
    async def get_count(cls, query: dict = {}):
        return await db.teams.count_documents(query)
    
    @classmethod
    def from_doc(cls, data: dict):
        return cls(
            id=data["_id"],
            name=data["name"],
            created_at=data["created_at"]
        )
    
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def created_at(self) -> float:
        return self._created_at
    

class Request:
    
    def __init__(
            self,
            id: ObjectId,
            sender: int,
            team_name: str,
            status: RequestStatus,
            approval_info: dict,
            created_at: float
        ):
        self._id: ObjectId = id
        self._sender: int = sender
        self._team_name: str = team_name
        self._status: RequestStatus = status
        self._approval_info: dict = approval_info
        self._created_at: float = created_at

    async def _change_status(self, new_status: RequestStatus, new_approval_info: dict = None):
        self._status = new_status
        if new_approval_info:
            self._approval_info = new_approval_info

        await db.requests.update_one(
            {"_id": self._id},
            {
                "$set": {
                    "status": self._status.value,
                    "approval_info": self._approval_info
                }
            }
        )

    async def approve(self, approved_by: int, approved_at: int):
        await self._change_status(RequestStatus.APPROVED, {"by": approved_by, "at": approved_at})
        
    async def decline(self, declined_by: int, declined_at: int):
        await self._change_status(RequestStatus.DECLINED, {"by": declined_by, "at": declined_at})

    @classmethod
    async def get(cls, id: ObjectId | str):
        if isinstance(id, str):
            id = ObjectId(id)

        request = await db.requests.find_one({"_id": id})
        if not request:
            return None
        
        return cls.from_doc(request)
    
    @classmethod
    async def create(cls, sender: int, team_name: str):
        request = {
            "sender": sender,
            "team_name": team_name,
            "status": RequestStatus.PENDING.value,
            "approval_info": {"by": None, "at": None},
            "created_at": time()
        }
        insert_result = await db.requests.insert_one(request)
        request["_id"] = insert_result.inserted_id
        return cls.from_doc(request)
    
    @classmethod
    def from_doc(cls, data: dict):
        return cls(
            id=data["_id"],
            sender=data["sender"],
            team_name=data["team_name"],
            status=RequestStatus[data["status"].upper()],
            approval_info=data.get("approval_info", {}),
            created_at=data["created_at"]
        )
    
    @property
    def id(self) -> ObjectId:
        return self._id
    
    @property
    def sender(self) -> int:
        return self._sender
    
    @property
    def team_name(self) -> str:
        return self._team_name

    @property
    def status(self) -> RequestStatus:
        return self._status
    
    @property
    def approval_info(self) -> dict:
        return self._approval_info
    
    @property
    def created_at(self) -> float:
        return self._created_at
    

class Reminder:

    def __init__(
            self,
            id: str,
            job_id: str,
            receiver_id: int,
            remind_at: float,
            type: ReminderType,
            created_at: float
        ):
        self._id: str = id
        self._job_id: str = job_id
        self._receiver_id: int = receiver_id
        self._type: ReminderType = type
        self._remind_at: float = remind_at
        self._created_at: float = created_at

    async def reschedule(self, remind_at: datetime, with_job: bool = True):
        self._remind_at = remind_at.timestamp()
        await db.reminders.update_one({"_id": self._id}, {"$set": {"remind_at": self._remind_at}})
        if with_job:
            if job := scheduler.get_job(self._job_id):
                job.reschedule(trigger="date", run_date=remind_at)

    async def delete(self, with_job: bool = False):
        await db.reminders.delete_one({"_id": self._id})
        if with_job:
            if job := scheduler.get_job(self._job_id):
                job.remove()

    @classmethod
    async def create(cls, id: str, job_id: str, receiver_id: int, type: ReminderType, remind_at: float):
        reminder = {
            "_id": id,
            "job_id": job_id,
            "receiver_id": receiver_id,
            "type": type.value,
            "remind_at": remind_at,
            "created_at": time()
        }
        await db.reminders.insert_one(reminder)
        return cls.from_doc(reminder)
    
    @classmethod
    async def get(cls, id: str):
        reminder = await db.reminders.find_one({"_id": id})
        if reminder:
            return cls.from_doc(reminder)
    
    @classmethod
    def from_doc(cls, data: dict):
        return cls(
            id=data["_id"],
            job_id=data["job_id"],
            receiver_id=data["receiver_id"],
            type=ReminderType[data["type"].upper()],
            remind_at=data["remind_at"],
            created_at=data["created_at"]
        )
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def job_id(self) -> str:
        return self._job_id
    
    @property
    def receiver_id(self) -> int:
        return self._receiver_id
    
    @property
    def type(self) -> ReminderType:
        return self._type
    
    @property
    def remind_at(self) -> float:
        return self._remind_at
    
    @property
    def created_at(self) -> float:
        return self._created_at