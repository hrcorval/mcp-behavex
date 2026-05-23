# mcp-behavex

MCP server for [BehaveX](https://github.com/hrcorval/behavex) — lets AI agents run BDD tests and inspect feature files without using the CLI.

## Installation

```bash
pip install mcp-behavex
```

Requires Python 3.9+ and BehaveX 4.7.0+.

## Tools

### `run_tests`

Runs BehaveX tests and returns a structured result.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `paths` | `list[str]` | Feature file or directory paths. Defaults to `BEHAVEX_FEATURES_PATH`. |
| `tags` | `list[str]` | Tag filters — AND logic between entries, OR within an entry. |
| `parallel_processes` | `int` | Number of parallel workers. |
| `parallel_scheme` | `str` | `'scenario'` or `'feature'`. |
| `output_folder` | `str` | Output directory for reports. Defaults to `BEHAVEX_OUTPUT_FOLDER`. |
| `no_report` | `bool` | Skip all file output. Faster for pass/fail-only use cases. |
| `dry_run` | `bool` | List scenarios without executing steps. |
| `stop` | `bool` | Stop after the first failure. |

**Returns:** `{run_id, exit_code, passed, summary, failed_scenarios, output_folder}`

### `list_features`

Scans feature files and returns their structure without running anything.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `paths` | `list[str]` | Paths to scan. Defaults to `BEHAVEX_FEATURES_PATH`. |
| `tags` | `list[str]` | Filter to features/scenarios with these tags. |

**Returns:** `{features, total_features, total_scenarios}`

## Configuration

| Environment variable | Description |
|---|---|
| `BEHAVEX_FEATURES_PATH` | Default feature paths (comma-separated). |
| `BEHAVEX_OUTPUT_FOLDER` | Default output folder for reports. |

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "behavex": {
      "command": "mcp-behavex",
      "env": {
        "BEHAVEX_FEATURES_PATH": "/path/to/your/tests/features",
        "BEHAVEX_OUTPUT_FOLDER": "/path/to/your/output"
      }
    }
  }
}
```
