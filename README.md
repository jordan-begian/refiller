# Refiller 💊

An automated medication refill request service.

## Overview

Refiller automates the process of requesting medication refills by logging into a healthcare provider's portal and submitting refill request.<br>
This service will be ran as a scheduled job to prevent missing a refill request.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (python package manager)

## Setup

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Create your config file**

   Create a `config.toml` file with the following values:
   ```toml
   username = "your_username"
   password = "your_password"
   office = "your_office_id"
   base_url = "https://your-provider-portal.com"
   med_id = "your_medication_id"
   ```

## Usage

Run the refiller service:

```bash
CONFIG_PATH="~/path/to/config.toml" uv run main.py
```

## Testing & Linting

### Test

```bash
uv run pytest
```

### Lint

```bash
uv run ruff check --fix
```

## Project Structure

```
refiller/
├── main.py                  # Entry point
├── config.toml              # Configuration template
├── src/
│   ├── config.py           # Configuration loader
│   └── refiller_client.py  # HTTP client for refill requests
└── tests/                  # Unit tests
```
