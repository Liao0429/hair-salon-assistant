# 单元测试结果

命令: .venv/Scripts/python.exe -m pytest -q
退出码: 0
通过: 13 | 失败: 0

```
.............                                                            [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\pydantic\_internal\_generate_schema.py:1030
  G:\hair-salon-assistant\.venv\Lib\site-packages\pydantic\_internal\_generate_schema.py:1030: UserWarning: Mixing V1 models and V2 models (or constructs, like `TypeAdapter`) is not supported. Please upgrade `AIMessage` to V2.
    warnings.warn(

.venv\Lib\site-packages\pydantic\_internal\_generate_schema.py:1030
  G:\hair-salon-assistant\.venv\Lib\site-packages\pydantic\_internal\_generate_schema.py:1030: UserWarning: Mixing V1 models and V2 models (or constructs, like `TypeAdapter`) is not supported. Please upgrade `BaseMessage` to V2.
    warnings.warn(

tests/test_output_parser.py::test_parser_format_instructions_include_required_fields
  G:\hair-salon-assistant\.venv\Lib\site-packages\langchain_core\output_parsers\pydantic.py:91: PydanticDeprecatedSince20: The `schema` method is deprecated; use `model_json_schema` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    schema = {k: v for k, v in self.pydantic_object.schema().items()}

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 3 warnings in 2.09s

```
