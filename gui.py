from calendar import c
from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as tkfd

import malmoenv
import numpy as np
import cv2

import pysoarlib as psl

from agent_connector import AgentConnector, StateViewerConnector
from consts import *
from vog_parser import VOG

OBSERVATION_SHAPE = (480, 640, 4)

true = True
false = False

class MineSoarGUI(tk.Tk):
    def __init__(self, agent: psl.SoarClient, connector: AgentConnector, state_viewer_connector: StateViewerConnector, port):
        super().__init__()
        self.title = "Minecraft Soar Testing Platform"

        self.agent = agent
        self.connector = connector
        self.state_viewer_connector = state_viewer_connector

        self.env = malmoenv.make()

        self.mission_file = None
        self.mission_port = port
        self.episodes_num = 1
        self.ep_max_steps = 0
        self.save_img_steps = 0

        self.mission_commands = None
        self.current_step = 0
        self.current_episode = 0
        self.current_observation = None

        self.mission_file_text_var = tk.StringVar()
        self.mission_port_text_var = tk.StringVar(value=self.mission_port)
        self.mission_num_eps_text_var = tk.StringVar(value=self.episodes_num)
        self.mission_max_steps_text_var = tk.StringVar(value=self.ep_max_steps)
        self.mission_save_img_steps_text_var = tk.StringVar(value=self.save_img_steps)
        self.current_step_text_var = tk.StringVar(value=self.current_step)
        self.current_episode_text_var = tk.StringVar(value=self.current_episode)
        self.action_select_text_var = tk.StringVar(value=0)

        self.soar_user_input_var = tk.StringVar()
        self.vog = VOG()

        self.make_mission_control_widgets()
        self.make_soar_control_widgets()

    def make_mission_control_widgets(self):
        self.mission_control_frame = ttk.Frame(self)
        
        self.mission_select_label = ttk.Label(self.mission_control_frame, text="Selct Mission XML:", justify='right')
        self.mission_select_button = ttk.Button(self.mission_control_frame, text="Open File", command=self._select_mission_file)
        self.current_mission_label = ttk.Label(self.mission_control_frame, textvariable=self.mission_file_text_var)
       
        self.mission_port_label = ttk.Label(self.mission_control_frame, text="Port:", justify='right')
        self.mission_port_entry = ttk.Entry(self.mission_control_frame, textvariable=self.mission_port_text_var)
       
        self.mission_num_eps_label = ttk.Label(self.mission_control_frame, text="# of Episodes:", justify='right')
        self.mission_num_eps_entry = ttk.Entry(self.mission_control_frame, textvariable=self.mission_num_eps_text_var)
       
        self.mission_max_steps_label = ttk.Label(self.mission_control_frame, text="Max # of Steps:", justify='right')
        self.mission_max_steps_entry = ttk.Entry(self.mission_control_frame, textvariable=self.mission_max_steps_text_var)
       
        self.mission_save_img_steps_label = ttk.Label(self.mission_control_frame, text="Save Image # of Steps:", justify='right')
        self.mission_save_img_steps_entry = ttk.Entry(self.mission_control_frame, textvariable=self.mission_save_img_steps_text_var)
       
        self.mission_current_step_label = ttk.Label(self.mission_control_frame, textvariable=self.current_step_text_var)
        self.mission_current_ep_label = ttk.Label(self.mission_control_frame, textvariable=self.current_episode_text_var)
       
        self.mission_init_button = ttk.Button(self.mission_control_frame, text="Initialize Mission", command=self._init_mission)
        self.mission_start_button = ttk.Button(self.mission_control_frame, text="Start Mission", command=self._start_mission)
        self.mission_reset_button = ttk.Button(self.mission_control_frame, text="Reset Mission", command=self._reset_mission)
        self.mission_stop_button = ttk.Button(self.mission_control_frame, text="Stop Mission", command=self._stop_mission)

        self.mission_choose_action_dropdown = ttk.Combobox(self.mission_control_frame, textvariable=self.action_select_text_var)
        self.mission_choose_action_button = ttk.Button(self.mission_control_frame, text="Act", command=self._mission_do_action)

       
        self.mission_control_frame.grid(column=0, row=0, sticky=tk.NSEW)
        
        self.mission_select_label.grid(column=0, columnspan=2, row=0)
        self.mission_select_button.grid(column=2, row=0)
        self.current_mission_label.grid(column=0, columnspan=3, row=1)

        self.mission_port_label.grid(column=0, columnspan=2, row=2)
        self.mission_port_entry.grid(column=2, row=2)

        self.mission_num_eps_label.grid(column=0, columnspan=2, row=3)
        self.mission_num_eps_entry.grid(column=2, row=3)

        self.mission_max_steps_label.grid(column=0, columnspan=2, row=4)
        self.mission_max_steps_entry.grid(column=2, row=4)

        self.mission_save_img_steps_label.grid(column=0, columnspan=2, row=5)
        self.mission_save_img_steps_entry.grid(column=2, row=5)

        self.mission_current_step_label.grid(column=0, columnspan=2, row=6)
        self.mission_current_ep_label.grid(column=2, row=6)

        self.mission_init_button.grid(column=0, row=7)
        self.mission_start_button.grid(column=1, row=7)
        self.mission_reset_button.grid(column=0, row=8)
        self.mission_stop_button.grid(column=1, row=8)
        
        self.mission_choose_action_dropdown.grid(column=0, columnspan=2, row=9)
        self.mission_choose_action_button.grid(column=2, row=9)

    def _select_mission_file(self):
        file_types = (('xml files', '*.xml'),)
        self.mission_file = Path(tkfd.askopenfilename(title="Select mission file", filetypes=file_types))
        self.mission_file_text_var.set(f"Selected: {self.mission_file}")

    def _init_mission(self):
        self.mission_port = int(self.mission_port_text_var.get())
        self.episodes_num = int(self.mission_num_eps_text_var.get())
        self.ep_max_steps = int(self.mission_max_steps_text_var.get())
        self.save_img_steps = int(self.mission_save_img_steps_text_var.get())
        self.env.init(xml=self.mission_file.read_text(),
                      server=None,
                      port=self.mission_port,
                      action_filter={})
        self.mission_commands = [cmd for cmd in self.env.action_space]
        self.mission_choose_action_dropdown['values'] = self.mission_commands
        self.mission_choose_action_dropdown.state(["readonly"])
        self.mission_choose_action_dropdown.set(self.mission_commands[0])
        self.env.reset()

    def _mission_do_action(self):
        action_str = self.action_select_text_var.get()
        self.perform_action(action_str=action_str)

    def _start_mission(self):
        raise NotImplementedError()

    def _reset_mission(self):
        self.update_observation(self.env.reset())

    def _stop_mission(self):
        raise NotImplementedError()

    def make_soar_control_widgets(self):
        self.soar_control_frame = ttk.Frame(self)

        self.soar_output_frame = ttk.Frame(self.soar_control_frame)
        self.soar_output_text = tk.Text(self.soar_output_frame, width=100, height=100)
        self.soar_output_scrollbar = ttk.Scrollbar(self.soar_output_frame, 
                                                   orient=tk.VERTICAL,
                                                   command=self.soar_output_text.yview)
        self.soar_output_text.configure(yscrollcommand=self.soar_output_scrollbar.set)
        
        self.soar_input_frame = ttk.Frame(self.soar_control_frame)
        self.soar_input_entry = ttk.Entry(self.soar_input_frame, textvariable=self.soar_user_input_var)
        self.soar_input_send_button = ttk.Button(self.soar_input_frame, text="Send", command=self._soar_input_send_callback)
        self.soar_input_step_button = ttk.Button(self.soar_input_frame, text="Step", command=self._soar_input_step_callback)
        self.soar_input_print_state_button = ttk.Button(self.soar_input_frame, text="State", command=self._soar_input_print_state_callback)

        self.soar_viewer_frame = ttk.Frame(self.soar_control_frame)
        self.soar_state_viewer_text = tk.Text(self.soar_viewer_frame, width=80, height=50)
        self.soar_vog_viewer_text = tk.Text(self.soar_viewer_frame, width=80, height=50)

        # Place frame and widgets in grid
        self.soar_control_frame.grid(column=1, row=0, sticky=tk.NSEW)
        self.soar_output_frame.grid(column=0, row=0, sticky=tk.NSEW)
        self.soar_output_text.grid(column=0, row=0, stick=tk.NSEW)
        self.soar_output_scrollbar.grid(column=1, row=0, sticky=tk.NSEW)

        self.soar_input_frame.grid(column=0, row=1, sticky=tk.NSEW)
        self.soar_input_entry.grid(column=0, row=0, sticky=tk.NSEW)
        self.soar_input_send_button.grid(column=1, row=0, sticky=tk.NSEW)
        self.soar_input_step_button.grid(column=2, row=0, sticky=tk.NSEW)
        self.soar_input_print_state_button.grid(column=3, row=0, sticky=tk.NSEW)
        
        self.soar_viewer_frame.grid(column=1, row=0, sticky=tk.NSEW)
        self.soar_state_viewer_text.grid(column=0, row=0, stick=tk.NSEW)
        self.soar_vog_viewer_text.grid(column=0, row=1, sticky=tk.NSEW)

    def _soar_input_send_callback(self):
        self.agent.execute_command(self.soar_user_input_var.get(), True)

    def _soar_input_step_callback(self):
        self.agent.execute_command("step", True)
    
    def _soar_input_print_state_callback(self):
        self.agent.execute_command(PRINT_STATE_COMMAND, True)

    def _soar_output_callback(self, text):
        self.soar_output_text.insert(tk.END, text)
        self.soar_output_text.insert(tk.END, "\n")
        print(text)

    def _soar_state_viewer_callback(self, state_text, vog_text):
        self.soar_state_viewer_text.delete(1.0, tk.END)
        self.soar_state_viewer_text.insert(tk.END, state_text)
        self.soar_state_viewer_text.insert(tk.END, "\n")

        self.vog.parse_vog_text(vog_text)
        self.soar_vog_viewer_text.delete(1.0, tk.END)
        self.soar_vog_viewer_text.insert(tk.END, str(self.vog))
        self.soar_vog_viewer_text.insert(tk.END, "\n")

    def perform_action(self, action_str):
        action_idx = self.mission_commands.index(action_str)
        obs, reward, done, info = self.env.step(action_idx)
        print(info)
        self.connector.update_info(eval(info))
        self.update_observation(obs)

    def update_observation(self, observation:np.ndarray, info=None):
        self.current_observation = observation.reshape(OBSERVATION_SHAPE)
        observation_bgr = cv2.cvtColor(self.current_observation, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite("./observation_raw.png", observation_bgr)
        self.connector.send_vision(observation_bgr)