import tkinter as tk
import threading
import socket
import pyautogui
import pickle
import zlib
from PIL import Image, ImageTk
from pynput import keyboard, mouse

# Define constants
HOST = '10.0.0.231'  # Change this to your host IP
PORT = 12345

# Global variables
is_host = None
root = None
client_socket = None
focused = False  # Flag to track if the tkinter window is focused
captured_events = []

def send_screen_and_receive_inputs():
    global captured_events, focused, client_socket
    if not is_host:
        while True:
            # Capture the screenshot
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.resize((1280, 720))
            #screenshot = zlib.compress(pickle.dumps(screenshot.tobytes()))  # Convert to bytes
            #screenshot = pickle.dumps(screenshot.tobytes())
            screenshot = screenshot.tobytes()

            # Send the screenshot
            client_socket.send(screenshot)

            #data = b''
            #while len(data) < 4096:
            #    packet = client_socket.recv(4096)
            #    if not packet:
            #        break
            #    data += packet

            #user_inputs = zlib.decompress(data)
            #user_inputs = pickle.loads(user_inputs)
            #execute_user_inputs(user_inputs)
    else:
        with keyboard.Listener(on_press=on_key, on_release=on_key_release) as key_listener, mouse.Listener(on_move=on_move, on_click=on_click) as mouse_listener:
            while True:
                if focused:
                    # Send captured user inputs when the tkinter window is focused
                    user_inputs = zlib.compress(pickle.dumps(captured_events))
                    client_socket.send(user_inputs)

                # Clear the captured events list
                captured_events = []

                # Receive and display the client's screen
                data = b''
                while len(data) < (1920 * 1080 * 3):  # Assuming Full HD resolution
                    packet = client_socket.recv(4096)
                    if not packet:
                        break
                    data += packet

                #data = client_socket.recv()

                #screenshot_bytes = zlib.decompress(data)
                #try:
                #screenshot_bytes = pickle.loads(data)
                screenshot_bytes = data
                screenshot = Image.frombytes('RGB', (1280, 720), screenshot_bytes)  # Reconstruct the image
                tkimage = ImageTk.PhotoImage(image=screenshot)
                canvas.create_image(0, 0, image=tkimage, anchor=tk.NW)
                root.update_idletasks()
                root.update()
                #except:
                #    pass

def execute_user_inputs(user_inputs):
    # Execute user inputs using pyautogui
    for event in user_inputs:
        if event[0] == 'keyboard':
            if event[2] == 'press':
                pyautogui.keyDown(event[1])
            else:
                pyautogui.keyUp(event[1])
        elif event[0] == 'mouse':
            if event[4] == 'press':
                pyautogui.mouseDown(event[3])
            else:
                pyautogui.mouseUp(event[3])

def on_focus_in(event):
    global focused
    focused = True

def on_focus_out(event):
    global focused
    focused = False

def on_key(key):
    try:
        captured_events.append(('keyboard', key.char, 'press'))
    except AttributeError:
        if key == keyboard.Key.esc:
            return False
        captured_events.append(('keyboard', str(key), 'press'))

def on_key_release(key):
    captured_events.append(('keyboard', str(key), 'release'))

def on_move(x, y):
    if focused:
        captured_events.append(('mouse', x, y))

def on_click(x, y, button, pressed):
    if focused:
        action = 'press' if pressed else 'release'
        captured_events.append(('mouse', x, y, button, action))

def main():
    global is_host, root, client_socket, canvas, focused

    is_host = input("Are you the host? (y/n): ").lower() == 'y'

    if is_host:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print("Waiting for a client to connect...")
        client_socket, client_address = server_socket.accept()
        print(f"Connected to {client_address}")

        root = tk.Tk()
        root.title("Screen Sharing")
        canvas = tk.Canvas(root, width=1920, height=1080)
        canvas.pack()

        # Bind focus events to the tkinter window
        root.bind("<FocusIn>", on_focus_in)
        root.bind("<FocusOut>", on_focus_out)

        send_receive_thread = threading.Thread(target=send_screen_and_receive_inputs)
        send_receive_thread.start()

        root.mainloop()
    else:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        send_receive_thread = threading.Thread(target=send_screen_and_receive_inputs)
        send_receive_thread.start()

if __name__ == "__main__":
    main()
