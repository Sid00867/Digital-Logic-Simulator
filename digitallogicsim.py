import pygame
import copy
import os
import dill
from pygame import gfxdraw
import platform
import ctypes

SAVE_FILE = "objects.pkl"

# ______________________________________________________________MIGHT CAUSE PROBLEMS

def get_screen_size():
    try:
        if platform.system() == 'Windows':
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        else:
            # For non-Windows systems, default to standard size
            return 1920, 1080
    except:
        return 1920, 1080

screen_width, screen_height = get_screen_size()
# Calculate diagonal size in pixels
diagonal_pixels = (screen_width**2 + screen_height**2)**0.5
# Approximate conversion (assuming 96 DPI)
diagonal_inches = diagonal_pixels / 96

print(diagonal_inches)

# Use smaller dimensions for screens 15.5 inches or less
if diagonal_inches <= 18.4:
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 720
else:
    WINDOW_WIDTH = 1500
    WINDOW_HEIGHT = 900


# ______________________________________________________________
    
DESIGN_AREA_HEIGHT = WINDOW_HEIGHT - 100  # Height of the design area (excluding component bar)

# Colors
BACKGROUND_COLOR = (20, 20, 30)
PANEL_COLOR = (40, 40, 60)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 160, 210)
BUTTON_TEXT_COLOR = (240, 240, 240)
COMPONENT_COLOR = (60, 70, 90)
COMPONENT_BORDER_COLOR = (100, 120, 150)
COMPONENT_TEXT_COLOR = (220, 230, 240)
INPUT_OFF_COLOR = (220, 80, 80)
INPUT_ON_COLOR = (80, 220, 80)
WIRE_COLOR = (180, 180, 220)
TEMP_WIRE_COLOR = (200, 200, 255)

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Logic Circuit Designer")
clock = pygame.time.Clock()

# Load fonts
title_font = pygame.font.Font(None, 42)
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
input_text = ""
input_active = False

# Button properties - positioned relative to window size
clear_button_rect = pygame.Rect(WINDOW_WIDTH - 200, 20, 80, 40)
build_button_rect = pygame.Rect(WINDOW_WIDTH - 100, 20, 80, 40)
input_box_rect = pygame.Rect(WINDOW_WIDTH - 400, 20, 180, 40)

class StorageSystem:

    @staticmethod
    def save_object(obj):
        data = []

        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "rb") as file:
                    data = dill.load(file)
            except (EOFError, FileNotFoundError):
                pass  # Ignore if file is empty

        data.append(obj)  

        with open(SAVE_FILE, "wb") as file:
            dill.dump(data, file)

    @staticmethod
    def load_objects():
        if not os.path.exists(SAVE_FILE):
            return []

        try:
            with open(SAVE_FILE, "rb") as file:
                return dill.load(file)
        except (EOFError, FileNotFoundError):
            return []  




class Component:
    def __init__(self, inputs, outputs, name, isDefaultLogicGate=False, DefaultLogic=None, isBuiltComponent=False, sceneComp = None, sceneConnect = None, extremes = None) -> None:
        self.inputs = [ConnectionPoint(isReciever=False, componentClass=self) for _ in range(inputs)]
        self.outputs = [ConnectionPoint(isReciever=True, componentClass=self) for _ in range(outputs)]
        self.name = name
        self.dragging = False  # Track dragging state
        self.hasRecievedAllInput = False
        self.isDefaultLogicGate = isDefaultLogicGate
        self.DefaultLogic = DefaultLogic
        self.isBuiltComponent = isBuiltComponent
        self.sceneComp = sceneComp
        self.sceneConnect = sceneConnect
        self.extremes = extremes
    

    def __deepcopy__(self, memo):
        new_component = Component(
                len(self.inputs), 
                len(self.outputs), 
                self.name, 
                isDefaultLogicGate=self.isDefaultLogicGate,  # ✅ Copy this
                DefaultLogic=self.DefaultLogic,  # ✅ Copy this
                isBuiltComponent = self.isBuiltComponent,
                sceneComp = self.sceneComp,
                sceneConnect = self.sceneConnect,
                extremes = self.extremes
            )
        return new_component

    def RunComponent(self):
        if self.isDefaultLogicGate:
            component_outputs = [output == 1 for output in self.DefaultLogic(self.inputs)]
            for output, statetoset in zip(self.outputs, component_outputs):
                output.State = statetoset
        
        if self.isBuiltComponent:
            for input, extreme_input in zip(self.inputs, self.extremes[0]):
                extreme_input.outputs[0].State = input.State
            self.PropogateCircuit()
            for output, extreme_output in zip(self.outputs, self.extremes[1]):
                output.State = extreme_output.inputs[0].State

        return self.outputs        

    def PropogateCircuit(self):
    # input_connections = []
        for connection in self.sceneConnect:
            if connection[0].componentClass.name == "Input":
                # input_connections.append(connection)
                self.RecursivePropogation(connection[1])
                # print(connection[0].State)

    # use node linking method

    def RecursivePropogation(self,startnode):
        num = 1
        for connection in self.sceneConnect:
            if connection[1] == startnode:
                if connection[0].State:
                    num *= 0
                else:
                    num *= 1

        startnode.State = num == 0  
            
        if startnode.componentClass.name == "Output":
            # print(startnode.State)
            return
        startnode.componentClass.RunComponent()

        # for now getting outputs directly, in the future have to include input to output logic somehow
        for output in startnode.componentClass.outputs:
            for connection in self.sceneConnect:
                if connection[0] == output:
                    self.RecursivePropogation(connection[1])    
        
    def SetPosition(self, X , Y):
        self.X = X
        self.Y = Y

        if self.name == "Input" or self.name == "Output":
            self.height = 25
            self.width = 65  
        else:
            self.height = 60 + 15 * max(len(self.inputs), len(self.outputs))
            self.width = 100  

        self.inputpos = []
        for index, input in enumerate(self.inputs):
            self.inputpos.append(input.SetPosition(self.X, self.Y + (20 * (index + 1))))

        self.outputpos = []
        for index, output in enumerate(self.outputs):
            self.outputpos.append(output.SetPosition(self.X + self.width, self.Y + (20 * (index + 1))))    

        return [(self.X, self.Y), (self.width, self.height)]    

class ConnectionPoint:
    def __init__(self, isReciever, componentClass) -> None:
        self.isReciever = isReciever
        self.componentClass = componentClass
        self.State = False

    def SetPosition(self, X , Y):
        self.X = X
        self.Y = Y
        return (X, Y)    

# -------------------------------------------

BuiltComponents = {
    "Input": Component(0, 1, "Input"),
    "Output": Component(1, 0, "Output"),
    "AND": Component(2, 1, "AND", isDefaultLogicGate=True, DefaultLogic=lambda inputs: [inputs[0].State * inputs[1].State]),
    "OR": Component(2, 1, "OR", isDefaultLogicGate=True, DefaultLogic=lambda inputs: [inputs[0].State + inputs[1].State - (inputs[0].State * inputs[1].State)]),
    "NOT": Component(1, 1, "NOT", isDefaultLogicGate=True, DefaultLogic=lambda inputs: [1 - inputs[0].State])
}

for comp in StorageSystem.load_objects():
    BuiltComponents[comp.name] = comp

# BuiltComponents[input_text] = Component(len(extremes[0]), len(extremes[1]), input_text, isBuiltComponent=True, sceneComp=SceneComponents, sceneConnect=connections,extremes=extremes) #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

SceneComponents = []
selected_component = None  # Track which component is being dragged
offset_x, offset_y = 0, 0  # Offset to prevent snap-to-center issues

connections = []

extremes = [[],[]]
# -------------------------------------------

def draw_rounded_rect(surface, rect, color, radius=15):
    """Draw a rounded rectangle"""
    rect = pygame.Rect(rect)
    color = pygame.Color(*color)
    alpha = color.a
    color.a = 0
    pos = rect.topleft
    rect.topleft = 0, 0
    rectangle = pygame.Surface(rect.size, pygame.SRCALPHA)
    
    circle = pygame.Surface([min(rect.size) * 3] * 2, pygame.SRCALPHA)
    pygame.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
    circle = pygame.transform.smoothscale(circle, [radius * 2] * 2)
    
    radius = min(radius, rect.width // 2, rect.height // 2)
    
    for corner, pos in (
            (0, (0, 0)),
            (1, (rect.width - radius, 0)),
            (2, (rect.width - radius, rect.height - radius)),
            (3, (0, rect.height - radius))
    ):
        rectangle.blit(circle, pos)
    
    rectangle.fill((0, 0, 0), rect.inflate(-radius * 2, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius * 2))
    
    rectangle.fill(color, special_flags=pygame.BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)
    
    # surface.blit(rectangle, rect.topleft)

def draw_button(surface, rect, text, color, hover_color=None, text_color=BUTTON_TEXT_COLOR, border_radius=10):
    """Draw a button with hover effect"""
    mouse_pos = pygame.mouse.get_pos()
    if hover_color and rect.collidepoint(mouse_pos):
        draw_rounded_rect(surface, rect, hover_color, border_radius)
    else:
        draw_rounded_rect(surface, rect, color, border_radius)
    
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def renderComponentBar():
    # Draw component panel
    pygame.draw.rect(screen, PANEL_COLOR, (0, DESIGN_AREA_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - DESIGN_AREA_HEIGHT))
    
    # Calculate button width based on window width and number of components
    component_count = len(BuiltComponents.keys())
    button_width = min(100, (WINDOW_WIDTH - 20) / (component_count + 1))
    button_spacing = (WINDOW_WIDTH - (button_width * component_count)) / (component_count + 1)
    
    # Draw component buttons
    for i, key in enumerate(BuiltComponents.keys()):
        button_x = button_spacing * (i + 1) + button_width * i
        button = pygame.Rect(button_x, DESIGN_AREA_HEIGHT + 10, button_width, 80)
        draw_rounded_rect(screen, button, BUTTON_COLOR, 10)
        text = small_font.render(key, True, BUTTON_TEXT_COLOR)
        text_rect = text.get_rect(center=(button.x + button.width / 2, button.y + button.height / 2))
        screen.blit(text, text_rect)

    # Draw control buttons
    draw_button(screen, clear_button_rect, "Clear", (180, 60, 60), (220, 80, 80))
    draw_button(screen, build_button_rect, "Build", (60, 180, 60), (80, 220, 80))
    
    # Draw input box
    if input_active:
        pygame.draw.rect(screen, (80, 80, 100), input_box_rect, 0, 5)
    pygame.draw.rect(screen, (150, 150, 180), input_box_rect, 2, 5)
    
    # Draw input text
    input_surface = font.render(input_text, True, BUTTON_TEXT_COLOR)
    screen.blit(input_surface, (input_box_rect.x + 10, input_box_rect.y + 10))
    
    # Draw title
    title = title_font.render("Logic Circuit Designer", True, (200, 200, 255))
    screen.blit(title, (20, 20))

def renderSceneComponents():
    for component in SceneComponents:
        # Draw component body with rounded corners
        draw_rounded_rect(screen, (component.X, component.Y, component.width, component.height), 
                         COMPONENT_COLOR, 10)
        pygame.draw.rect(screen, COMPONENT_BORDER_COLOR, 
                        (component.X, component.Y, component.width, component.height), 2, 10)
        
        # Draw component name
        text = small_font.render(component.name, True, COMPONENT_TEXT_COLOR)
        text_rect = text.get_rect(center=(component.X + component.width / 2, component.Y + component.height / 2))
        screen.blit(text, text_rect)

        # Draw connection points
        for input_point in component.inputs:
            color = INPUT_OFF_COLOR if not input_point.State else INPUT_ON_COLOR
            # Draw a filled circle with anti-aliasing
            gfxdraw.aacircle(screen, input_point.X, input_point.Y, 6, color)
            gfxdraw.filled_circle(screen, input_point.X, input_point.Y, 6, color)
            
        for output_point in component.outputs:
            color = INPUT_OFF_COLOR if not output_point.State else INPUT_ON_COLOR
            gfxdraw.aacircle(screen, output_point.X, output_point.Y, 6, color)
            gfxdraw.filled_circle(screen, output_point.X, output_point.Y, 6, color)

def renderConnections():
    for connection in connections:
        # Draw a smooth line for connections
        start_pos = (connection[0].X, connection[0].Y)
        end_pos = (connection[1].X, connection[1].Y)
        
        # If there are bend points in this connection
        if len(connection) > 2:
            # Draw from start to first bend point
            points = []
            steps = 20
            first_bend = connection[2]
            control_x = (start_pos[0] + first_bend[0]) / 2
            
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * first_bend[0]
                y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * (start_pos[1] + first_bend[1])/2 + t**2 * first_bend[1]
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.aalines(screen, WIRE_COLOR, False, points, 2)
            
            # Draw between bend points
            for i in range(2, len(connection) - 1):
                start_bend = connection[i]
                end_bend = connection[i + 1]
                
                points = []
                control_x = (start_bend[0] + end_bend[0]) / 2
                
                for j in range(steps + 1):
                    t = j / steps
                    x = (1-t)**2 * start_bend[0] + 2*(1-t)*t * control_x + t**2 * end_bend[0]
                    y = (1-t)**2 * start_bend[1] + 2*(1-t)*t * (start_bend[1] + end_bend[1])/2 + t**2 * end_bend[1]
                    points.append((int(x), int(y)))
                
                if len(points) > 1:
                    pygame.draw.aalines(screen, WIRE_COLOR, False, points, 2)
            
            # Draw from last bend point to end
            last_bend = connection[-1]
            
            points = []
            control_x = (last_bend[0] + end_pos[0]) / 2
            
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**2 * last_bend[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                y = (1-t)**2 * last_bend[1] + 2*(1-t)*t * (last_bend[1] + end_pos[1])/2 + t**2 * end_pos[1]
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.aalines(screen, WIRE_COLOR, False, points, 2)
                
            # Draw bend points as small circles
            for i in range(2, len(connection)):
                point = connection[i]
                gfxdraw.aacircle(screen, point[0], point[1], 4, WIRE_COLOR)
                gfxdraw.filled_circle(screen, point[0], point[1], 4, WIRE_COLOR)
        else:
            # Calculate control points for a bezier curve
            control_x = (start_pos[0] + end_pos[0]) / 2
            
            # Draw a bezier curve
            points = []
            steps = 20
            for i in range(steps + 1):
                t = i / steps
                # Quadratic bezier curve
                x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * (start_pos[1] + end_pos[1])/2 + t**2 * end_pos[1]
                points.append((int(x), int(y)))
            
            # Draw the curve
            if len(points) > 1:
                pygame.draw.aalines(screen, WIRE_COLOR, False, points, 2)

def PropogateCircuit():
    # input_connections = []
    for connection in connections:
        if connection[0].componentClass.name == "Input":
            # input_connections.append(connection)
            RecursivePropogation(connection[1])

    # use node linking method

def RecursivePropogation(startnode):
    num = 1
    for connection in connections:
        if connection[1] == startnode:
            if connection[0].State:
                num *= 0
            else:
                num *= 1

    startnode.State = num == 0  
         
    if startnode.componentClass.name == "Output":
        return
    startnode.componentClass.RunComponent()
    
    # for now getting outputs directly, in the future have to include input to output logic somehow
    for output in startnode.componentClass.outputs:
        for connection in connections:
            if connection[0] == output:
                RecursivePropogation(connection[1])


running = True
tempwire = False
tempwirepos = [[],[]]
wire_bend_points = []  

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if tempwire and event.type == pygame.MOUSEMOTION:
            if event.pos:
                tempwirepos[1] = [max(0, min(event.pos[0], WINDOW_WIDTH)), max(0, min(event.pos[1], WINDOW_HEIGHT))]
            else:
                tempwirepos[1] = [0, 0]

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Calculate button positions dynamically
            component_count = len(BuiltComponents.keys())
            button_width = min(100, (WINDOW_WIDTH - 20) / (component_count + 1))
            button_spacing = (WINDOW_WIDTH - (button_width * component_count)) / (component_count + 1)
            
            for i, (key, component) in enumerate(BuiltComponents.items()):
                button_x = button_spacing * (i + 1) + button_width * i
                button = pygame.Rect(button_x, DESIGN_AREA_HEIGHT + 10, button_width, 80)
                if button.collidepoint(event.pos):
                    component_deepcopy = copy.deepcopy(component)
                    if component_deepcopy.name == "Input":
                        # Position inputs on the left side in sets of 4sets of 4
                        input_count = sum(1 for comp in SceneComponents if comp.name == "Input")
                        row = input_count // 4  # Determine which row (0-indexed)
                        col = input_count % 4   # Determine position within row (0-3)
                        # Add extra vertical space between 
                        y_position = 70 + (row * 50 * 4) + (row * 30) + (col * 50)
                        component_deepcopy.SetPosition(50, y_position)
                    elif component_deepcopy.name == "Output":
                        # Position outputs on the right side in sets of 4
                        output_count = sum(1 for comp in SceneComponents if comp.name == "Output")
                        row = output_count // 4  # Determine which row (0-indexed)
                        col = output_count % 4   # Determine position within row (0-3)
                        # Add extra vertical space between sets of 4
                        y_position = 70 + (row * 50 * 4) + (row * 30) + (col * 50)
                        component_deepcopy.SetPosition(WINDOW_WIDTH - 150, y_position)
                    else:
                        # Other components in the center
                        component_deepcopy.SetPosition(WINDOW_WIDTH // 2, DESIGN_AREA_HEIGHT // 2)
                    SceneComponents.append(component_deepcopy)

            # Handle dragging
            for component in SceneComponents:
                if (component.X <= event.pos[0] <= component.X + component.width and component.Y <= event.pos[1] <= component.Y + component.height) and not tempwire:
                    selected_component = component
                    component.dragging = True
                    offset_x = event.pos[0] - component.X  # Store offset to prevent jump
                    offset_y = event.pos[1] - component.Y

            for component in SceneComponents:
                for input_point in component.inputs:
                    if (input_point.X - 10 <= event.pos[0] <= input_point.X + 10 and input_point.Y - 10 <= event.pos[1] <= input_point.Y + 10) and tempwire:
                        if [tempwirepos[0][0],input_point] not in connections:
                            # Create a connection with the wire bend points
                            connection_data = [tempwirepos[0][0], input_point]
                            # Add all bend points to the connection
                            for bend_point in wire_bend_points:
                                connection_data.append(bend_point)
                            connections.append(connection_data)
                            tempwirepos = [[],[]]
                            tempwire = False
                            wire_bend_points = []  # Reset bend points for next wire
                for output_point in component.outputs:
                    if (output_point.X - 10 <= event.pos[0] <= output_point.X + 10 and output_point.Y - 10 <= event.pos[1] <= output_point.Y + 10) and not tempwire:
                        # print("halleljah")
                        tempwire = True
                        tempwirepos[0] = [output_point]
                        tempwirepos[1] = [event.pos[0], event.pos[1]]
                        wire_bend_points = []  # Reset bend points for new wire

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
            # Check if we're on a component's input
            on_connection_point = False
            for component in SceneComponents:
                if (component.X <= event.pos[0] <= component.X + component.width and component.Y <= event.pos[1] <= component.Y + component.height) and component.name == "Input":
                    component.outputs[0].State = not component.outputs[0].State
                    on_connection_point = True
                    break
                
                # Check if we're on any connection point
                for input_point in component.inputs:
                    if (input_point.X - 10 <= event.pos[0] <= input_point.X + 10 and input_point.Y - 10 <= event.pos[1] <= input_point.Y + 10):
                        on_connection_point = True
                        break
                for output_point in component.outputs:
                    if (output_point.X - 10 <= event.pos[0] <= output_point.X + 10 and output_point.Y - 10 <= event.pos[1] <= output_point.Y + 10):
                        on_connection_point = True
                        break
                if on_connection_point:
                    break

            if tempwire and not on_connection_point:
                bend_point = (event.pos[0], event.pos[1])
                wire_bend_points.append(bend_point)

                tempwirepos[1] = [event.pos[0], event.pos[1]]

        # Update position while dragging
        elif event.type == pygame.MOUSEMOTION:
            if selected_component and selected_component.dragging:
                old_x, old_y = selected_component.X, selected_component.Y
                # Constrain component position to design area
                new_x = max(0, min(event.pos[0] - offset_x, WINDOW_WIDTH - selected_component.width))
                new_y = max(0, min(event.pos[1] - offset_y, DESIGN_AREA_HEIGHT - selected_component.height))
                selected_component.SetPosition(new_x, new_y)
                
                # Update wire bend points when components move
                dx = selected_component.X - old_x
                dy = selected_component.Y - old_y
                
                # Update connections for this component
                for connection in connections:
                    # If this component is the source of the connection
                    if connection[0].componentClass == selected_component:
                        # If there are bend points, update the first one
                        if len(connection) > 2:
                            first_bend = connection[2]
                            connection[2] = (first_bend[0] + dx, first_bend[1] + dy)
                    
                    # If this component is the target of the connection
                    if connection[1].componentClass == selected_component:
                        # If there are bend points, update the last one
                        if len(connection) > 2:
                            last_bend = connection[-1]
                            connection[-1] = (last_bend[0] + dx, last_bend[1] + dy)

        # Stop dragging when mouse button is released
        elif event.type == pygame.MOUSEBUTTONUP:
            if selected_component:
                selected_component.dragging = False
                selected_component = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if clear_button_rect.collidepoint(event.pos):
                SceneComponents = []
                connections = []
                extremes = [[],[]]
                

            elif build_button_rect.collidepoint(event.pos):
                extremes[0] = sorted([component for component in SceneComponents if component.name == "Input"], key=lambda component: component.Y)
                extremes[1] = sorted([component for component in SceneComponents if component.name == "Output"], key=lambda component: component.Y)

                BuiltComponents[input_text] = Component(len(extremes[0]), len(extremes[1]), input_text, isBuiltComponent=True, sceneComp=SceneComponents, sceneConnect=connections,extremes=extremes) #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                StorageSystem.save_object(BuiltComponents[input_text])
                SceneComponents = []
                connections = []
                extremes = [[],[]]


            elif input_box_rect.collidepoint(event.pos):
                input_active = not input_active
            else:
                input_active = False
        
        if event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_RETURN:
                print("Input submitted:", input_text)
                input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode        


    screen.fill(BACKGROUND_COLOR)
    
    # Draw grid for better visual reference
    grid_size = 20
    for x in range(0, WINDOW_WIDTH, grid_size):
        pygame.draw.line(screen, (40, 40, 50), (x, 0), (x, DESIGN_AREA_HEIGHT), 1)
    for y in range(0, DESIGN_AREA_HEIGHT, grid_size):
        pygame.draw.line(screen, (40, 40, 50), (0, y), (WINDOW_WIDTH, y), 1)

    if tempwire:
        # Draw temporary wire with bezier curve and bend points
        if wire_bend_points:
            # Draw segments from start to each bend point
            start_pos = (tempwirepos[0][0].X, tempwirepos[0][0].Y)
            
            # Draw from start to first bend point
            points = []
            steps = 20
            end_pos = wire_bend_points[0]
            control_x = (start_pos[0] + end_pos[0]) / 2
            
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * (start_pos[1] + end_pos[1])/2 + t**2 * end_pos[1]
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.aalines(screen, TEMP_WIRE_COLOR, False, points, 2)
            
            # Draw between bend points
            for i in range(len(wire_bend_points) - 1):
                start_pos = wire_bend_points[i]
                end_pos = wire_bend_points[i + 1]
                
                points = []
                control_x = (start_pos[0] + end_pos[0]) / 2
                
                for j in range(steps + 1):
                    t = j / steps
                    x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                    y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * (start_pos[1] + end_pos[1])/2 + t**2 * end_pos[1]
                    points.append((int(x), int(y)))
                
                if len(points) > 1:
                    pygame.draw.aalines(screen, TEMP_WIRE_COLOR, False, points, 2)
            
            # Draw from last bend point to current mouse position
            start_pos = wire_bend_points[-1]
            end_pos = (tempwirepos[1][0], tempwirepos[1][1])
            
            points = []
            control_x = (start_pos[0] + end_pos[0]) / 2
            
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * (start_pos[1] + end_pos[1])/2 + t**2 * end_pos[1]
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.aalines(screen, TEMP_WIRE_COLOR, False, points, 2)
                
            # Draw bend points as small circles
            for point in wire_bend_points:
                gfxdraw.aacircle(screen, point[0], point[1], 4, TEMP_WIRE_COLOR)
                gfxdraw.filled_circle(screen, point[0], point[1], 4, TEMP_WIRE_COLOR)
        else:
            # Draw simple wire without bend points
            start_pos = (tempwirepos[0][0].X, tempwirepos[0][0].Y)
            end_pos = (tempwirepos[1][0], tempwirepos[1][1])
            
            # Calculate control points
            control_x = (start_pos[0] + end_pos[0]) / 2
            
            # Draw a bezier curve
            points = []
            steps = 20
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * (start_pos[1] + end_pos[1])/2 + t**2 * end_pos[1]
                points.append((int(x), int(y)))
            
            # Draw the curve
            if len(points) > 1:
                pygame.draw.aalines(screen, TEMP_WIRE_COLOR, False, points, 2)

    renderComponentBar()
    renderSceneComponents()
    renderConnections()
    PropogateCircuit()     

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
