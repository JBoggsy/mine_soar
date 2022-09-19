from argparse import ArgumentParser
import json
from math import ceil, sqrt
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt

#######################
# PARSE CLI ARGUMENTS #
#######################
cli = ArgumentParser(description="Python-based tool for viewing the .json files produced as debugging output from SVS.")
cli.add_argument("names", type=str, help="The node names to be examined. Defaults to all.", nargs='*')
cli_namespace = cli.parse_args()


def show_matrix_as_heatmap(matrix_data: np.ndarray) -> tuple[Figure, np.ndarray]:
    rows, cols, channels = matrix_data.shape
    subplot_cols = ceil(sqrt(channels))
    subplot_rows = ceil(channels/subplot_cols)
    fig, ax = plt.subplots(nrows=subplot_rows, ncols=subplot_cols)

    if channels == 1:
        ax = np.array([ax,]).reshape((1,1))
    if channels == 2:
        ax = ax.reshape((2,1))

    for chan in range(channels):
        row = chan//subplot_rows
        col = chan - (row*subplot_cols)
        chan_img = ax[row, col].imshow(matrix_data[:,:,chan])
        if channels > 1:
            ax[row, col].set_title(f"Channel {chan}")

    # if channels == 3:
    #     ax[1,1].imshow(matrix_data.astype(int))

    fig.tight_layout()

    return fig, ax

def show_matrix_as_image(matrix_data):
    assert type(matrix_data) is np.ndarray, "Image matrix must be of type np.ndarray"

    rows, cols, chans = matrix_data.shape
    assert chans in [1, 3, 4], "Image matrix must have either 1, 3, or 4 channels"

    if chans == 3:
        matrix_data = matrix_data[...,::-1].copy()
    elif chans == 4:
        matrix_data = matrix_data[...,[2,1,0,3]].copy()
    matrix_data = matrix_data.astype(int)
    
    fig, ax = plt.subplots()
    ax.imshow(matrix_data)
    
    return fig, np.array([ax,]).reshape(1,1)

def show_matrix_as_points(matrix_data):
    assert type(matrix_data) is np.ndarray, "Image matrix must be of type np.ndarray"

    rows, cols, chans = matrix_data.shape
    assert chans in [2, 3], "Image matrix must have either 2 or 3 channels"

    if chans == 3:
        dist_matrix = np.sqrt(np.square(matrix_data[:,:,2]) + np.square(matrix_data[:,:,0]) + np.square(matrix_data[:,:,1]))
        fig = plt.figure()
        ax = plt.axes(projection="3d")
        ax.scatter3D(matrix_data[:,:,2].flatten(), matrix_data[:,:,0].flatten(), matrix_data[:,:,1].flatten(), c=dist_matrix)
        ax.view_init(15, -135)
    
    return fig, ax



if __name__ == "__main__":
    key_file = Path("./key.json")
    with key_file.open('r') as f:
        node_key = json.load(f)
    node_files = list(Path.cwd().glob("node*.json"))

    for json_file in node_files:
        node_id = json_file.stem.split("-")[1]
        
        node_name = node_key[node_id]["node-name"][0] if "node-name" in node_key[node_id] else "save-node"
        if node_name not in cli_namespace.names and len(cli_namespace.names) > 0:
            continue
        
        node_op = node_key[node_id]["op-name"][0]

        with json_file.open('r') as f:
            raw_json = json.load(f)
            image_data = raw_json['Image Data']
            rows = image_data['rows']
            cols = image_data['cols']
            raw_data = image_data['data']
            data_type = image_data['dt']
            if len(data_type) > 1:
                channels = int(data_type[0])
            else:
                channels = 1
        
        matrix = np.array(raw_data).reshape((rows,cols,channels))

        print(f"Processing node-{node_id} ({node_op}) with shape ({rows}, {cols}, {channels})...")
        if node_op in ["save-to-file", "get-from-vsm"]:
            fig, axes = show_matrix_as_image(matrix)
        elif node_op in ["stack-matrices"]:
            fig, axes = show_matrix_as_points(matrix)
        else:
            fig, axes = show_matrix_as_heatmap(matrix)
            axes = axes.flatten()
            for i, ax in enumerate(axes):
                ax.set_title(f"{node_name}-{i}")
            
    plt.show()