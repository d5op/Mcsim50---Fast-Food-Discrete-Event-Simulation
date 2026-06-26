import requests
import pandas as pd
import plotly.express as px

from flask import redirect, render_template, session
from functools import wraps
import plotly.graph_objects as go

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def cal(sim_list):
        count_list = [len(l) for l in sim_list]
        serve_list = [sum(1 for dict in l if not dict["left"]) for l in sim_list]
        leave_list = [sum(1 for dict in l if dict["left"]) for l in sim_list]

        avg_waittime = (sum(sum(dic["t_waiting"] for dic in l) / len(l) for l in sim_list) / len(sim_list))

        all_waits = [list(dic["t_waiting"] for dic in l) for l in sim_list]

        return count_list, serve_list, leave_list, avg_waittime, all_waits

def graph_gen(wait_list_cycle, serve_l, left_l, total_l):

    wait_list = [wt for cycle in wait_list_cycle for wt in cycle]
    
    df = pd.DataFrame({'wait_times': wait_list})
    fig_his = px.histogram(wait_list, nbins=10)
    fig_his.update_layout(
        xaxis_title= "Waiting Time(min)",
        yaxis_title= "Number of Customers",
        title="Waiting Time Distribution"
    )

    labels = ["0-1","1-2","2-3","3-4","4-5","5-10","10-15",">15"]
    df['bracket'] = pd.cut(df['wait_times'], bins=[0,1,2,3,4,5,10,15,float('inf')], labels=labels, right=False)
    df['bracket'] = df['bracket'].astype(str)


    pie_data = df['bracket'].value_counts().reset_index()
    pie_data.columns = ['bracket', 'count']

    fig_pie = px.pie(pie_data, names='bracket', values='count', title='Waiting Time Distribution')

    wait_means = [sum(w)/len(w) for w in wait_list_cycle]

    fig_line = px.line(
        x=list(range(1, len(wait_means)+1)),
        y=wait_means,
        labels={'x':'Cycle', 'y':'Mean Waiting Time(min)'},
        title='Mean Waiting Time per Cycle'
    )

    y = []
    x = []
    cycle_ids = []

    for i, cycle in enumerate(wait_list_cycle, start=1):
        y.extend(cycle)
        x.extend(range(1, len(cycle)+1))
        cycle_ids.extend([f"Cycle {i}"] * len(cycle))

    df1 = pd.DataFrame({'Customer':x, 'Waiting Time': y, 'Cycle': cycle_ids})

    fig_sca = px.scatter(
        df1,
        x='Customer',
        y='Waiting Time',
        color='Cycle',
        labels={'Customer':'Customer Index', 'Waiting Time':'Waiting Time (min)'},
        title='Waiting Time per Customer'
    )
    
    left_count = sum(left_l)
    served_count = sum(serve_l)

    fig_left = px.pie(names=['Served', 'Left'], values=[served_count, left_count],
                title="Customer Served vs Left")

    records = []
    for cycle_idx, cycle in enumerate(total_l):
        for cust in cycle:
            records.append({
                "cycle": f"Cycle {cycle_idx+1}",
                "arrival": cust["t_arrive"],
                "waiting": cust["t_waiting"],
                "left": cust["left"]
            })

    df2 = pd.DataFrame(records)
    df_sorted = df2.sort_values('arrival').reset_index(drop=True)

    # Assign a color to each cycle
    cycle_colors = ['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta']
    color_map = {f"Cycle {i+1}": cycle_colors[i % len(cycle_colors)] for i in range(len(total_l))}

    # Prepare frames
    frames = []
    max_len = len(df_sorted)
    for k in range(0, max_len, 10):
        frame_data = []
        for cycle_name in df_sorted['cycle'].unique():
            df_cycle = df_sorted[(df_sorted['cycle'] == cycle_name) & (df_sorted.index <= k)]
            frame_data.append(go.Scatter(
                x=df_cycle['arrival'],
                y=df_cycle['waiting'],
                mode='markers',
                name=cycle_name,
                marker=dict(color=color_map[cycle_name], size=8, line=dict(width=1, color='black'))
            ))
        frames.append(go.Frame(data=frame_data, name=str(k)))

    # Initial empty figure with one trace per cycle (needed for legend)
    init_data = []
    for cycle_name in df_sorted['cycle'].unique():
        init_data.append(go.Scatter(
            x=[],
            y=[],
            mode='markers',
            name=cycle_name,
            marker=dict(color=color_map[cycle_name], size=8, line=dict(width=1, color='black'))
        ))

    fig_live = go.Figure(
        data=init_data,
        layout=go.Layout(
            title="Customer Waiting Time Over Simulation",
            xaxis_title="Arrival Time",
            yaxis_title="Waiting Time",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="Play",
                        method="animate",
                        args=[None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]),
                    dict(label="Pause",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
                ]
            )]
        ),
        frames=frames
    )
    graph_live = fig_live.to_html(full_html=False)       
    graph_line = fig_line.to_html(full_html=False)
    graph_his = fig_his.to_html(full_html=False)
    graph_pie = fig_pie.to_html(full_html=False)
    graph_sca = fig_sca.to_html(full_html=False)
    graph_left = fig_left.to_html(full_html=False)

    return graph_his, graph_pie, graph_line, graph_sca, graph_left, graph_live