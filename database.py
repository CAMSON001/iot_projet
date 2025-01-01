import sqlite3

def initialize_db():
    connection = sqlite3.connect("smart_dumbbell.db")
    cursor = connection.cursor()

    # Création de la table users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,  -- Changement du type à TEXT
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Création de la table objects
    cursor.execute('''
        CREATE TABLE objects (
        id TEXT PRIMARY KEY, -- Identifiant unique pour chaque objet
        name TEXT,
        state TEXT
);
    ''')

    # Création de la table objects
    cursor.execute('''
        CREATE TABLE users_objects (
            user_id TEXT, -- ID de l'utilisateur
            object_id TEXT, -- ID de l'objet
            PRIMARY KEY (user_id, object_id), -- Clé primaire composite
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
        );
    ''')

    connection.commit()
    connection.close()

# Appeler cette fonction pour initialiser la base
initialize_db()
