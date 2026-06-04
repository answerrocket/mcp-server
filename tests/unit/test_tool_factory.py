"""Tool generation: required params get no default; annotations reflect scheduling-only."""
import inspect

from mcp_server.skill_parameter import SkillParameter, HydratedSkillConfig
from mcp_server.utils import ToolFactory


def _config(scheduling_only=False):
    return HydratedSkillConfig(
        copilot_skill_id="csid",
        name="Trend Analysis",
        tool_description="trend",
        detailed_description="trend detailed",
        tool_name="trend_analysis",
        scheduling_only=scheduling_only,
        dataset_id=None,
        parameters=[
            SkillParameter(
                name="metrics", type_hint=list, description="metrics",
                required=True, is_multi=True, metadata_field=None, constrained_values=None,
            ),
            SkillParameter(
                name="growth_type", type_hint=str, description="growth",
                required=False, is_multi=False, metadata_field=None, constrained_values=["Y/Y", "P/P"],
            ),
        ],
    )


def test_required_param_has_no_default_optional_has_none():
    fn = ToolFactory.create_skill_tool_function(_config(), "http://x", "tok", "cop")
    sig = inspect.signature(fn)
    assert sig.parameters["metrics"].default is inspect.Parameter.empty   # required
    assert sig.parameters["growth_type"].default is None                  # optional
    assert sig.parameters["context"].kind == inspect.Parameter.KEYWORD_ONLY


def test_annotations_read_only_for_non_scheduling():
    ann = ToolFactory.create_tool_annotations(_config(scheduling_only=False))
    assert ann.readOnlyHint is True
    ann2 = ToolFactory.create_tool_annotations(_config(scheduling_only=True))
    assert ann2.readOnlyHint is False
