"""Required-parameter mapping in SkillParameter.from_hydrated_parameter."""
from typing import List

from mcp_server.skill_parameter import SkillParameter


def _param(**overrides):
    base = {
        "key": "metrics",
        "is_hidden": False,
        "is_multi": False,
        "is_required": False,
        "metadata_field": None,
        "llm_description": "the metric",
        "description": "the metric",
        "constrained_values": None,
    }
    base.update(overrides)
    return base


def test_required_true_is_reflected():
    p = SkillParameter.from_hydrated_parameter(_param(is_required=True))
    assert p is not None
    assert p.required is True


def test_required_false():
    p = SkillParameter.from_hydrated_parameter(_param(is_required=False))
    assert p.required is False


def test_required_missing_defaults_false():
    d = _param()
    del d["is_required"]
    p = SkillParameter.from_hydrated_parameter(d)
    assert p.required is False


def test_hidden_param_skipped():
    assert SkillParameter.from_hydrated_parameter(_param(is_hidden=True)) is None


def test_multi_param_type_hint():
    p = SkillParameter.from_hydrated_parameter(_param(is_multi=True))
    assert p.type_hint == List[str]


def test_constrained_values_stringified():
    p = SkillParameter.from_hydrated_parameter(_param(constrained_values=[1, 2, 3]))
    assert p.constrained_values == ["1", "2", "3"]
