import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import json

# Constants
IMAGE_COORD_LEFT_BOTTOM = -80300, 50000 #(X=-83481.581331,Y=49212.589821,Z=63.579365)
IMAGE_COORD_RIGHT_TOP = 70000, -57000 #(X=68105.272395,Y=-57570.548075,Z=63.579365)
WAYPOINT_SIZE = 7
MAP_IMAGE_PATH = 'SmallCityLvl_1.png'
WAYPOINT_FILE = 'WayPointLog.csv'
ROUTE_FILE = '../InitConfig.json'
FONT = ('Arial', 12)

class Waypoint:
    def __init__(self, index, name, x, y, next_waypoint=None, is_self_report=False, set_transparency_on=False,
                 set_task_complexity_high=False, set_reliability_low=False, set_control_mode_manual=False):
        self.index = index
        self.name = name
        self.x = x
        self.y = y
        self.next_waypoint = next_waypoint
        self.is_self_report = is_self_report
        self.set_transparency_on = set_transparency_on
        self.set_task_complexity_high = set_task_complexity_high
        self.set_reliability_low = set_reliability_low
        self.set_control_mode_manual = set_control_mode_manual
        self.if_transparency_changed = False
        self.if_task_complexity_changed = False
        self.if_reliability_changed = False
        self.if_control_mode_changed = False

    def reset_attributes(self):
        self.next_waypoint = None
        self.is_self_report = False
        self.set_transparency_on = False
        self.set_task_complexity_high = False
        self.set_reliability_low = False
        self.set_control_mode_manual = False
        self.if_transparency_changed = False
        self.if_task_complexity_changed = False
        self.if_reliability_changed = False
        self.if_control_mode_changed = False

class WaypointHandler:
    def __init__(self, filename):
        self.waypoints = self.load_waypoints(filename)

    def load_waypoints(self, filename):
        waypoints = []
        with open(filename, 'r') as file:
            for line in file:
                data = line.strip().split(', ')
                if len(data) >= 4:
                    index, name, x, y = data[:4]
                    waypoints.append(Waypoint(int(index), name, float(x), float(y)))
        return waypoints
    
class MapVisualizer:
    def __init__(self, master, image_path, waypoint_handler):
        self.master = master
        self.map_image = cv2.imread(image_path)
        self.waypoint_handler = waypoint_handler
        self.selected_waypoint = None
        self.route = []
        self.route_mode = False
        self.last_waypoint = None
        self.hovered_waypoint = None
        self.route_saved = False
        self.mouse_pos = None
        
        map_points = np.array([(0, 0), (self.map_image.shape[1], 0),
                            (self.map_image.shape[1], self.map_image.shape[0]),
                            (0, self.map_image.shape[0])], dtype=np.float32)
                
        coordinate_points = np.array([(IMAGE_COORD_LEFT_BOTTOM[0], IMAGE_COORD_RIGHT_TOP[1]), (IMAGE_COORD_RIGHT_TOP[0], IMAGE_COORD_RIGHT_TOP[1]), 
                                      (IMAGE_COORD_RIGHT_TOP[0], IMAGE_COORD_LEFT_BOTTOM[1]), (IMAGE_COORD_LEFT_BOTTOM[0], IMAGE_COORD_LEFT_BOTTOM[1])], dtype=np.float32)

        map_points = map_points.reshape(4, 1, 2)
        coordinate_points = coordinate_points.reshape(4, 1, 2)
        
        self.transformation_matrix = cv2.getPerspectiveTransform(coordinate_points, map_points)
        
        self.canvas = tk.Canvas(self.master, width=self.map_image.shape[1], height=self.map_image.shape[0])
        self.canvas.pack(side=tk.LEFT)

        self.options_frame = tk.Frame(self.master)
        self.options_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.create_option_widgets()
        self.update_waypoint_info()

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def transform_coordinates(self, x, y):
        point = np.array([[x, y]], dtype=np.float32)
        point = np.reshape(point, (1, 1, 2))  # Reshape to (1, 1, 2)
        transformed_point = cv2.perspectiveTransform(point, self.transformation_matrix)
        return int(transformed_point[0][0][0]), int(transformed_point[0][0][1])

    def draw_waypoints(self, image):
        for waypoint in self.waypoint_handler.waypoints:
            scaled_x, scaled_y = self.transform_coordinates(waypoint.x, waypoint.y)
            color = (0, 0, 255) if waypoint == self.last_waypoint else (0, 255, 0)
            cv2.rectangle(image, (scaled_x - WAYPOINT_SIZE, scaled_y - WAYPOINT_SIZE),
                        (scaled_x + WAYPOINT_SIZE, scaled_y + WAYPOINT_SIZE), color, -1)

            if waypoint == self.selected_waypoint:
                cv2.rectangle(image, (scaled_x - WAYPOINT_SIZE - 2, scaled_y - WAYPOINT_SIZE - 2),
                            (scaled_x + WAYPOINT_SIZE + 2, scaled_y + WAYPOINT_SIZE + 2), (255, 0, 0), 2)

    def draw_routes(self, image):
        for start, end in self.route:
            start_x, start_y = self.transform_coordinates(start.x, start.y)
            end_x, end_y = self.transform_coordinates(end.x, end.y)
            cv2.arrowedLine(image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)
            
    def create_option_widgets(self):
        self.waypoint_info_label = tk.Label(self.options_frame, text="Waypoint Info", font=FONT)
        self.waypoint_info_label.pack()

        self.waypoint_labels = {}
        labels = ["Index", "Name", "X", "Y", "Next Waypoint"]
        for label in labels:
            self.waypoint_labels[label] = tk.Label(self.options_frame, text=f"{label}: ", font=FONT)
            self.waypoint_labels[label].pack(anchor=tk.W)

        button_frame = tk.Frame(self.options_frame)
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        self.waypoint_labels["Self-Report"] = tk.Button(button_frame, text="Self-Report: ", font=FONT, relief=tk.GROOVE, padx=5, pady=2)
        self.waypoint_labels["Self-Report"].pack(anchor=tk.W, fill=tk.X, pady=2)

        button_labels = ["Transparency On", "Task Complexity High", "Reliability Low", "Control Mode Manual"]
        for label in button_labels:
            button_subframe = tk.Frame(button_frame)
            button_subframe.pack(anchor=tk.W, fill=tk.X, pady=2)

            self.waypoint_labels[f"{label}_changed"] = tk.Button(button_subframe, text="", font=FONT, relief=tk.GROOVE, padx=5, pady=2, width=2)
            self.waypoint_labels[f"{label}_changed"].pack(side=tk.LEFT)

            self.waypoint_labels[label] = tk.Button(button_subframe, text=f"{label}: None", font=FONT, relief=tk.GROOVE, padx=5, pady=2)
            self.waypoint_labels[label].pack(side=tk.LEFT, fill=tk.X, expand=True)

    def draw(self):
        display_image = self.map_image.copy()
        self.draw_waypoints(display_image)
        self.draw_routes(display_image)
        self.draw_hover_info(display_image)
        self.draw_route_list(display_image)

        rgb_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        photo = ImageTk.PhotoImage(pil_image)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo

    def draw_hover_info(self, image):
        if self.hovered_waypoint is not None:
            scaled_x, scaled_y = self.transform_coordinates(self.hovered_waypoint.x, self.hovered_waypoint.y)
            text_pos = (scaled_x + 20, scaled_y + 10)
            cv2.putText(image, f"{self.hovered_waypoint.index}: {self.hovered_waypoint.name}", text_pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    def draw_route_list(self, image):
        route_color = (0, 0, 255) if not self.route_saved else (0, 255, 0)
        cv2.putText(image, "Route:", (image.shape[1] - 150, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, route_color, 2)
        for i, (start, end) in enumerate(self.route):
            cv2.putText(image, f"{start.index} -> {end.index}", (image.shape[1] - 120, 40 + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, route_color, 2)

    def on_left_click(self, event):
        self.process_click(event.x, event.y, left=True)

    def on_right_click(self, event):
        self.process_click(event.x, event.y, left=False)

    def on_mouse_move(self, event):
        self.mouse_pos = (event.x, event.y)
        self.update_hover(event.x, event.y)

    def process_click(self, x, y, left=True):
        clicked_waypoint = None
        for waypoint in self.waypoint_handler.waypoints:
            scaled_x, scaled_y = self.transform_coordinates(waypoint.x, waypoint.y)
            if abs(x - scaled_x) < WAYPOINT_SIZE and abs(y - scaled_y) < WAYPOINT_SIZE:
                clicked_waypoint = waypoint
                break

        if clicked_waypoint is not None:
            if left:
                self.toggle_route_mode(clicked_waypoint)
            
            self.selected_waypoint = clicked_waypoint
            self.update_waypoint_info()
        else:
            self.route_mode = False
            self.last_waypoint = None
            self.selected_waypoint = None
            self.update_waypoint_info()

    def toggle_route_mode(self, waypoint):
        if self.route_mode and waypoint == self.last_waypoint:
            self.route_mode = False
            self.last_waypoint = None
        else:
            if self.route_mode:
                if waypoint.next_waypoint == self.last_waypoint:
                    print("circle detected")
                    return
                self.last_waypoint.next_waypoint = waypoint.index
                self.route.append((self.last_waypoint, waypoint))
                self.route_saved = False
            self.route_mode = True
            self.last_waypoint = waypoint

    def update_hover(self, x, y):
        self.hovered_waypoint = None
        for waypoint in self.waypoint_handler.waypoints:
            scaled_x, scaled_y = self.transform_coordinates(waypoint.x, waypoint.y)
            if abs(x - scaled_x) < WAYPOINT_SIZE and abs(y - scaled_y) < WAYPOINT_SIZE:
                self.hovered_waypoint = waypoint
                break

    def clear_route(self):
        self.route.clear()
        self.route_mode = False
        self.last_waypoint = None
        self.route_saved = False
        for waypoint in self.waypoint_handler.waypoints:
            waypoint.reset_attributes()
        self.update_waypoint_info()

    def save_route(self, filename):
        route_details = []
        for start, end in self.route:
            special_functions = {}
            if start.if_transparency_changed:
                special_functions["set_transparency_on"] = start.set_transparency_on
            if start.if_task_complexity_changed:
                special_functions["set_task_complexity_high"] = start.set_task_complexity_high
            if start.if_reliability_changed:
                special_functions["set_reliability_low"] = start.set_reliability_low
            if start.if_control_mode_changed:
                special_functions["set_control_mode_manual"] = start.set_control_mode_manual

            route_details.append({
                "index": start.index,
                "name": start.name,
                "next_waypoint": start.next_waypoint,
                "is_self_report": start.is_self_report,
                "special_functions": special_functions
            })

        if end:
            special_functions = {}
            if end.if_transparency_changed:
                special_functions["set_transparency_on"] = end.set_transparency_on
            if end.if_task_complexity_changed:
                special_functions["set_task_complexity_high"] = end.set_task_complexity_high
            if end.if_reliability_changed:
                special_functions["set_reliability_low"] = end.set_reliability_low
            if end.if_control_mode_changed:
                special_functions["set_control_mode_manual"] = end.set_control_mode_manual

            route_details.append({
                "index": end.index,
                "name": end.name,
                "next_waypoint": None,
                "is_self_report": end.is_self_report,
                "special_functions": special_functions
            })

        route_json = {"waypoints": route_details}

        with open(filename, 'w') as file:
            json.dump(route_json, file, indent=4)
        self.route_saved = True

    def update_waypoint_info(self):
        if self.selected_waypoint is not None:
            self.waypoint_labels["Index"].config(text=f"Index: {self.selected_waypoint.index}")
            self.waypoint_labels["Name"].config(text=f"Name: {self.selected_waypoint.name}")
            self.waypoint_labels["X"].config(text=f"X: {self.selected_waypoint.x}")
            self.waypoint_labels["Y"].config(text=f"Y: {self.selected_waypoint.y}")
            self.waypoint_labels["Next Waypoint"].config(text=f"Next Waypoint: {self.selected_waypoint.next_waypoint}")

            self.waypoint_labels["Self-Report"].config(text=f"Self-Report: {self.selected_waypoint.is_self_report}", command=lambda: self.toggle_attribute(None, "is_self_report"), fg="forest green" if self.selected_waypoint.is_self_report else "brown3")

            attribute_mapping = {
                "Transparency On": ("if_transparency_changed", "set_transparency_on"),
                "Task Complexity High": ("if_task_complexity_changed", "set_task_complexity_high"),
                "Reliability Low": ("if_reliability_changed", "set_reliability_low"),
                "Control Mode Manual": ("if_control_mode_changed", "set_control_mode_manual")
            }

            for label, (changed_flag, attribute) in attribute_mapping.items():
                changed_value = getattr(self.selected_waypoint, changed_flag)
                changed_text = "✓" if changed_value else ""
                self.waypoint_labels[f"{label}_changed"].config(text=changed_text, command=lambda cf=changed_flag, attr=attribute: self.toggle_changed_flag(cf, attr))

                attribute_value = getattr(self.selected_waypoint, attribute)
                button_text = f"{label}: {str(attribute_value)}" if changed_value else f"{label}: None"
                button_color = "forest green" if attribute_value else "brown3"
                if not changed_value:
                    button_color = "black"
                self.waypoint_labels[label].config(text=button_text, command=lambda cf=changed_flag, attr=attribute: self.toggle_attribute(cf, attr), fg=button_color)
        else:
            for label in self.waypoint_labels.values():
                label.config(text="", command=None)

    def toggle_changed_flag(self, changed_flag, attribute):
        setattr(self.selected_waypoint, changed_flag, not getattr(self.selected_waypoint, changed_flag))
        self.update_waypoint_info()
        self.route_saved = False

    def toggle_attribute(self, changed_flag, attribute):
        setattr(self.selected_waypoint, attribute, not getattr(self.selected_waypoint, attribute))
        if changed_flag is not None:
            setattr(self.selected_waypoint, changed_flag, True)
        self.update_waypoint_info()
        self.route_saved = False

def main():
    root = tk.Tk()
    root.title("Map Visualizer")

    waypoint_handler = WaypointHandler(WAYPOINT_FILE)
    visualizer = MapVisualizer(root, MAP_IMAGE_PATH, waypoint_handler)

    def update():
        visualizer.draw()
        root.after(10, update)

    def on_key_press(event):
        if event.char == 'q':
            root.quit()
        elif event.char == 'c':
            visualizer.clear_route()
        elif event.char == 's':
            visualizer.save_route(ROUTE_FILE)

    root.bind("<Key>", on_key_press)
    update()
    root.mainloop()

if __name__:
    main()
