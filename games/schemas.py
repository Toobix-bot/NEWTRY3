from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict


Action = Literal[
    "move_up", "move_down", "move_left", "move_right", "wait", "interact"
]


class WorldPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Small, additive, whitelisted world changes
    open_exit: Optional[Dict[str, str]] = Field(
        default=None,
        description='{"from": "Flur", "dir": "ost", "to": "Garten"}',
    )
    add_item: Optional[Dict[str, str]] = Field(
        default=None,
        description='{"at": "Raum", "item": "Notiz"}',
    )
    set_goal: Optional[str] = Field(default=None, description="Kurzes Ziel, z. B. 'Finde die Blume'")


class AvaTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thoughts: str = Field(default="", description="Kurze Innensicht")
    action: Action = Field(default="wait")
    speech: str = Field(default="")
    design_feedback: str = Field(default="")
    self_update: Optional[str] = Field(default=None)
    world_patch: Optional[WorldPatch] = Field(default=None)
