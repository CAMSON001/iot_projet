import random
import time
import requests
import math
import socket
import threading
from datetime import datetime

# Configuration
object_info = {
    "id": "kgsghhoaNhzlkln",
    "name": "Dumbells Pro",
    "weight" : 25,
    "addr" : "192.168.11.104",
    "port" : 12345
}

EXERCISE = 'shoulder_press'  # Can be changed to other exercises later
WEIGHT = 10  # kg
REPS_PER_SET = 8
TOTAL_SETS = 3
REP_DURATION = 3.0  # seconds

SERVER_ADDRESS = ('192.168.11.104', 12345)  # Address and port for the socket server

# Starting positions (in meters)
LEFT_SHOULDER_POS = (-0.2, 1.4, 0)   # x, y, z
RIGHT_SHOULDER_POS = (0.2, 1.4, 0)   # x, y, z

def calculate_positions(progress, going_up):
    """
    Calculate positions for both dumbbells and elbows based on exercise progress
    progress: 0 to 1 representing movement progress
    going_up: True if movement is upward, False if downward
    """
    if going_up:
        height_factor = math.sin(progress * math.pi/2)  # Smooth upward movement
    else:
        height_factor = 1 - math.sin(progress * math.pi/2)  # Smooth downward movement
    
    # Small random variations for natural movement
    variation = 0.03
    
    # Calculate dumbbell positions
    left_dumbbell = {
        'x': LEFT_SHOULDER_POS[0] + random.uniform(-variation, variation),
        'y': LEFT_SHOULDER_POS[1] + (0.4 * height_factor),  # 0.4m total vertical movement
        'z': LEFT_SHOULDER_POS[2] + random.uniform(-variation, variation)
    }
    
    right_dumbbell = {
        'x': RIGHT_SHOULDER_POS[0] + random.uniform(-variation, variation),
        'y': RIGHT_SHOULDER_POS[1] + (0.4 * height_factor),  # 0.4m total vertical movement
        'z': RIGHT_SHOULDER_POS[2] + random.uniform(-variation, variation)
    }
    
    # Calculate elbow positions (slightly below and behind dumbbells)
    left_elbow = {
        'x': left_dumbbell['x'] - 0.1,
        'y': left_dumbbell['y'] - 0.25 - (0.1 * height_factor),  # Elbow moves less than dumbbell
        'z': left_dumbbell['z'] - 0.1
    }
    
    right_elbow = {
        'x': right_dumbbell['x'] + 0.1,
        'y': right_dumbbell['y'] - 0.25 - (0.1 * height_factor),  # Elbow moves less than dumbbell
        'z': right_dumbbell['z'] - 0.1
    }
    
    return {
        'left_dumbbell': {k: round(v, 3) for k, v in left_dumbbell.items()},
        'right_dumbbell': {k: round(v, 3) for k, v in right_dumbbell.items()},
        'left_elbow': {k: round(v, 3) for k, v in left_elbow.items()},
        'right_elbow': {k: round(v, 3) for k, v in right_elbow.items()}
    }

def generate_workout_data(current_set, total_reps, positions):
    """Generate a single data point during the exercise"""
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'exercise': EXERCISE,
        'weight': WEIGHT,
        'current_set': current_set,
        'current_rep': (total_reps % REPS_PER_SET) + 1,
        'total_reps': total_reps,
        'sensors': {
            'left_dumbbell': positions['left_dumbbell'],
            'right_dumbbell': positions['right_dumbbell'],
            'left_elbow': positions['left_elbow'],
            'right_elbow': positions['right_elbow']
        },
        'temp': round(random.uniform(20, 30), 1),
        'battery': random.randint(60, 100)
    }

def send_to_server(url, data):
    
    """Send data to the local server"""
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending data: {e}")
        return False
#To send client info    
def send_info(info_object):
    send_to_server("http://localhost:5000/handle_info",info_object)

def use_object():
    """Run the main simulation loop"""
    print(f"Starting {EXERCISE} simulation")
    print(f"Weight: {WEIGHT}kg")
    print(f"Sets: {TOTAL_SETS}, Reps per set: {REPS_PER_SET}")
    print("Press Ctrl+C to stop")
    
    current_set = 1
    total_reps = 0
    
    try:
        while current_set <= TOTAL_SETS:
            # Up movement
            for i in range(10):
                progress = i / 9
                positions = calculate_positions(progress, going_up=True)
                data = generate_workout_data(current_set, total_reps, positions)
                print(f"\rSet {current_set}, Rep {(total_reps % REPS_PER_SET) + 1}, "
                      f"Height: {positions['left_dumbbell']['y']:.2f}m", end='')
                send_to_server("http://localhost:5000/handle_use",data)
                time.sleep(REP_DURATION / 20)
            
            # Down movement
            for i in range(10):
                progress = i / 9
                positions = calculate_positions(progress, going_up=False)
                data = generate_workout_data(current_set, total_reps, positions)
                print(f"\rSet {current_set}, Rep {(total_reps % REPS_PER_SET) + 1}, "
                      f"Height: {positions['left_dumbbell']['y']:.2f}m", end='')
                send_to_server("http://localhost:5000/handle_use",data)
                time.sleep(REP_DURATION / 20)
            
            total_reps += 1
            print()  # New line after each rep
            
            # Check if set is complete
            if total_reps % REPS_PER_SET == 0:
                current_set += 1
                if current_set <= TOTAL_SETS:
                    print(f"\nRest between sets (30 seconds)...")
                    time.sleep(30)
        
        print("\nWorkout complete!")
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")        
    

def handle_client(client_socket):
    """Handle a client connection"""
    with client_socket as sock:
        try:
            # Recevoir le message du client
            message = sock.recv(1024).decode('utf-8').strip()

            if message == "use":
                print("Received 'use' command. Starting workout...")
                # Répondre au client avec "ok"
                sock.sendall(b"ok")
                # Lancer une action côté serveur si nécessaire
                threading.Thread(target=use_object).start() 

            elif message.startswith("act"):
                print(f"Received 'act' command with message: {message[4:]}")
                # Répondre au client si nécessaire
                sock.sendall(b"action acknowledged")
            
            else:
                print(f"Unknown command received: {message}")
                # Répondre avec un message d'erreur au client
                sock.sendall(b"unknown command")
        
        except Exception as e:
            print(f"Error while handling client: {e}")

def start_server():
    """Start the socket server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(SERVER_ADDRESS)
        server.listen(5)
        print(f"Server listening on {SERVER_ADDRESS}")
        while True:
            client_socket, addr = server.accept()
            print(f"Connection accepted from {addr}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    send_info(object_info)
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
