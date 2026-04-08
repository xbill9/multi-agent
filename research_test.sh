# Use the Google Cloud SDK bundled Python 3.13
PYTHON_CMD=/usr/lib/google-cloud-sdk/platform/bundledpythonunix/bin/python3
if [ ! -f "$PYTHON_CMD" ]; then
  PYTHON_CMD=python3
fi

# This runs the researcher agent in interactive mode
$PYTHON_CMD -m google.adk.cli run agents/researcher
