import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

# Constants
IMAGE_OFFSET_X = 900
IMAGE_OFFSET_Y = -700
SCALE = 0.0253
WAYPOINT_SIZE = 10
MAP_IMAGE_PATH = 'test_map.png'
WAYPOINT_FILE = 'WayPointLog.csv'
ROUTE_FILE = 'route.txt'
FONT = ('Arial', 12)

class Waypoint:
    def __init__(self, index, name, x, y, next_waypoint=None, is_self_report=False, transparency=False,
                 task_complexity=False, reliability=False, control_mode=False):
        self.index = index
        self.name = name
        self.x = x
        self.y = y
        self.next_waypoint = next_waypoint
        self.is_self_report = is_self_report
        self.transparency = transparency
        self.task_complexity = task_complexity
        self.reliability = reliability
        self.control_mode = control_mode

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
        self.min_x, self.max_x, self.min_y, self.max_y = self.compute_bounds()
        self.offset_x, self.offset_y = self.compute_offsets()

        self.canvas = tk.Canvas(self.master, width=self.map_image.shape[1], height=self.map_image.shape[0])
        self.canvas.pack(side=tk.LEFT)

        self.options_frame = tk.Frame(self.master)
        self.options_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.create_option_widgets()
        self.update_waypoint_info()

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

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
        
        button_labels = ["Self-Report", "Transparency", "Task Complexity", "Reliability", "Control Mode"]
        for label in button_labels:
            self.waypoint_labels[label] = tk.Button(button_frame, text=f"{label}: ", font=FONT, relief=tk.GROOVE, padx=5, pady=2)
            self.waypoint_labels[label].pack(anchor=tk.W, fill=tk.X, pady=2)

    def compute_bounds(self):
        min_x = min(waypoint.x for waypoint in self.waypoint_handler.waypoints) + IMAGE_OFFSET_X
        max_x = max(waypoint.x for waypoint in self.waypoint_handler.waypoints)
        min_y = min(waypoint.y for waypoint in self.waypoint_handler.waypoints) + IMAGE_OFFSET_Y
        max_y = max(waypoint.y for waypoint in self.waypoint_handler.waypoints)
        return min_x, max_x, min_y, max_y

    def compute_offsets(self):
        offset_x = (self.map_image.shape[1] - (self.max_x - self.min_x) * SCALE) / 2
        offset_y = (self.map_image.shape[0] - (self.max_y - self.min_y) * SCALE) / 2
        return offset_x, offset_y

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

    def draw_waypoints(self, image):
        for waypoint in self.waypoint_handler.waypoints:
            scaled_x = int((waypoint.x - self.min_x) * SCALE + self.offset_x)
            scaled_y = int((waypoint.y - self.min_y) * SCALE + self.offset_y)
            color = (0, 0, 255) if waypoint == self.last_waypoint else (0, 255, 0)
            cv2.rectangle(image, (scaled_x - WAYPOINT_SIZE, scaled_y - WAYPOINT_SIZE),
                        (scaled_x + WAYPOINT_SIZE, scaled_y + WAYPOINT_SIZE), color, -1)

            if waypoint == self.selected_waypoint:
                cv2.rectangle(image, (scaled_x - WAYPOINT_SIZE - 2, scaled_y - WAYPOINT_SIZE - 2),
                            (scaled_x + WAYPOINT_SIZE + 2, scaled_y + WAYPOINT_SIZE + 2), (255, 0, 0), 2)

    def draw_routes(self, image):
        for start, end in self.route:
            start_x = int((start.x - self.min_x) * SCALE + self.offset_x)
            start_y = int((start.y - self.min_y) * SCALE + self.offset_y)
            end_x = int((end.x - self.min_x) * SCALE + self.offset_x)
            end_y = int((end.y - self.min_y) * SCALE + self.offset_y)
            cv2.arrowedLine(image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)

    def draw_hover_info(self, image):
        if self.hovered_waypoint is not None:
            text_pos = list(self.mouse_pos)
            text_pos[0] += 20
            text_pos[1] += 10
            cv2.putText(image, f"{self.hovered_waypoint.index}: {self.hovered_waypoint.name}", tuple(text_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

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
            scaled_x = int((waypoint.x - self.min_x) * SCALE + self.offset_x)
            scaled_y = int((waypoint.y - self.min_y) * SCALE + self.offset_y)
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
            scaled_x = int((waypoint.x - self.min_x) * SCALE + self.offset_x)
            scaled_y = int((waypoint.y - self.min_y) * SCALE + self.offset_y)
            if abs(x - scaled_x) < WAYPOINT_SIZE and abs(y - scaled_y) < WAYPOINT_SIZE:
                self.hovered_waypoint = waypoint
                break

    def clear_route(self):
        self.route.clear()
        self.route_mode = False
        self.last_waypoint = None
        self.route_saved = False

    def save_route(self, filename):
        route_details = []
        for start, end in self.route:
            route_details.append(f"{start.index}, {start.next_waypoint}, {start.is_self_report}, {start.transparency}, {start.task_complexity}, {start.reliability}, {start.control_mode}, {end.index}\n")
        route_details.append(f"{end.index}, {end.next_waypoint}, {end.is_self_report}, {end.transparency}, {end.task_complexity}, {end.reliability}, {end.control_mode}, None\n")

        with open(filename, 'w') as file:
            for details in route_details:
                file.write(details)
        self.route_saved = True

    def update_waypoint_info(self):
        if self.selected_waypoint is not None:
            self.waypoint_labels["Index"].config(text=f"Index: {self.selected_waypoint.index}")
            self.waypoint_labels["Name"].config(text=f"Name: {self.selected_waypoint.name}")
            self.waypoint_labels["X"].config(text=f"X: {self.selected_waypoint.x}")
            self.waypoint_labels["Y"].config(text=f"Y: {self.selected_waypoint.y}")
            self.waypoint_labels["Next Waypoint"].config(text=f"Next Waypoint: {self.selected_waypoint.next_waypoint}")

            attribute_mapping = {
                "Self-Report": "is_self_report",
                "Transparency": "transparency",
                "Task Complexity": "task_complexity",
                "Reliability": "reliability",
                "Control Mode": "control_mode"
            }

            for label, attribute in attribute_mapping.items():
                attribute_value = getattr(self.selected_waypoint, attribute)
                button_text = f"{label}: {attribute_value}"
                button_color = "green" if attribute_value else "black"
                self.waypoint_labels[label].config(text=button_text, command=lambda attr=attribute: self.toggle_attribute(attr), fg=button_color)
        else:
            for label in self.waypoint_labels.values():
                label.config(text="", command=None)

    def toggle_attribute(self, attribute):
        setattr(self.selected_waypoint, attribute, not getattr(self.selected_waypoint, attribute))
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

if __name__ == '__main__':
    main()
