# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
import os
import sys
import warnings
from pathlib import Path

# Ensure shared directory is in path
sys.path.insert(0, os.path.dirname(__file__))

import click
import uvicorn
from a2a_utils import a2a_card_dispatch
from google.adk.cli import fast_api
from logging_config import get_uvicorn_log_config, setup_logging
from starlette.middleware.base import BaseHTTPMiddleware

# Suppress experimental warnings
warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*", category=UserWarning)
os.environ["ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS"] = "True"

# Ensure shared directory is in path

LOG_LEVELS = click.Choice(
    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    case_sensitive=False,
)


@click.command()
@click.argument(
    "agents_dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    default=os.getcwd(),
)
@click.option("--host", type=str, default="127.0.0.1", show_default=True)
@click.option(
    "--port", type=int, default=int(os.getenv("PORT", 8000)), show_default=True
)
@click.option("--allow_origins", multiple=True)
@click.option("--eval_storage_uri", type=str, default=None)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("--log_level", type=LOG_LEVELS, default="INFO")
@click.option("--trace_to_cloud", is_flag=True, default=False)
@click.option("--otel_to_cloud", is_flag=True, default=False)
@click.option("--session_service_uri", help="URI for session persistence.")
@click.option("--artifact_service_uri", type=str, default=None)
@click.option("--memory_service_uri", type=str, default=None)
@click.option("--with_web_ui", is_flag=True, default=False)
@click.option("--url_prefix", type=str, default=None)
@click.option("--extra_plugins", multiple=True, default=None)
@click.option("--a2a", is_flag=True, default=False, help="Enable A2A endpoints.")
def main(
    agents_dir: str,
    host: str,
    port: int,
    allow_origins: list[str] | None,
    eval_storage_uri: str | None = None,
    verbose: bool = False,
    log_level: str = "INFO",
    trace_to_cloud: bool = False,
    otel_to_cloud: bool = False,
    session_service_uri: str | None = None,
    artifact_service_uri: str | None = None,
    memory_service_uri: str | None = None,
    with_web_ui: bool = False,
    url_prefix: str | None = None,
    extra_plugins: list[str] | None = None,
    a2a: bool = False,
):
    """Starts a FastAPI server for ADK agents."""
    if verbose:
        log_level = "DEBUG"

    # Standardized logging setup
    setup_logging(os.path.basename(agents_dir), log_level)

    files_to_cleanup = []
    folders_to_cleanup = []

    # Determine if we are loading a single agent in the provided directory
    agent_root_py = Path(agents_dir) / "agent.py"
    agent_root_json = Path(agents_dir) / "agent.json"
    
    # We'll pass this info to _prepare_a2a_agent_cards and use it for get_fast_api_app
    effective_agents_dir = agents_dir
    effective_agents = None

    if agent_root_py.exists() or agent_root_json.exists():
        # Point AgentLoader to the parent and load this directory as the agent
        parent_dir = str(Path(agents_dir).parent)
        agent_name = os.path.basename(agents_dir)
        effective_agents_dir = parent_dir
        effective_agents = [agent_name]

    try:
        if a2a:
            _prepare_a2a_agent_cards(agents_dir, files_to_cleanup, folders_to_cleanup, effective_agents)

        app = fast_api.get_fast_api_app(
            agents_dir=effective_agents_dir,
            session_service_uri=session_service_uri,
            artifact_service_uri=artifact_service_uri,
            memory_service_uri=memory_service_uri,
            eval_storage_uri=eval_storage_uri,
            allow_origins=allow_origins,
            web=with_web_ui,
            trace_to_cloud=trace_to_cloud,
            otel_to_cloud=otel_to_cloud,
            a2a=a2a,
            host=host,
            port=port,
            extra_plugins=extra_plugins,
        )

        if a2a:
            app.add_middleware(BaseHTTPMiddleware, dispatch=a2a_card_dispatch)

        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            reload=False,
            log_config=get_uvicorn_log_config(log_level),
        )
        server = uvicorn.Server(config)
        server.run()

    finally:
        # Robust cleanup of temporary agent cards
        for f in files_to_cleanup:
            try:
                Path(f).unlink(missing_ok=True)
            except Exception as e:
                logging.warning(f"Failed to cleanup file {f}: {e}")

        for d in folders_to_cleanup:
            try:
                Path(d).rmdir()
            except Exception as e:
                logging.debug(f"Failed to cleanup folder {d}: {e}")


def _prepare_a2a_agent_cards(
    agents_dir: str, files_to_cleanup: list, folders_to_cleanup: list, effective_agents: list[str] | None = None
):
    """Generates temporary agent.json cards for A2A discovery if they don't exist."""
    from a2a.types import AgentCapabilities
    from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
    from google.adk.apps import App
    from google.adk.cli.utils.agent_loader import AgentLoader

    if effective_agents:
        agents = effective_agents
        # If we have effective agents, it means we are loading them from the parent
        loader = AgentLoader(str(Path(agents_dir).parent))
        agents_dir = str(Path(agents_dir).parent)
    else:
        loader = AgentLoader(agents_dir)
        agents = loader.list_agents() or ["agent"]

    for agent_name in agents:
        agent_path = Path(agents_dir) / agent_name
        if not agent_path.exists():
            agent_path.mkdir(exist_ok=True)
            folders_to_cleanup.append(agent_path)

        card_file = agent_path / "agent.json"
        if not card_file.exists():
            try:
                agent = loader.load_agent(agent_name)
            except Exception as e:
                logging.debug(f"Skipping {agent_name}: not a valid agent directory ({e})")
                continue

            if isinstance(agent, App):
                agent = agent.root_agent

            # Temporary URL for building the card; rewritten by middleware later
            card_builder = AgentCardBuilder(
                agent=agent,
                rpc_url=f"http://127.0.0.1/a2a/{agent_name}",
                capabilities=AgentCapabilities(streaming=True),
            )
            agent_card = asyncio.run(card_builder.build())
            card_file.write_text(agent_card.model_dump_json(indent=2))
            files_to_cleanup.append(card_file)


if __name__ == "__main__":
    main()
