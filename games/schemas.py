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
    # Creative shaping (still small and guarded)
    create_place: Optional[Dict[str, str]] = Field(
        default=None,
        description='{"name": "Werkstatt", "connect_from": "Flur", "dir": "nord"}',
    )
    create_item: Optional[Dict[str, str]] = Field(
        default=None,
        description='{"at": "Werkstatt", "item": "Skizzenbuch"}',
    )
    set_trait: Optional[Dict[str, str]] = Field(
        default=None,
        description='{"target": "ava|Raum|world", "key": "stimmung", "value": "hoffnungsvoll"}',
    )
    modify_rule: Optional[str] = Field(default=None, description="Kleine Regelidee als Notiz für den Designer")


class AvaTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thoughts: str = Field(default="", description="Kurze Innensicht")
    action: Action = Field(default="wait")
    speech: str = Field(default="")
    design_feedback: str = Field(default="")
    self_update: Optional[str] = Field(default=None)
    world_patch: Optional[WorldPatch] = Field(default=None)
    # Perception & Memory
    perceptions: Optional[str] = Field(default=None, description="Was nehme ich wahr?")
    experience: Optional[str] = Field(default=None, description="Was habe ich erlebt?")
    insights: Optional[str] = Field(default=None, description="Welche Erkenntnis habe ich gewonnen?")
    conclusions: Optional[str] = Field(default=None, description="Welchen Schluss ziehe ich?")
    wishes: Optional[str] = Field(default=None, description="Was wünsche ich mir?")
    fears: Optional[str] = Field(default=None, description="Was fürchte ich?")
    # Expressive shaping intents (documented; actual effect via world_patch)
    self_shape: Optional[str] = Field(default=None, description="Wie forme/verändere ich mich?")
    world_shape: Optional[str] = Field(default=None, description="Was möchte ich erschaffen/verändern?")
