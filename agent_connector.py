import base64
from multiprocessing.sharedctypes import Value

import cv2

import pysoarlib as psl
import Python_sml_ClientInterface as sml


class AgentConnector(psl.AgentConnector):
    def __init__(self, agent: psl.SoarClient):
        super().__init__(agent)
        self.agent = agent
        self.gui = None
        self.agent.execute_command("svs --enable")

        self.first_input = True

        self.new_vision_update = False
        self.vision_update_num = 0
        self.new_vision_update_wme = psl.SoarWME("vision-update", self.vision_update_num)

        self.time_alive = 0
        self.time_alive_wme = psl.SoarWME("time-alive", self.time_alive)

        self.x_pos = 0.0
        self.x_pos_wme = psl.SoarWME("x-pos", self.x_pos)
        
        self.y_pos = 0.0
        self.y_pos_wme = psl.SoarWME("y-pos", self.y_pos)
        
        self.z_pos = 0.0
        self.z_pos_wme = psl.SoarWME("z-pos", self.z_pos)
        
        self.pitch = 0.0
        self.pitch_wme = psl.SoarWME("pitch", self.pitch)
        
        self.yaw = 0.0
        self.yaw_wme = psl.SoarWME("yaw", self.yaw)
        
        self.world_time = 0
        self.world_time_wme = psl.SoarWME("world-time", self.world_time)

    def send_vision(self, visual):
        success, data = cv2.imencode('.png', visual)
        obs_data_b64 = base64.b64encode(data).decode()
        inject_cmd_str = f"svs vsm.inject {obs_data_b64}"
        self.agent.execute_command(inject_cmd_str)
        self.new_vision_update = True
        self.vision_update_num += 1

    def update_info(self, info_dict):
        self.time_alive = info_dict["TimeAlive"]
        self.x_pos = info_dict["XPos"]
        self.y_pos = info_dict["YPos"]
        self.z_pos = info_dict["ZPos"]
        self.pitch = info_dict["Pitch"]
        self.yaw = info_dict["Yaw"]
        self.world_time = info_dict["WorldTime"]

    def on_input_phase(self, input_link):
        if self.new_vision_update:
            self.new_vision_update_wme.set_value(self.vision_update_num)
            self.new_vision_update_wme.update_wm(input_link)
            self.new_vision_update = False

        self.time_alive_wme.set_value(self.time_alive)
        self.time_alive_wme.update_wm(input_link)
        
        self.x_pos_wme.set_value(self.x_pos)
        self.x_pos_wme.update_wm(input_link)

        self.y_pos_wme.set_value(self.y_pos)
        self.y_pos_wme.update_wm(input_link)

        self.z_pos_wme.set_value(self.z_pos)
        self.z_pos_wme.update_wm(input_link)

        self.pitch_wme.set_value(self.pitch)
        self.pitch_wme.update_wm(input_link)

        self.yaw_wme.set_value(self.yaw)
        self.yaw_wme.update_wm(input_link)

        self.world_time_wme.set_value(self.world_time)
        self.world_time_wme.update_wm(input_link)

        state_text = self.agent.execute_command("p s1 -d 6", False)
        vog_text = self.agent.execute_command("p v6 -d 4", False)
        self.gui._soar_state_viewer_callback(state_text, vog_text)

    def on_output_event(self, command_name, root_id):
        print(f"output event: {command_name}")
        if command_name == "take-action":
            action_str = root_id.GetParameterValue("action-str")
            print(f"\taction string: {action_str}")
        if self.gui is not None:
            self.gui.perform_action(action_str)
            root_id.AddStatusComplete()
        return super().on_output_event(command_name, root_id)