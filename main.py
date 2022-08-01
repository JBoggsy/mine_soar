from subprocess import Popen
import sys

import pysoarlib as psl

from agent_connector import AgentConnector, StateViewerConnector
from gui import MineSoarGUI

MALMO_PORT = 9001
USER_NAME = "boggsj"
MALMO_ARGS = [f"/home/{USER_NAME}/Coding/malmo/Minecraft/launchClient.sh", "-port", str(MALMO_PORT), "-env"]

if __name__ == "__main__":

    agent = psl.SoarClient(agent_name="Steve",
                           agent_source="/home/boggsj/Coding/research/mine_soar/atari_agents/agent_1/agent_1.soar",
                           write_to_stdout=True,
                           watch_level=1)

    minecraft_connector = AgentConnector(agent)
    minecraft_connector.add_output_command("take-action")
    agent.add_connector("minecraft", minecraft_connector)

    state_view_connector = StateViewerConnector(agent)
    agent.add_connector("state_viewer", state_view_connector)

    malmo_proc = Popen(MALMO_ARGS, stdout=sys.stdout)
    
    mine_gui = MineSoarGUI(agent, minecraft_connector, state_view_connector, MALMO_PORT)
    minecraft_connector.gui = mine_gui
    state_view_connector.gui = mine_gui
    agent.print_handler = mine_gui._soar_output_callback
    
    agent.connect()
    mine_gui.mainloop()