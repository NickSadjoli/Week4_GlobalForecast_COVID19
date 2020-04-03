import matplotlib.pyplot as plt
from matplotlib import gridspec
import plotly.graph_objs as go

def plot_grid_pyplot(grid_size, x_list, y_list, label_list, log_usages, grid_titles, plot_type="scatter", g_width_ratios=[1,1], wspace=0.25, scatter_size=8, figsize=(12,5)):
    
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
    return go.Scatter(x = x, y = y, marker=go.scatter.Marker(color=marker_color, size=marker_size), mode=marker_types, name=name)

def graph_plot_w_plotly(plotly_go_data, graph_title, axis_titles, axis_ticklens, axis_zerolines, plot_dims=(500, 700), bg_color="rgb(299, 299, 299)"):
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
    
