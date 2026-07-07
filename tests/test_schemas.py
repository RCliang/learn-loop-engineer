from shared.tools.schemas import ALL_TOOLS, ALL_TOOLS_AS_CALLABLES


def test_all_tools_has_three_schemas():
    assert len(ALL_TOOLS) == 3
    names = {t["name"] for t in ALL_TOOLS}
    assert names == {"bash_exec", "file_read", "file_write"}


def test_each_schema_has_required_fields():
    for t in ALL_TOOLS:
        assert "name" in t
        assert "description" in t
        assert "input_schema" in t
        assert t["input_schema"]["type"] == "object"


def test_callables_match_schemas():
    assert len(ALL_TOOLS_AS_CALLABLES) == 3
    schema_names = {t["name"] for t in ALL_TOOLS}
    callable_names = {t.name for t in ALL_TOOLS_AS_CALLABLES}
    assert schema_names == callable_names


def test_callable_descriptions_match_schemas():
    by_schema = {t["name"]: t["description"] for t in ALL_TOOLS}
    for tool in ALL_TOOLS_AS_CALLABLES:
        assert tool.description == by_schema[tool.name]
