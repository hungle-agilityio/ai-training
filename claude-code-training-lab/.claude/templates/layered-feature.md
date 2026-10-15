# Template: a new feature through the layers

Read `rules/architecture.md` first. Order is test-first; replace the names in `<angle brackets>`.

1. **Test** (`reviews/tests/unit/test_<feature>.py`, `reviews/tests/integration/test_<feature>_view.py`): the rule with exact values, the empty case, and the query count.
2. **Repository** (`reviews/repositories.py`): one function, one query, `select_related` / `prefetch_related`, unique ordering.

```python
def <thing>_for_<scope>(<arg>: <Type>) -> QuerySet[<Model>]:
    """What it returns, in one line."""
    return <Model>.objects.filter(...).select_related(...).order_by("-created_at", "-id")
```

3. **Service** (`reviews/services.py`): the rule, returns frozen dataclasses, no request objects.

```python
@dataclass(frozen=True)
class <Result>:
    ...

def <do_the_rule>(<arg>: <Type>) -> <Result>:
    """The business rule, in one line."""
```

4. **Form** (`reviews/forms.py`): validates every value from the request.
5. **View** (`reviews/views.py`): parse → call service → render. No logic.
6. **Template** (`reviews/templates/`): show the empty case.
7. **Check:** `uv run ruff check . && uv run mypy . && uv run pytest -q --no-cov`.
