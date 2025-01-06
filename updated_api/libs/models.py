import os
import sys
import logging
import json

from typing import Dict, TypedDict, Optional, List, Annotated
from pydantic import BaseModel, Field



class GraphState(TypedDict):
    question: Optional[str] = None
    client_id: Optional[str] = None
    classification: Optional[str] = None
    client_state: Optional[str] = None
    client_name: Optional[str] = None
    client_industry: Optional[str] = None
    job_title: Optional[str] = None
    response: Optional[str] = None
    human_ask: Optional[str] = None
    human_input: Optional[str] = None
    source_title: Optional[List[str]] = None
    source_metadata_id: Optional[List[str]] = None
    source_url: Optional[List[str]] = None

class User_Input(BaseModel):
    """Valid United States state name and industry name"""
    state: str = Field(description="US State name")
    industry: str = Field(description="Industry name")