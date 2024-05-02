import cv2
import numpy as np

image_offset_x = 900
image_offset_y = -700
scale = 0.0253
waypoint_size = 10

map_image = cv2.imread('test_map.png')

waypoints = []
with open('WayPointLog.csv', 'r') as file:
    for line in file:
        data = line.strip().split(', ')
        if len(data) >= 4:
            index, name, x, y = data[:4]
            waypoints.append((int(index), name, float(x), float(y)))

route_mode = False
route = []
last_waypoint = None
mouse_pos = None
hovered_waypoint = None
route_saved = False

min_x = min(waypoint[2] for waypoint in waypoints) + image_offset_x
max_x = max(waypoint[2] for waypoint in waypoints)
min_y = min(waypoint[3] for waypoint in waypoints) + image_offset_y
max_y = max(waypoint[3] for waypoint in waypoints)

offset_x = (map_image.shape[1] - (max_x - min_x) * scale) / 2
offset_y = (map_image.shape[0] - (max_y - min_y) * scale) / 2

def mouse_callback(event, x, y, flags, param):
    global route_mode, last_waypoint, mouse_pos, hovered_waypoint, route_saved
    if event == cv2.EVENT_LBUTTONDOWN:
        waypoint_clicked = False
        for waypoint in waypoints:
            scaled_x = int((waypoint[2] - min_x) * scale + offset_x)
            scaled_y = int((waypoint[3] - min_y) * scale + offset_y)
            if abs(x - scaled_x) < waypoint_size and abs(y - scaled_y) < waypoint_size:
                if route_mode and waypoint == last_waypoint:
                    route_mode = False
                    last_waypoint = None
                else:
                    if route_mode:
                        route.append((last_waypoint, waypoint))
                        route_saved = False
                    route_mode = True
                    last_waypoint = waypoint
                waypoint_clicked = True
                break
        if not waypoint_clicked and route_mode:
            route_mode = False
            last_waypoint = None
    elif event == cv2.EVENT_MOUSEMOVE:
        mouse_pos = (x, y)
        hovered_waypoint = None
        for waypoint in waypoints:
            scaled_x = int((waypoint[2] - min_x) * scale + offset_x)
            scaled_y = int((waypoint[3] - min_y) * scale + offset_y)
            if abs(x - scaled_x) < waypoint_size and abs(y - scaled_y) < waypoint_size:
                hovered_waypoint = waypoint
                break

cv2.namedWindow('Map')
cv2.setMouseCallback('Map', mouse_callback)

while True:
    display_image = map_image.copy()

    for waypoint in waypoints:
        scaled_x = int((waypoint[2] - min_x) * scale + offset_x)
        scaled_y = int((waypoint[3] - min_y) * scale + offset_y)
        if waypoint == last_waypoint:
            cv2.rectangle(display_image, (scaled_x - waypoint_size, scaled_y - waypoint_size),
                          (scaled_x + waypoint_size, scaled_y + waypoint_size), (0, 0, 255), -1)
        else:
            cv2.rectangle(display_image, (scaled_x - waypoint_size, scaled_y - waypoint_size),
                          (scaled_x + waypoint_size, scaled_y + waypoint_size), (0, 255, 0), -1)

    for start, end in route:
        scaled_start_x = int((start[2] - min_x) * scale + offset_x)
        scaled_start_y = int((start[3] - min_y) * scale + offset_y)
        scaled_end_x = int((end[2] - min_x) * scale + offset_x)
        scaled_end_y = int((end[3] - min_y) * scale + offset_y)
        cv2.arrowedLine(display_image, (scaled_start_x, scaled_start_y), (scaled_end_x, scaled_end_y), (255, 0, 0), 2)

    if route_mode and last_waypoint is not None and mouse_pos is not None:
        scaled_start_x = int((last_waypoint[2] - min_x) * scale + offset_x)
        scaled_start_y = int((last_waypoint[3] - min_y) * scale + offset_y)
        cv2.arrowedLine(display_image, (scaled_start_x, scaled_start_y), mouse_pos, (255, 0, 0), 2)

    if hovered_waypoint is not None:
        text_pos = list(mouse_pos)
        text_pos[0] += 20
        text_pos[1] += 10
        cv2.putText(display_image, str(hovered_waypoint[0]), tuple(text_pos), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    route_color = (0, 0, 255) if not route_saved else (0, 255, 0)
    cv2.putText(display_image, "Route:", (display_image.shape[1] - 150, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, route_color, 2)
    for i, (start, end) in enumerate(route):
        cv2.putText(display_image, f"{start[0]} -> {end[0]}", (display_image.shape[1] - 120, 40 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, route_color, 2)

    cv2.imshow('Map', display_image)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        route.clear()
        route_mode = False
        last_waypoint = None
        route_saved = False
    elif key == ord('s'):
        with open('route.txt', 'w') as file:
            for start, end in route:
                file.write(f"{start[0]}, {start[1]}, {start[2]}, {start[3]}, {end[0]}, {end[1]}, {end[2]}, {end[3]}\n")
        route_saved = True

cv2.destroyAllWindows()
