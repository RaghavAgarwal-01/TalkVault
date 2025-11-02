from typing import Union, List, Optional
from pydantic import BaseModel

class MeetingCreate(BaseModel):
    title: str
    datetime: str
    duration: Optional[int] = 0
    participants: Union[int, str, List[str], None] = 0
    summary: Optional[str] = ""

class MeetingOut(MeetingCreate):
    id: str
    is_done: bool = False
