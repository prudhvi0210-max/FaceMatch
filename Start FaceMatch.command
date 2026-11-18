#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if [[ -n "$FACEMATCH_PYTHON" ]]; then
  runtime="$FACEMATCH_PYTHON"
elif [[ -x "$HOME/.venvs/facematch-university/bin/python" ]]; then
  runtime="$HOME/.venvs/facematch-university/bin/python"
else
  runtime="$PWD/.venv/bin/python"
fi
if [[ ! -x "$runtime" ]]; then
  echo "Create the Python 3.11 environment using the commands in README.md."
  read -r "reply?Press Enter to close."
  exit 1
fi
exec "$runtime" -B app/ui.py
