# LLM Eval Studio

A local evaluation workbench that versions datasets and prompts, compares prompt outputs, records failures and latency, estimates token costs, exports JSON, and fails CI when quality falls below a threshold. Built with FastAPI and SQLite.

## Run

Requires Python 3.11+.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn studio.api:app --host 127.0.0.1 --port 8002
```

Open http://127.0.0.1:8002. Save the sample dataset. Save prompts named `baseline` and `concise`, select both, and run with **Recorded outputs**. The sample yields a 50% exact-match rate for baseline and 100% for concise. These are saved fixture outputs, not generated model results. `/docs` provides API documentation.

## Live providers

- **Bedrock:** install `boto3`, set `AWS_REGION` and `BEDROCK_MODEL_ID`, and configure AWS credentials through the provider chain. The role needs model access and `bedrock:InvokeModel`. The model must support Converse.
- **OpenAI-compatible HTTP:** set `LLM_BASE_URL` to an API base such as `http://localhost:11434/v1`, `LLM_MODEL`, and optionally `LLM_API_KEY`. The adapter calls `/chat/completions`; endpoint support for temperature/max_tokens is required.

Export environment variables in your shell before starting the server. `.env.example` is a reference; the app does not automatically load it. Live providers send the rendered input/template to the configured endpoint, use temperature 0 and a 512-token output limit, and have a 25-second per-case read timeout. Supply input/output prices per million tokens in the form. Costs are estimates based on returned token usage, and remain unavailable if usage is missing. Replay does not manufacture token counts or cost estimates.

## Dataset and assertions

`examples/dataset.json` contains cases with unique IDs, inputs, and either `expected` text or nonempty `contains` assertions. Exact match trims leading/trailing whitespace but remains case sensitive. If both kinds are supplied, all assertions must pass. A provider error is a failed case. These checks measure deterministic expectations; they do not establish factuality, safety, or overall response quality.

Replay selects `case.outputs[prompt.name]`. Prompt versions with the same name use the same recorded output; use separate names to compare distinct recorded candidates. Replay latency measures local evaluation overhead, not model speed.

## CLI and CI

```sh
python -m studio.cli examples/dataset.json examples/prompt.json --min-pass-rate 1
python -m studio.cli dataset.json prompt.json --provider bedrock --min-pass-rate .9 --output report.json
```

Prompt files contain `{name,version,template}` with an `{input}` placeholder. Exit 0 for passing threshold, 1 for regression/provider errors, 2 for malformed input. The included concise replay sample passes at 100%.

## Tests

```sh
python -m unittest discover -s tests -v
```

Seven tests passed, including the full save-dataset/save-prompt/queue-batch/result retrieval flow through FastAPI TestClient, scoring, error handling, versioning, and token-cost arithmetic. The browser JavaScript passed syntax validation. Live model calls and browser interactions were not verified in the managed environment.

## Storage and limits

Immutable artifacts and run snapshots persist in `data/evals.sqlite` (override with `EVAL_DB`). Each saved run includes dataset and prompt versions. Batches run in the server process, one at a time, with 1–50 cases and 1–3 prompt versions. Only the most recent 100 runs appear in history. Requests are limited to 1 MB. A server restart interrupts active batches; interrupted runs are marked failed at the next startup. This is a single-worker local MVP without authentication or a durable task queue. Keep it on loopback; outputs may contain sensitive information.

MIT licensed.
