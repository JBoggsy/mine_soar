import json
from pathlib import Path
import re
from subprocess import Popen
import sys

import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import filedialog as tkfd

import malmoenv
import numpy as np
import cv2

import pysoarlib as psl

from agent_connector import AgentConnector, StateViewerConnector
from soar_state import SoarState
from vog_parser import VOG


OBSERVATION_SHAPE = (480, 640, 4)
NODE_PATTERN = re.compile("\((\w\d+)(([ \n]+\^([!-~]+)[ \n]+([!-~ ]+))*)\)")
ATTRIBUTE_PATTERN = re.compile("\^([\w\d\-_]+)\s+([\w\d\-_*.]+|\|.*\|)")



class MineSoarGUI(tk.Tk):
    def __init__(self, agent: psl.SoarClient, connector: AgentConnector, state_viewer_connector: StateViewerConnector, port):
        super().__init__()
        self.title = "Minecraft Soar Testing Platform"

        self.agent = agent
        self.connector = connector
        self.state_viewer_connector = state_viewer_connector

        self.env = malmoenv.make()
        self.current_observation = None

        self.mission_file = None
        self.mission_port = port
        self.mission_file_text_var = tk.StringVar(value="No Mission Selected")
        self.mission_port_text_var = tk.StringVar(value=self.mission_port)

        self.mission_commands = None
        self.action_select_text_var = tk.StringVar(value=0)

        self.production_list = []
        self.production_match_entry_text_var = tk.StringVar()
        self.production_match_select_list_var = tk.StringVar()
        self.source_file_text_var = tk.StringVar()
        self.soar_user_input_var = tk.StringVar()
        self.soar_state = SoarState()
        self.vog = VOG()

        self.default_font = font.nametofont("TkFixedFont")
        self.bold_font = self.default_font.copy()
        self.bold_font.configure(weight="bold")
        self.italic_font = self.default_font.copy()
        self.italic_font.configure(slant="italic")

        self.soar_output_highlight_tag = "output-white"

        self.make_soar_control_widgets()
        self.make_mission_control_widgets()
        self.make_soar_output_widgets()
        # self.make_vog_visual_widget()

        self._load_production_list()


    #############################
    # SOAR CONTROL GUI ELEMENTS #
    #############################

    def make_soar_control_widgets(self):
        # CREATE UI ELEMENT OBJECTS
        ###########################
        self.soar_control_frame = ttk.Frame(self, relief="groove", borderwidth=5)
        self.soar_control_panel_label = ttk.Label(self.soar_control_frame, text="Soar Control Frame", anchor=tk.CENTER)

        self.soar_control_panel_separator_0 =ttk.Separator(self.soar_control_frame, orient=tk.HORIZONTAL)
        self.soar_control_panel_separator_1 =ttk.Separator(self.soar_control_frame, orient=tk.HORIZONTAL)
        self.soar_control_panel_separator_2 =ttk.Separator(self.soar_control_frame, orient=tk.HORIZONTAL)
        self.soar_control_panel_separator_3 =ttk.Separator(self.soar_control_frame, orient=tk.HORIZONTAL)
        self.soar_control_panel_separator_4 =ttk.Separator(self.soar_control_frame, orient=tk.HORIZONTAL)
        
        self.run_button         = ttk.Button(self.soar_control_frame,  text="Run", command=self._soar_run_callback, width=3)
        self.step_button        = ttk.Button(self.soar_control_frame, text="Step 1", command=self._soar_step_callback, width=6)
        self.step_5_button      = ttk.Button(self.soar_control_frame, text="5",  command=lambda: self._soar_step_callback(5), width=1)
        self.step_10_button     = ttk.Button(self.soar_control_frame, text="10", command=lambda: self._soar_step_callback(10), width=2)
        self.phase_step_button  = ttk.Button(self.soar_control_frame, text="Next Phase", command=self._soar_phase_step_callback, width=10)

        self.print_s1_button    = ttk.Button(self.soar_control_frame, text="Print S1", command=self._print_state_callback, width=8)
        self.print_SVS_button   = ttk.Button(self.soar_control_frame, text="Print SVS", command=lambda: self._print_state_callback("V1 -d 4"), width=9)
        self.print_VOG_button   = ttk.Button(self.soar_control_frame, text="Print VOG", command=lambda: self._print_state_callback("V6 -d 3"), width=9)
        self.print_IO_link      = ttk.Button(self.soar_control_frame, text="Print IO", command=lambda: self._print_state_callback("I1 -d 4"), width=8)

        self.print_all_matches_button   = ttk.Button(self.soar_control_frame, text="All Matches", command=self._print_all_matches_callback, width=11)
        self.print_prod_matches_button  = ttk.Button(self.soar_control_frame, text="Prod. Matches", command=self._print_prod_matches_callback, width=13)
        self.single_production_entry    = ttk.Entry(self.soar_control_frame, textvariable=self.production_match_entry_text_var, width=25)
        self.single_production_list     = tk.Listbox(self.soar_control_frame, self.production_list, height=6, width=50)
        
        self.reinit_soar_button = ttk.Button(self.soar_control_frame, text="Re-Init", command=self._reinit_soar_callback, width=7)
        self.excise_all_button  = ttk.Button(self.soar_control_frame, text="Excise All", command=self._excise_all_command_callback, width=10)
        self.reset_soar_button  = ttk.Button(self.soar_control_frame, text="Reset Soar", command=self._reset_soar_callback, width=10)
        self.source_file_button = ttk.Button(self.soar_control_frame, text="Source", command=self._source_soar_file_callback, width=6)
        self.source_file_entry  = ttk.Entry(self.soar_control_frame, textvariable=self.source_file_text_var)
        
        self.soar_input_entry = ttk.Entry(self.soar_control_frame, textvariable=self.soar_user_input_var)
        self.soar_input_send_button = ttk.Button(self.soar_control_frame, text="Send", command=self._soar_send_callback, width=4)
        
        # GRID UI ELEMENTS
        ##################
        num_columns = 6
        for col_i in range(num_columns):
            self.soar_control_frame.columnconfigure(col_i, weight=1, uniform="soar")

        self.soar_control_frame.grid(column=0, row=0, sticky=tk.N+tk.EW)
        self.soar_control_panel_label.grid(column=0, columnspan=num_columns, row=0, sticky=tk.NSEW, pady=5)
        self.soar_control_panel_separator_0.grid(column=0, columnspan=num_columns, row=1, sticky=tk.NSEW, pady=5)

        run_row = 2
        self.run_button.grid(column=0, columnspan=2, row=run_row, rowspan=2, sticky=tk.NSEW)
        self.step_button.grid(column=2, columnspan=2, row=run_row, rowspan=1, sticky=tk.NSEW)
        self.phase_step_button.grid(column=4, columnspan=2, row=run_row, rowspan=2, sticky=tk.NSEW)
        self.step_5_button.grid(column=2, row=run_row+1, sticky=tk.NSEW)
        self.step_10_button.grid(column=3, row=run_row+1, sticky=tk.NSEW)

        self.soar_control_panel_separator_1.grid(column=0, columnspan=num_columns, row=run_row+2, sticky=tk.NSEW, pady=5)

        print_row = run_row + 3
        self.print_s1_button.grid(column=0, columnspan=3, row=print_row, sticky=tk.NSEW)
        self.print_SVS_button.grid(column=0, columnspan=3, row=print_row+1, sticky=tk.NSEW)
        self.print_VOG_button.grid(column=3, columnspan=3, row=print_row, sticky=tk.NSEW)
        self.print_IO_link.grid(column=3, columnspan=3, row=print_row+1, sticky=tk.NSEW)

        self.soar_control_panel_separator_2.grid(column=0, columnspan=num_columns, row=print_row+2, sticky=tk.NSEW, pady=5)

        matches_row = print_row+3
        self.print_all_matches_button.grid(column=0, columnspan=2, row=matches_row, sticky=tk.NSEW)
        self.print_prod_matches_button.grid(column=0, columnspan=2, row=matches_row+1, sticky=tk.NSEW)
        self.single_production_entry.grid(column=0, columnspan=2, row=matches_row+2, sticky=tk.NSEW)
        self.single_production_list.grid(column=2, columnspan=4, row=matches_row, rowspan=3, sticky=tk.NSEW)

        self.soar_control_panel_separator_3.grid(column=0, columnspan=num_columns, row=matches_row+3, sticky=tk.NSEW, pady=5)

        reset_row = matches_row + 4
        self.reinit_soar_button.grid(column=0, columnspan=2, row=reset_row, rowspan=1, sticky=tk.NSEW)
        self.excise_all_button.grid(column=2, columnspan=2, row=reset_row, rowspan=1, sticky=tk.NSEW) 
        self.reset_soar_button.grid(column=4, columnspan=2, row=reset_row, rowspan=1, sticky=tk.NSEW) 
        self.source_file_button.grid(column=0, columnspan=2, row=reset_row+1, rowspan=1, sticky=tk.NSEW)
        self.source_file_entry.grid(column=2, columnspan=4, row=reset_row+1, rowspan=1, sticky=tk.NSEW) 
        self.soar_control_panel_separator_4.grid(column=0, columnspan=num_columns, row=reset_row+2, sticky=tk.NSEW, pady=5)

        input_row = reset_row+3
        self.soar_input_entry.grid(column=0, columnspan=4, row=input_row, sticky=tk.NSEW)
        self.soar_input_send_button.grid(column=4, columnspan=2, row=input_row, sticky=tk.NSEW)

        # CONFIGURE UI ELEMENTS
        #######################
        self.single_production_list.bind('<<ListboxSelect>>', self._production_select_callback)
        self.soar_input_entry.bind("<Return>", self._soar_send_callback)

    def __output_highlight(func):
        def func_with_highlight(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.soar_output_highlight_tag = "output-white" if self.soar_output_highlight_tag == "output-grey" else "output-grey"
        return func_with_highlight

    @__output_highlight
    def _soar_send_callback(self):
        self.agent.execute_command(self.soar_user_input_var.get(), True)

    @__output_highlight
    def _soar_step_callback(self, num_steps=1):
        self.agent.execute_command(f"step {num_steps}", True)
    
    @__output_highlight
    def _print_state_callback(self, target="S1 -d 6"):
        self.agent.execute_command(f"p {target}", True)

    @__output_highlight
    def _soar_run_callback(self):
        self.agent.execute_command("run", True)

    @__output_highlight
    def _soar_phase_step_callback(self):
        self.agent.execute_command("r -p 1", True)

    @__output_highlight
    def _print_all_matches_callback(self):
        self.agent.execute_command("matches", True)

    @__output_highlight
    def _print_prod_matches_callback(self):
        target = self.production_match_entry_text_var.get()
        self.agent.execute_command(f"matches {target}", True)

    @__output_highlight
    def _production_select_callback(self, event):
        selection_index = self.single_production_list.curselection()
        production = self.single_production_list.get(selection_index)
        self.production_match_entry_text_var.set(production)

    @__output_highlight
    def _reinit_soar_callback(self):
        self.agent.execute_command("soar init", True)

    @__output_highlight
    def _excise_all_command_callback(self):
        self.agent.execute_command("production excise --all", True)
        self._load_production_list()

    @__output_highlight
    def _reset_soar_callback(self):
        self._excise_all_command_callback()
        self._reinit_soar_callback()

    @__output_highlight
    def _source_soar_file_callback(self):
        filename = self.source_file_text_var.get()
        self.agent.execute_command(f"source {filename}", True)

    def _load_production_list(self):
        raw_productions=self.agent.execute_command("p", False)
        self.production_list = raw_productions.split("\n")


    ##############################
    # MALMO CONTROL GUI ELEMENTS #
    ##############################

    def make_mission_control_widgets(self):
        # CREATE UI ELEMENT OBJECTS
        ###########################
        self.mission_control_frame = ttk.Frame(self, relief="groove", borderwidth=5)
        self.mission_control_label = ttk.Label(self.mission_control_frame, text="Malmo Control Panel", anchor=tk.CENTER)

        self.malmo_control_panel_separator_0 =ttk.Separator(self.mission_control_frame, orient=tk.HORIZONTAL)
        self.malmo_control_panel_separator_1 =ttk.Separator(self.mission_control_frame, orient=tk.HORIZONTAL)
        
        self.mission_port_entry     = ttk.Entry(self.mission_control_frame, textvariable=self.mission_port_text_var)
        self.launch_client_button   = ttk.Button(self.mission_control_frame, text="Launch Client", command=self._launch_malmo_client)
        self.mission_init_button    = ttk.Button(self.mission_control_frame, text="Init Mission", command=self._init_mission)
        self.mission_select_button  = ttk.Button(self.mission_control_frame, text="Select Mission", command=self._select_mission_file)
        self.current_mission_label  = ttk.Label(self.mission_control_frame, textvariable=self.mission_file_text_var)

        self.mission_choose_action_dropdown = ttk.Combobox(self.mission_control_frame, textvariable=self.action_select_text_var)
        self.mission_choose_action_button   = ttk.Button(self.mission_control_frame, text="Act", command=self._mission_do_action)

        self.vertical_fill_frame = ttk.Frame(self)

        # GRID UI ELEMENTS
        ##################
        num_columns = 3
        for col_i in range(num_columns):
            self.mission_control_frame.columnconfigure(col_i, weight=1, uniform="malmo")

        self.mission_control_frame.grid(column=0, row=1, sticky=tk.EW)
        self.mission_control_label.grid(column=0, columnspan=3, row=0, sticky=tk.NSEW, pady=5)

        self.malmo_control_panel_separator_0.grid(column=0, columnspan=3, row=1, sticky=tk.NSEW, pady=5)

        self.mission_port_entry.grid(column=0, row=2, sticky=tk.NSEW, pady=3)
        self.current_mission_label.grid(column=1, columnspan=2, row=2, sticky=tk.NSEW)

        self.launch_client_button.grid(column=0, row=3, sticky=tk.NSEW)
        self.mission_select_button.grid(column=1, row=3, sticky=tk.NSEW)
        self.mission_init_button.grid(column=2, row=3, sticky=tk.NSEW)

        self.malmo_control_panel_separator_1.grid(column=0, columnspan=3, row=4, sticky=tk.NSEW, pady=5)
        
        self.mission_choose_action_dropdown.grid(column=0, columnspan=2, row=5, sticky=tk.NSEW)
        self.mission_choose_action_button.grid(column=2, row=5, sticky=tk.NSEW)

        self.vertical_fill_frame.grid(column=0, row=3, rowspan=3, sticky=tk.NSEW)

    def _launch_malmo_client(self):
        MALMO_ARGS = [f"/home/boggsj/Coding/malmo/Minecraft/launchClient.sh", "-port", self.mission_port_text_var.get(), "-env"]
        malmo_proc = Popen(MALMO_ARGS, stdout=sys.stdout)

    def _select_mission_file(self):
        file_types = (('xml files', '*.xml'),)
        self.mission_file = Path(tkfd.askopenfilename(title="Select mission file", filetypes=file_types))
        self.mission_file_text_var.set(f"Selected: {self.mission_file}")

    def _init_mission(self):
        if self.mission_file is None:
            print("No mission file selected")
            return
        self.mission_port = int(self.mission_port_text_var.get())
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

    def _reset_mission(self):
        self.update_observation(self.env.reset())

    
    #######################
    # SOAR OUTPUT WIDGETS #
    #######################

    def make_soar_output_widgets(self):
        # CREATE UI ELEMENT OBJECTS
        ###########################
        self.soar_output_frame      = ttk.Frame(self, relief="groove")
        self.soar_output_label      = ttk.Label(self.soar_output_frame, text="Soar Output", anchor=tk.CENTER, relief="ridge")

        self.soar_output_text       = tk.Text(self.soar_output_frame, width=100, height=50)
        self.soar_output_scrollbar  = ttk.Scrollbar(self.soar_output_frame, orient=tk.VERTICAL, command=self.soar_output_text.yview)

        self.soar_state_viewer_tree = ttk.Treeview(self.soar_output_frame, columns=("value"))
        self.soar_vog_viewer_tree   = ttk.Treeview(self.soar_output_frame, columns=("value"))

        # GRID UI ELEMENTS
        ##################
        self.soar_output_frame.grid(column=1, row=0, rowspan=4, sticky=tk.NSEW)
        self.soar_output_label.grid(column=0, columnspan=4, row=0, sticky=tk.NSEW, ipady=5)

        self.soar_output_text.grid(column=0, row=1, rowspan=2, stick=tk.NSEW)
        self.soar_output_scrollbar.grid(column=1, row=1, rowspan=2, sticky=tk.NSEW)
        
        self.soar_state_viewer_tree.grid(column=2, row=1, stick=tk.NSEW)
        self.soar_vog_viewer_tree.grid(column=2, row=2, sticky=tk.NSEW)

        # CONFIGURE UI ELEMENTS
        #######################
        self.soar_output_text.configure(yscrollcommand=self.soar_output_scrollbar.set)
        self.soar_output_text.tag_configure("output-white", background='white smoke')
        self.soar_output_text.tag_configure("output-grey", background='alice blue')

        self.soar_state_viewer_tree.insert("", tk.END, "S1")
        self.soar_vog_viewer_tree.insert("", tk.END, "-1")

    def _soar_output_callback(self, text):
        self.soar_output_text.insert(tk.END, text, (self.soar_output_highlight_tag,))
        self.soar_output_text.insert(tk.END, "\n", (self.soar_output_highlight_tag,))
        self.soar_output_text.yview_moveto(1.0)
        print(text)

    def _soar_state_viewer_callback(self, state_text, vog_text):
        self.soar_state.parse_state_text(state_text)
        self._write_state_to_viewer()

        self.vog.parse_vog_text(vog_text)
        self._write_vog_text_to_viewer()

    def _write_state_to_viewer(self):
        self.soar_state_viewer_tree.delete("S1")
        self.soar_state_viewer_tree.insert("", tk.END, "S1", text="root")
        self.soar_state.insert_in_treeview(self.soar_state_viewer_tree)
        self.soar_state_viewer_tree.item("S1", open=True)

    def _write_vog_text_to_viewer(self):
        self.soar_vog_viewer_tree.delete("-1")
        self.soar_vog_viewer_tree.insert("", tk.END, "-1", text="root")
        for node_id, node in self.vog.nodes.items():
            if node_id == -1: continue
            if node.node_op != "save-to-file":
                tree_id = self.soar_vog_viewer_tree.insert("-1", tk.END, str(node_id), text=node.node_name, values=(node.node_op,))
            else:
                tree_id = self.soar_vog_viewer_tree.insert(str(node.attributes["target"][0]), tk.END, str(node_id), text=node.node_name, values=(node.node_op,))
            for attr, vals in node.attributes.items():
                for v in vals:
                    self.soar_vog_viewer_tree.insert(tree_id, tk.END, text=attr, values=(v,))
        self.soar_vog_viewer_tree.item("-1", open=True)

    
    def make_vog_visual_widget(self):
        pass


    def perform_action(self, action_str):
        true = True     # Allows the eval() method below to work
        false = False   # Allows the eval() method below to work
        action_idx = self.mission_commands.index(action_str)
        obs, reward, done, info = self.env.step(action_idx)
        print(info)
        self.connector.update_info(eval(info))
        self.update_observation(obs)

    def update_observation(self, observation:np.ndarray, info=None):
        self.current_observation = np.flip(observation.reshape(OBSERVATION_SHAPE), axis=0)
        observation_bgr = cv2.cvtColor(self.current_observation, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite("./observation_raw.png", observation_bgr)
        self.connector.send_vision(observation_bgr)