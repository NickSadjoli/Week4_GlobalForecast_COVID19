"""
Contains the function tools to enable more convenient data visualization in a notebook.

Authored by: Nicholas Sadjoli (Github @NickSadjoli)
Co-authored by: Josephine Monica (Github @josephinemonica)
"""

import matplotlib.pyplot as plt
from matplotlib import gridspec
import plotly.graph_objs as go

def plot_grid_pyplot(grid_size, x_list, y_list, label_list, log_usages, grid_titles, plot_type="scatter", g_width_ratios=[1,1], wspace=0.25, scatter_size=8, figsize=(12,5)):
    '''
    Plots a list of x and y data to a Matplotlib Pyplot's Grid

    Arguments:
    - grid_size => a Tuple specifying the number of (rows, columns) of the grid
    - x_list => List, with expected size: (grid_size[rows] * grid_size[columns]). Contains list of x data points to be used for each grid cell.
    - y_list => List, with expected size: (grid_size[rows] * grid_size[columns]). Contains list of y data points to be used for each grid cell.
    - label_list => List, with expected size: (grid_size[rows] * grid_size[columns]). Contains list of labels to be assigned to the x and y data points.
    - log_usages => Boolean List, with expected size: (grid_size[rows] * grid_size[columns]). Specifies whether each grid cell uses a logarithmic or normal scale.
    - grid_titles => List of strings, with expected size: (grid_size[rows] * grid_size[columns]). Contains the titles to be assigned to each grid cell.
    - plot_type => (Optional) Specifies the type of data marker to be used. Default is scatterplot data ("scatter")
    - g_width_ratio => (Optional) Width ratio to be used by GridSpec
    - wspace => (Optional) Sets the width space to be used by GridSpec
    - scatter_size => (Optional) If plot_type is chosen to be of type "scatter", determines the size of of scatterplot points to be renderred.
    - figsize => (Optional) Sets the size of the entire figure.

    Returns:
      Plots the data to a GridSpec figure of specified size 
    '''

    #Perform some sanity checks on the amount of data provided...
    if len(x_list) != len(y_list):
        print("ERROR - Input data has unequal lengths. Please ensure that x and y lengths are equal!")
        if len(x_list) > len(y_list):
            print("len(x) > len(y)!")
            return False
        else:
            print("len(x) < len(y)")
            return False
    
    #... as well as their dimensions vs requested grid size
    if len(x_list) != (grid_size[0] * grid_size[1]):
        print("ERROR - Length of data not matching requested grid size!")
        return False
    
    grid_rows, grid_columns = grid_size
    gs = gridspec.GridSpec(grid_rows, grid_columns, width_ratios=g_width_ratios, wspace=wspace)
    fig = plt.figure(figsize=figsize)
    
    #iterate for each axes in the gridSpec
    for i in range(0, grid_rows):
        for j in range(0, grid_columns):
            cur_ax = fig.add_subplot(gs[i, j])
            #axes_list.append(cur_ax)
            data_idx = (i * grid_columns) + j
            if log_usages[data_idx]:
                cur_ax.set_yscale('log')
            
            cur_x_data = x_list[data_idx]
            cur_y_data = y_list[data_idx]
            cur_labels = label_list[data_idx]
            if plot_type == "scatter":
                for idx in range(0, len(cur_x_data)):
                    cur_ax.scatter(cur_x_data[idx], cur_y_data[idx], label=cur_labels[idx], s=scatter_size)
            elif plot_type == "line":
                    cur_ax.plot(cur_x_data[idx], cur_y_data[idx], label=cur_labels[idx])
            cur_ax.set_title(grid_titles[data_idx])
            cur_ax.legend()

def plotly_scatter_obj(x, y, marker_color='rgb(255, 0, 0)', marker_size=7, marker_types='markers', name=""):
    '''
    Returns a Plotly ScatterPlot Graph Object.

    Arguments:
    - x => x data points to be used. Expected to have same length as y
    - y => y data points to be used. Expected to have same length as x.
    - marker_color => (Optional) Specifies the color to be used to represent the data points. 
    - marker_size => (Optional) Specifies the size of the markers to be used when rendering later.
    - marker_types => (Optional) Type of marker to be used. By default is normal 'scatterplot', but could be changed to a 'line' plot
    - name => (Optional) Name of the Graph Object to be assigned
    '''
    return go.Scatter(x = x, y = y, marker=go.scatter.Marker(color=marker_color, size=marker_size), mode=marker_types, name=name)

def graph_plot_w_plotly(plotly_go_data, graph_title, axis_titles, axis_ticklens, axis_zerolines, plot_dims=(500, 700), bg_color="rgb(299, 299, 299)"):
    '''
    Renders a graph using Plotly

    Arguments:
    - plotly_go_data => List of Plotly Graph Objects to be renderred/drawn.
    - graph_title => String object, Title of the graph to be renderred.
    - axis_titles => Tuple object, containing titles to be given for each of the x and y axes.
    - axis_ticklens => Tuple object, specifying the ticklens to be used for each x and y axes.
    - axis_zerolines => Tuple object, specifying whether to use the zeroline for each x and y axes.
    - plot_dims => (Optional) Tuple object, specifying (height, width) of the Plotly Graph to be renderred
    - bg_color => (Optional) Specifies the color of the background of the Plotly Graph
    '''
    x_title, y_title = axis_titles,
    x_ticklen, y_ticklen = axis_ticklens,
    x_zeroline, y_zeroline = axis_zerolines
    graph_height, graph_width = plot_dims
    layout = go.Layout(title        = graph_title, 
                       plot_bgcolor = bg_color,
                       xaxis        = dict(title=x_title, ticklen=x_ticklen, zeroline=x_zeroline),
                       yaxis        = dict(title=y_title, ticklen=y_ticklen, zeroline=y_zeroline),
                       height       = graph_height,
                       width        = graph_width
                       )
    fig = go.Figure(data=plotly_go_data, layout=layout)
    fig.show()
    
