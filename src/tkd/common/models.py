from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

EnvMap = Dict[str, str]
JSONPrimitive = Union[str, int, float, bool, None]
JSONValue = Any
JSONObject = Dict[str, JSONValue]
PathList = List[Path]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MutableModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArtifactLayout(FrozenModel):
    mode: str
    path: Optional[str] = None
    suffix: str = ".md"


class AgentLayout(FrozenModel):
    name: str
    config_dir: str
    rules: ArtifactLayout
    commands: ArtifactLayout
    mcp: ArtifactLayout


def _normalize_selection(raw, default_all=False) -> tuple[list[str], bool]:
    if raw is None:
        return [], default_all
    if isinstance(raw, str):
        if raw in {"*", "all"}:
            return [], True
        return [raw], False
    values = list(raw)
    if values == ["*"] or values == ["all"] or "*" in values or "all" in values:
        return [], True
    return values, False


class SourceAuth(FrozenModel):
    type: str
    token: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None


class SourceConfig(FrozenModel):
    name: str
    type: str
    path: Optional[str] = None
    url: Optional[str] = None
    ref: Optional[str] = None
    auth: Optional[SourceAuth] = None


class TargetsConfig(FrozenModel):
    agents: object = Field(default_factory=list)
    root: str = "."


class SelectionConfig(FrozenModel):
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    include_all: bool = False
    source: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, value):
        if isinstance(value, str):
            return {"source": value}
        raw = {} if value is None else dict(value)
        if "include" in raw and "exclude" in raw:
            raise ValueError("include and exclude cannot be used at the same time")
        include, include_all = _normalize_selection(raw.get("include"), default_all=True)
        exclude, _ = _normalize_selection(raw.get("exclude"), default_all=False)
        raw["include"] = include
        raw["exclude"] = exclude
        raw["include_all"] = include_all
        return raw


class NamedSelectionConfig(SelectionConfig):
    enabled: bool = True
    alias: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, value):
        raw = super().normalize(value)
        raw["alias"] = raw.get("as", raw.get("alias"))
        raw.pop("as", None)
        return raw


class CollectionConfig(NamedSelectionConfig):
    pass


class CommandConfig(NamedSelectionConfig):
    pass


class CustomConfig(SelectionConfig):
    enabled: bool = True
    scope: str = "root"
    dest: str = ""


class TkdConfig(FrozenModel):
    targets: TargetsConfig = Field(default_factory=TargetsConfig)
    sources: dict[str, SourceConfig]
    skills: dict[str, CollectionConfig] = Field(default_factory=dict)
    rules: dict[str, CollectionConfig] = Field(default_factory=dict)
    mcp: JSONObject = Field(default_factory=dict)
    commands: dict[str, CommandConfig] = Field(default_factory=dict)
    custom: dict[str, CustomConfig] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, value):
        raw = {} if value is None else dict(value)
        raw["targets"] = raw.get("targets", {})
        raw_sources = raw.get("sources", {})
        if not raw_sources:
            raise ValueError("Config must define at least one source")
        raw["sources"] = {
            name: _coerce_source_value(name=name, value=item) for name, item in raw_sources.items()
        }
        return raw


class SkillArtifact(FrozenModel):
    name: str
    description: str
    path: Path


class RuleArtifact(FrozenModel):
    name: str
    content: str
    path: Path


class MCPArtifact(FrozenModel):
    name: str
    config: JSONObject
    path: Path


class CommandArtifact(FrozenModel):
    name: str
    description: str
    template: str
    path: Path
    metadata: dict[str, object] = Field(default_factory=dict)


class InstallPayload(MutableModel):
    skills: list[SkillArtifact] = Field(default_factory=list)
    rules: list[RuleArtifact] = Field(default_factory=list)
    mcp: list[MCPArtifact] = Field(default_factory=list)
    commands: list[CommandArtifact] = Field(default_factory=list)


class ResolvedSource(FrozenModel):
    config: SourceConfig
    root: Path

    def skill_path(self, name: str) -> Path:
        return self.root / "skills" / name

    def rule_path(self, name: str) -> Path:
        return self.root / "rules" / name

    def mcp_path(self, name: str) -> Path:
        return self.root / "mcp" / name

    def command_path(self, name: str) -> Path:
        return self.root / "commands" / name


class SharedAgentPayload(Protocol):
    skills: list[Any]
    rules: list[Any]
    commands: list[Any]


def _coerce_source_value(name: str, value) -> dict[str, object]:
    if isinstance(value, str):
        if value.startswith("http://") or value.startswith("https://"):
            url, _, ref = value.partition("#")
            return {
                "name": name,
                "type": "git",
                "url": url,
                "ref": ref or None,
            }
        return {
            "name": name,
            "type": "local",
            "path": value,
        }

    raw = dict(value)
    if "path" in raw:
        return {
            "name": name,
            "type": "local",
            "path": raw.get("path"),
        }

    if "url" not in raw:
        raise ValueError("Source {0} must define either path or url".format(name))

    auth = raw.get("auth")
    return {
        "name": name,
        "type": "git",
        "url": raw.get("url"),
        "ref": raw.get("ref"),
        "auth": auth,
    }
