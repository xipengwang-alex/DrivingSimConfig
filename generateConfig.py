import plotly.graph_objects as go

with open('WayPointLog.csv', 'r') as file:
    lines = file.readlines()

waypoints = []
for line in lines:
    data = line.strip().split(', ')
    try:
        index = int(data[0])
        name = data[1]
        x = float(data[2])
        y = float(data[3])
        waypoints.append((index, name, x, y))
    except ValueError:
        print(f"Skipping invalid data: {line.strip()}")

waypoint_size_x = 2150
waypoint_size_y = 2150

traces = []
for waypoint in waypoints:
    index, name, x, y = waypoint
    trace = go.Scatter(
        x=[x - waypoint_size_x / 2, x + waypoint_size_x / 2, x + waypoint_size_x / 2, x - waypoint_size_x / 2, x - waypoint_size_x / 2],
        y=[y - waypoint_size_y / 2, y - waypoint_size_y / 2, y + waypoint_size_y / 2, y + waypoint_size_y / 2, y - waypoint_size_y / 2],
        mode='lines',
        fill='toself',
        opacity=0.5,
        line=dict(width=0),
        fillcolor=f'rgba({index}, {255 - index}, {index}, 0.5)',
        text=f"Index: {index}<br>Name: {name}<br>Size: {waypoint_size_x} x {waypoint_size_y}",
        hoverinfo='text'
    )
    traces.append(trace)

label_traces = []
for waypoint in waypoints:
    index, name, x, y = waypoint
    label_trace = go.Scatter(
        x=[x],
        y=[y],
        mode='text',
        text=[f"{index}"],
        textposition='middle center',
        textfont=dict(size=12),
        hoverinfo='none'
    )
    label_traces.append(label_trace)

traces.extend(label_traces)

layout = go.Layout(
    title='Waypoint Placement (2D)',
    xaxis=dict(title='X (cm)'),
    yaxis=dict(title='Y (cm)'),
    width=800,
    height=800, 
    showlegend=False
)

fig = go.Figure(data=traces, layout=layout)

fig.update_layout(
    clickmode='event+select'
)

fig.show()