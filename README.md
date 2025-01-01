# iot_projet
# Smart Dumbbell Simulation and Server

This project simulates a smart dumbbell connected to a server that processes real-time workout data and provides an interface for interaction. The dumbbell mimics an IoT device that tracks movement, logs workout data, and interacts with users through a Flask web interface and a socket server.

## Features

1. **IoT Device Simulation:**
   - Simulates a smart dumbbell performing shoulder press exercises.
   - Tracks the positions of dumbbells and elbows during each repetition.
   - Sends real-time data to a local server.

2. **Server Communication:**
   - A socket server listens for commands to start or interact with the dumbbell.
   - Flask API endpoints handle user interactions and data processing.

3. **Workout Tracking:**
   - Logs workout data including set, repetition, weight, and sensor details.
   - Generates realistic movement variations for natural simulation.

4. **Web Interface:**
   - Flask-based UI to display and manage connected objects.
   - Allows starting workouts, viewing logs, and managing objects.

5. **Data Persistence:**
   - Stores user objects and connected devices in JSON and SQLite databases.

## Installation

### Prerequisites

- Python 3.8+
- Flask
- Requests
- SQLite3

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/CAMSON001/iot_project.git
   cd iot_project.
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create the SQLite database:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('smart_dumbbell.db'); conn.close()"
   ```

4. Ensure required JSON files are present:
   - `new_objects.json` (for new device management)
   - `connected_object.json` (for connected objects)

   If not, create them with an empty list:
   ```json
   []
   ```

5. Run the server:
   ```bash
   python server.py
   ```

6. Start the simulation:
   ```bash
   python IoT_object.py
   ```

## Usage

### Flask Web Interface
- Access the web interface at `http://localhost:5000`.
- Use the interface to manage devices and initiate workouts.

### Socket Communication
- The server listens for commands such as:
  - `use`: Starts the workout simulation.
  - `act <message>`: Sends an action message to the server.

### API Endpoints
- `/handle_use` (POST): Receives workout data.
- `/use_object/<object_id>` (POST): Starts using a specific object.
- `/delete_object/<object_id>` (POST): Deletes an object.

## Project Structure

```
smart-dumbbell/
├── server.py                # Flask server
├── IoT_object.py         # Dumbbell simulation script
├── templates/            # HTML templates for Flask
├── static/               # Static files (CSS, JS, images)
├── connected_object.json # JSON file for connected devices
├── new_objects.json      # JSON file for new devices
├── smart_dumbbell.db     # SQLite database
├── database.py           #database script

```

## Simulation Workflow

1. The simulation script sends periodic data during a shoulder press workout.
2. Data includes dumbbell and elbow positions, temperature, and battery status.
3. The server processes the data and updates the workout state in real time.

## Known Issues
- Ensure the IP address and port in `object_info` match your local setup.
- Check file permissions for JSON and database files.

## Future Improvements
- Add support for multiple exercise types.
- Implement a mobile app interface for real-time feedback.
- Enhance security for API and socket communication.

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit your changes: `git commit -m 'Add feature name'`.
4. Push to the branch: `git push origin feature-name`.
5. Submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
