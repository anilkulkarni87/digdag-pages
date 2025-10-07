# Examples

## sample_project
Minimal `.dig` project that demonstrates:
- `schedule` with `cron>`
- `timezone`
- `_export` with `!include` (as a key) to merge `config/environment.yml`
- `td>` task pointing to `queries/foo.sql`
- `_do` nesting, `if>` branch, and `mail>`

### Run
From repo root after `pip install -e .`:
```bash
digdaggraph
# or run only inside examples (outputs still go to repo-level graphs/):
cd examples && digdaggraph
```
Then open `scheduled_workflows.html` and click into `sample_project/workflow.html`.
