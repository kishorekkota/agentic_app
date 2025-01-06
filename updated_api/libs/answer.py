from dataclasses import dataclass
from enum import Enum
from typing import List

class InfoType(Enum):
    STATE = "state"
    ZIPCODE = "zipcode"

@dataclass
class Sources:
    reference_id: str
    title: str
    url: str

@dataclass
class Answer:
    question: str
    answer: str
    sources: list
    run_id: str
    thread_id: str
    client_state: str
    client_industry: str
    classification: str = None
    additional_info_needed: bool = False
    info_type: InfoType = None
    sources: List[Sources]
