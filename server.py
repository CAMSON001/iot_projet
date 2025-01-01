from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, Response
import sqlite3
import uuid
import threading
import time
import socket
import json


# Liste des objets existants et nouveaux
existing_objects = []

FILE_PATH = 'new_objects.json'

def load_new_objects():
    try:
        with open(FILE_PATH, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_new_objects(objects):
    if not isinstance(objects, list):
        raise ValueError("Les données à sauvegarder doivent être une liste.")
    with open(FILE_PATH, 'w') as file:
        json.dump(objects, file)

# Chargement des objets connectés
def load_connected_objects():
    with open('connected_object.json', 'r') as file:
        return json.load(file)


# Charger la liste des objets existants au démarrage
new_objects_list = load_new_objects()

# Code Flask existant pour gérer les routes...


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Nécessaire pour gérer les sessions
DATABASE = 'smart_dumbbell.db'

# Fonction pour générer un identifiant aléatoire
def generate_random_id():
    return str(uuid.uuid4())

# Fonction pour se connecter à la base de données
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return g.db

# Ferme la connexion à la base de données après chaque requête
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Route pour la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/use_object/<object_id>', methods=['POST'])
def use_object(object_id):
    connected_objects = load_connected_objects()

    # Trouver l'objet correspondant dans le fichier JSON
    target_object = next((obj for obj in connected_objects if obj['id'] == object_id), None)
    if target_object:
        try:
            # Établir une connexion avec le socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_object['ip'], target_object['port']))
                s.sendall(b"use")  # Envoyer la commande "use"
                # Attendre la réponse
                response = s.recv(1024).decode('utf-8')
                if response == "ok":
                    # Mettre à jour l'état de l'objet à "Using"
                    print(response)
                    return render_template('workout.html')
        except (socket.error, Exception) as e:
            print(f"Erreur de connexion avec l'objet {target_object['name']}: {e}")
    
    return redirect(url_for('home'))

@app.route('/delete_object/<int:object_id>', methods=['POST'])
def delete_object(object_id):
    # Logique pour supprimer l'objet
    global user_objects
    user_objects = [obj for obj in user_objects if obj['id'] != object_id]
    return redirect(url_for('home'))

# Données fictives pour les performances d'exercice (juste pour simuler l'exercice en temps réel)
workout_data = {}

@app.route('/handle_use', methods=['POST'])
def handle_use():
    data = request.get_json()  # Récupérer les données envoyées en JSON
    #print(data)
    if not data:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    # Mettre à jour les données d'exercice en temps réel
    workout_data.update(data)

    return jsonify({"status": "success", "message": "Données reçues"}), 200


@app.route('/workout')
def workout():
    def generate():
        """Générer le flux d'événements pour afficher les mises à jour des données"""
        while True:
            # Diffuser les données d'exercice en temps réel
            yield f"data: {json.dumps(workout_data)}\n\n"
            time.sleep(1)  # Attendre 1 seconde avant la prochaine mise à jour

    # Retourner la page HTML avec le flux SSE
    return Response(generate(), content_type='text/event-stream')



@app.route('/home')
def home():
    # Vérifie si l'utilisateur est connecté via la session
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))  # Si non connecté, rediriger vers la page de login

    # Récupérer les informations de l'utilisateur
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        return "Utilisateur non trouvé", 404  # Si l'utilisateur n'existe pas, afficher une erreur

    # Données fictives pour les performances hebdomadaires
    weekly_performance = {
        'week_1': {'repetitions': 50, 'avg_duration': 15},
        'week_2': {'repetitions': 60, 'avg_duration': 17},
        'week_3': {'repetitions': 55, 'avg_duration': 16},
        'week_4': {'repetitions': 70, 'avg_duration': 18}
    }

   # Récupérer les objets associés à l'utilisateur
    cursor.execute('''
        SELECT o.id, o.name, o.state 
        FROM objects o 
        JOIN users_objects uo ON o.id = uo.object_id 
        WHERE uo.user_id = ?
    ''', (user_id,))
    user_objects = cursor.fetchall()


    # Nouvelle liste d'objets (new_objects_list)
    new_ob = []
    new_ob.extend(new_objects_list)
    # Récupérer les messages de succès/erreur
    success_message = request.args.get('success')
    error_message = request.args.get('error')

    return render_template('home.html', user=user, 
                           weekly_performance=weekly_performance, 
                           user_objects=user_objects, 
                           new_ob=new_ob,
                           success_message=success_message,
                           error_message=error_message)


@app.route('/add_object', methods=['POST'])
def add_object():
    entered_id = request.form.get('entered_id')
    selected_object_id = request.form.get('selected_object_id')

    if not entered_id or not selected_object_id:
        return redirect(url_for('home', error="Veuillez entrer un ID et choisir un objet."))

    if entered_id != selected_object_id:
        return redirect(url_for('home', error="Les ID ne correspondent pas."))

    new_objects_list = load_new_objects()
    selected_object = next((obj for obj in new_objects_list if obj['id'] == selected_object_id), None)

    if not selected_object:
        return redirect(url_for('home', error="L'objet sélectionné n'existe pas."))

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    # Vérifier si l'objet est déjà associé à l'utilisateur
    cursor.execute('SELECT * FROM users_objects WHERE user_id = ? AND object_id = ?', (user_id, selected_object_id))
    if cursor.fetchone():
        return redirect(url_for('home', error="Cet objet est déjà enregistré pour cet utilisateur."))

    # Insérer l'objet dans `users_objects`
    cursor.execute('INSERT INTO users_objects (user_id, object_id) VALUES (?, ?)', (user_id, selected_object_id))

    # Insérer l'objet dans `objects` si ce n'est pas encore le cas
    cursor.execute('SELECT * FROM objects WHERE id = ?', (selected_object_id,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO objects (id, name, state) VALUES (?, ?, ?)', 
                       (selected_object_id, selected_object['name'], 'off'))

    db.commit()

    # Mettre à jour la liste des nouveaux objets
    new_objects_list = [obj for obj in new_objects_list if obj['id'] != selected_object_id]
    save_new_objects(new_objects_list)

    return redirect(url_for('home', success="L'objet a été ajouté avec succès."))



@app.route('/handle_info', methods=['POST'])
def handle_info():
    data = request.get_json()
    if not data or 'id' not in data or 'name' not in data or 'weight' not in data:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    new_objects_list = load_new_objects()
    
    # Vérifie si l'objet existe déjà
    if any(obj['id'] == data['id'] for obj in new_objects_list):
        return jsonify({"status": "info", "message": "L'objet existe déjà."}), 200
    
    # Ajouter l'objet et sauvegarder
    new_objects_list.append(data)
    save_new_objects(new_objects_list)

    # Charger les objets déjà connectés depuis connected_object.json
    connected_objects = load_connected_objects()

    # Vérifier si l'objet existe déjà dans connected_object.json
    if any(obj['id'] == data['id'] for obj in connected_objects):
        return jsonify({"status": "info", "message": "L'objet existe déjà."}), 200

    # Ajouter l'objet et sauvegarder dans connected_object.json
    connected_objects.append(data)
    with open('connected_object.json', 'w') as file:
        json.dump(connected_objects, file)


    return jsonify({"status": "success", "message": "Objet ajouté avec succès."}), 200



# Route pour la page de création de compte
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        user_id = generate_random_id()  # Générer un ID unique
        name = request.form.get('name')
        age = request.form.get('age')
        username = request.form.get('username')
        password = request.form.get('password')

        # Insertion dans la base de données SQLite
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute('''
                INSERT INTO users (id, name, age, username, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, age, username, password))
            db.commit()
        except sqlite3.IntegrityError:
            return "Ce nom d'utilisateur existe déjà. Essayez un autre."

        # Redirection après enregistrement
        return redirect(url_for('index'))

    return render_template('register.html')

# Route pour la connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Vérification dans la base de données
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        if user:
            # Stocker les infos utilisateur pour la session
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')  # Récupération de l'ID utilisateur de la session
    if not user_id:
        return redirect(url_for('login'))  # Si l'utilisateur n'est pas connecté, rediriger vers la page de login

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()  # Récupère l'utilisateur à partir de son ID

    if not user:
        return "Utilisateur non trouvé", 404  # Si l'utilisateur n'est pas trouvé, afficher une erreur

    # Données fictives pour les performances
    stats = {
        'repetitions': 50,
        'avg_duration': 15,
    }

    # Récupérer les objets connectés de l'utilisateur
    cursor.execute('SELECT * FROM objects WHERE user_id = ?', (user_id,))
    objects = cursor.fetchall()  # Liste des objets de l'utilisateur

    new_ob = new_ob + new_objects_list

    # Passer les informations au template
    return render_template('dashboard.html', user=user, new_ob=new_ob, objects=objects)



if __name__ == '__main__':
    app.run(debug=True)
