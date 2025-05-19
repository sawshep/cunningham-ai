# Cunningham: Open WebUI-Compatible AI Coding Agent

Leverage self-hosted models for programming and system
administration.

![./demo.png]

## Installation

- Download: `git clone https://github.com/sawshep/cunningham-agent`
- Install requirements: `pip install -r requirements.txt`
- Configure environment variables in `.env`:
    - `OPENWEBUI_BASE_URL`
    - `OPENWEBUI_API_KEY`
    - `OPENWEBUI_MODEL`
- Start the agent! `python /main.py` or just `./main.py`
- You can also symlink the executable to your path under a
  different name if you'd like

## Advice

Currently, it only works well with reasoning models. My
model of choice is Qwen3:32b. Use a reasoning model until
non-reasoning models are patched.

A good prompt is the key to success. I have luck with the
included `prompt.txt`. Modify it to your liking.

## Contributing & Issues

Open a Github Issue if you have a problem, or a pull request
if you want to merge a feature.
