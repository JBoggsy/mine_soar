from argparse import ArgumentParser
from pathlib import Path
from subprocess import Popen
import sys

import pysoarlib as psl

from agent_connector import AgentConnector
from gui import MineSoarGUI


USER_NAME = "boggsj"

#######################
# PARSE CLI ARGUMENTS #
#######################
cli = ArgumentParser(description="Test bed for Soar agents with SVS 2.0 running in the Malmo environment.")
cli.add_argument(
    "-p", "--port", 
    default=9000,
    type=int,
    help="The port to use for Python <-> Malmo communication."
)
cli.add_argument(
    "-a", "--agent", 
    default="soar_agents/agent_gamma.soar",
    type=Path,
    help="The path to the .soar file which should be sourced for the agent."
)
cli.add_argument(
    "-n", "--name",
    default="Steve",
    type=str,
    help="The name for the agent in Minecraft."
)
cli.add_argument(
    "-w", "--watch-level",
    default=1,
    type=int,
    choices=[0, 1, 2, 3, 4 ,5],
    help="The Soar watch level, controls how verbose Soar output is."
)
cli.add_argument(
    "-l", "--launch-minecraft",
    action="store_true",
    help="Flag that indicates the minecraft client should be launched along with the python app."
)
cli_namespace = cli.parse_args()

######################
# CREATE SOAR CLIENT #
######################
agent = psl.SoarClient(agent_name=cli_namespace.name,
                        agent_source=str(cli_namespace.agent),
                        write_to_stdout=True,
                        watch_level=cli_namespace.watch_level)

minecraft_connector = AgentConnector(agent)
minecraft_connector.add_output_command("take-action")
agent.add_connector("minecraft", minecraft_connector)

# state_view_connector = StateViewerConnector(agent)
# agent.add_connector("state_viewer", state_view_connector)

##############
# CREATE GUI #
##############
mine_gui = MineSoarGUI(agent, minecraft_connector, cli_namespace.port)
minecraft_connector.gui = mine_gui
agent.print_handler = mine_gui._soar_output_callback

#######################
# LAUNCH MALMO CLIENT #
#######################
if cli_namespace.launch_minecraft:
    MALMO_ARGS = [f"/home/{USER_NAME}/Coding/malmo/Minecraft/launchClient.sh", "-port", str(cli_namespace.port), "-env"]
    malmo_proc = Popen(MALMO_ARGS, stdout=sys.stdout)

#################
# PROGRAM START #
#################
agent.connect()
mine_gui.mainloop()