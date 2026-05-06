import tkinter as tk
from flask import Flask
from flaskext.mysql import MySQL

characters = []
current_user_id = None


def init_db():
    app = Flask(__name__)
    mysql = MySQL()
    app.config['MYSQL_DATABASE_USER'] = 'root'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'root_password'
    app.config['MYSQL_DATABASE_DB'] = 'character_manager'
    app.config['MYSQL_DATABASE_HOST'] = 'localhost'
    mysql.init_app(app)
    conn = mysql.connect()
    cursor = conn.cursor()
    return cursor, conn


def close_db(cursor, conn):
    conn.commit()
    cursor.close()
    conn.close()


def fetch_characters(user_id):
    cursor, conn = init_db()
    try:
        cursor.execute("SELECT * FROM characters WHERE user_id = %s", (user_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        close_db(cursor, conn)


def fetch_all_types():
    cursor, conn = init_db()
    try:
        cursor.execute("SELECT type_name FROM character_type")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching types: {e}")
        return []
    finally:
        close_db(cursor, conn)


def fetch_all_worlds():
    cursor, conn = init_db()
    try:
        cursor.execute("SELECT world_name FROM worlds")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching worlds: {e}")
        return []
    finally:
        close_db(cursor, conn)


def fetch_worlds_for_type(type_name):
    cursor, conn = init_db()
    try:
        cursor.execute(
            "SELECT world_name FROM world_characters WHERE character_type = %s",
            (type_name,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        close_db(cursor, conn)


def fetch_types_for_world(world_name):
    cursor, conn = init_db()
    try:
        cursor.execute(
            "SELECT character_type FROM world_characters WHERE world_name = %s",
            (world_name,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        close_db(cursor, conn)


def make_linked_dropdowns(parent, all_types, all_worlds,
                          initial_type=None, initial_world=None):

    type_var  = tk.StringVar(value=initial_type  or (all_types[0]  if all_types  else ""))
    world_var = tk.StringVar(value=initial_world or (all_worlds[0] if all_worlds else ""))


    type_frame = tk.Frame(parent)
    type_frame.pack(pady=5, padx=10)
    tk.Label(type_frame, text="Type:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
    tk.OptionMenu(type_frame, type_var, *all_types).pack(side=tk.LEFT, padx=5)


    world_frame = tk.Frame(parent)
    world_frame.pack(pady=5, padx=10)
    tk.Label(world_frame, text="World:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
    tk.OptionMenu(world_frame, world_var, *all_worlds).pack(side=tk.LEFT, padx=5)


    warn_var = tk.StringVar(value="")
    tk.Label(parent, textvariable=warn_var, fg="orange",
             wraplength=340, justify=tk.LEFT).pack(padx=10, pady=(0, 4))

    def _check_compatibility(*_):
        t = type_var.get()
        w = world_var.get()
        if not t or not w:
            warn_var.set("")
            return
        allowed_worlds = fetch_worlds_for_type(t)
        allowed_types  = fetch_types_for_world(w)
        if allowed_worlds and w not in allowed_worlds:
            warn_var.set(
                f"Warning: '{w}' is not available for type '{t}'. "
                "Please choose a compatible combination."
            )
        elif allowed_types and t not in allowed_types:
            warn_var.set(
                f"Warning: type '{t}' cannot exist in world '{w}'. "
                "Please choose a compatible combination."
            )
        else:
            warn_var.set("")

    type_var.trace_add("write",  _check_compatibility)
    world_var.trace_add("write", _check_compatibility)
    _check_compatibility()

    def is_compatible():
        return warn_var.get() == ""

    return type_var, world_var, is_compatible


def refresh_character_page():
    for widget in root.winfo_children():
        widget.destroy()
    if current_user_id:
        setup_character_page(current_user_id)


def edit_character(character_id, details_window):
    global characters

    character = next((c for c in characters if c["id"] == character_id), None)
    if not character:
        return

    edit_window = tk.Toplevel()
    edit_window.title("Edit Character")

    plain_fields = [
        ("Name",       "character_name"),
        ("Armor",      "armor"),
        ("Weapon",     "weapon"),
        ("Inventory",  "inventory"),
        ("Attributes", "attributes"),
    ]


    
    entries = {}
    for label_text, key in plain_fields:
        frame = tk.Frame(edit_window)
        frame.pack(pady=5, padx=10)
        tk.Label(frame, text=f"{label_text}:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(frame, width=30)
        entry.pack(side=tk.LEFT, padx=5)
        entry.insert(0, str(character.get(key, "")))
        entries[key] = entry

    frame = tk.Frame(edit_window)
    frame.pack(pady=5, padx=10)
    age_label = tk.Label(frame, text="Age:", width=12, anchor=tk.W)
    age_label.pack(side=tk.LEFT, padx=5)
    age_entry = tk.Spinbox(frame, from_=0, to=1000, width=5)
    age_entry.pack(side=tk.LEFT, padx=5)
    age_entry.delete(0, tk.END)
    age_entry.insert(0, str(character.get("age", 0)))

    all_types  = fetch_all_types()
    all_worlds = fetch_all_worlds()

    type_var, world_var, is_compatible = make_linked_dropdowns(
        edit_window, all_types, all_worlds,
        initial_type=character.get("type_name"),
        initial_world=character.get("world_name"),
    )

    err_label = tk.Label(edit_window, text="", fg="red", wraplength=340)
    err_label.pack(padx=10)

    def save_changes():
        if not is_compatible():
            err_label.config(text="Cannot save: resolve the Type / World incompatibility first.")
            return
        err_label.config(text="")

        updated = {key: entries[key].get() for _, key in plain_fields}
        updated["age"]        = age_entry.get()
        updated["type_name"]  = type_var.get()
        updated["world_name"] = world_var.get()

        cursor, conn = init_db()
        try:
            cursor.execute(
                "UPDATE characters SET character_name=%s, armor=%s, weapon=%s, "
                "inventory=%s, age=%s, attributes=%s, world_name=%s, type_name=%s "
                "WHERE character_id=%s",
                (
                    updated["character_name"], updated["armor"],    updated["weapon"],
                    updated["inventory"],      updated["age"],      updated["attributes"],
                    updated["world_name"],     updated["type_name"], character_id,
                ),
            )
        except Exception as e:
            err_label.config(text=f"Error saving character: {e}")
            return
        finally:
            close_db(cursor, conn)

        character.update(updated)
        edit_window.destroy()
        details_window.destroy()
        refresh_character_page()

    tk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=10)


def delete_character(character_id, details_window):
    global characters

    cursor, conn = init_db()
    try:
        cursor.execute("DELETE FROM characters WHERE character_id = %s", (character_id,))
    except Exception as e:
        tk.Label(root, text=f"Error deleting character: {e}").pack(pady=10)
    finally:
        close_db(cursor, conn)

    characters = [c for c in characters if c["id"] != character_id]
    details_window.destroy()
    refresh_character_page()


def show_character_details(index):
    character = characters[index]
    details_window = tk.Toplevel()
    details_window.title(f"{character['character_name']}'s Details")

    details_text = (
        f"Name:       {character['character_name']}\n"
        f"Armor:      {character.get('armor', '')}\n"
        f"Weapon:     {character.get('weapon', '')}\n"
        f"Inventory:  {character['inventory']}\n"
        f"Age:        {character['age']}\n"
        f"Attributes: {character['attributes']}\n"
        f"World:      {character['world_name']}\n"
        f"Type:       {character['type_name']}\n"
    )

    tk.Label(details_window, text=details_text, justify=tk.LEFT).pack(padx=20, pady=20)
    tk.Button(details_window, text="Edit Character",
              command=lambda: edit_character(character['id'], details_window)).pack(pady=10)
    tk.Button(details_window, text="Delete Character",
              command=lambda: delete_character(character['id'], details_window)).pack(pady=10)


def open_create_character(user_id):
    create_window = tk.Toplevel()
    create_window.title("Create New Character")

    plain_fields = [
        ("Name",       "character_name"),
        ("Armor",      "armor"),
        ("Weapon",     "weapon"),
        ("Inventory",  "inventory"),
        ("Attributes", "attributes"),
    ]

    entries = {}

    for label, key in plain_fields:
        frame = tk.Frame(create_window)
        frame.pack(pady=5, padx=10)
        tk.Label(frame, text=label + ":", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(frame, width=30)
        entry.pack(side=tk.LEFT, padx=5)
        entries[key] = entry

    frame = tk.Frame(create_window)
    frame.pack(pady=5, padx=10)

    age_label = tk.Label(frame, text="Age:", width=12, anchor=tk.W)
    age_label.pack(side=tk.LEFT, padx=5)
    age_entry = tk.Spinbox(frame, from_=0, to=1000, width=5)
    age_entry.pack(side=tk.LEFT, padx=5)
    all_types  = fetch_all_types()
    all_worlds = fetch_all_worlds()
    type_var, world_var, is_compatible = make_linked_dropdowns(create_window, all_types, all_worlds)

    err_label = tk.Label(create_window, text="", fg="red", wraplength=340)
    err_label.pack(padx=10)

    def save_character():
        if not is_compatible():
            err_label.config(text="Cannot save: resolve the Type / World incompatibility first.")
            return
        err_label.config(text="")

        character_data = {key: entries[key].get() for _, key in plain_fields}
        character_data["age"]        = age_entry.get()
        character_data["type_name"]  = type_var.get()
        character_data["world_name"] = world_var.get()

        cursor, conn = init_db()
        try:
            cursor.execute(
                "INSERT INTO characters "
                "(user_id, character_name, armor, weapon, inventory, age, attributes, world_name, type_name) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    user_id,
                    character_data["character_name"], character_data["armor"],
                    character_data["weapon"],         character_data["inventory"],
                    character_data["age"],            character_data["attributes"],
                    character_data["world_name"],     character_data["type_name"],
                )
            )

            create_window.destroy()
            root.after(500, refresh_character_page)
        except Exception as e:
            err_label.config(text=f"Error: {e}")
        finally:
            close_db(cursor, conn)

    tk.Button(create_window, text="Save Character", command=save_character).pack(pady=10)


def setup_character_page(user_id):
    global characters, current_user_id
    current_user_id = user_id
    characters.clear()

    tk.Label(root, text="Character Page").pack(pady=20)

    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    character_list = tk.Listbox(root, yscrollcommand=scrollbar.set)
    character_list.pack(fill=tk.X, expand=tk.YES, pady=10)
    scrollbar.config(command=character_list.yview)

    character_list.bind(
        "<Double-Button-1>",
        lambda event: show_character_details(character_list.curselection()[0])
            if character_list.curselection() else None
    )

    for character in fetch_characters(user_id):
        characters.append({
            "id":             character[0],
            "character_name": character[2],
            "armor":          character[3],
            "weapon":         character[4],
            "inventory":      character[5],
            "age":            character[6],
            "attributes":     character[7],
            "world_name":     character[8],
            "type_name":      character[9],
        })
        character_list.insert(
            tk.END,
            f"Name: {character[2]} | Age: {character[6]} | Type: {character[9]} | World: {character[8]}"
        )

    tk.Button(root, text="Create New Character",
              command=lambda: open_create_character(user_id)).pack(pady=10)


def register_user(email, username, top_ref):
    cursor, conn = init_db()
    try:
        cursor.execute("INSERT INTO users (email, username) VALUES (%s, %s)", (email, username))
        top_ref.destroy()
    except Exception as e:
        tk.Label(root, text=f"Error: {e}").pack(pady=10)
        top_ref.destroy()
    finally:
        close_db(cursor, conn)


def login_user(username, top_ref):
    cursor, conn = init_db()
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user:
            top_ref.destroy()
            for widget in root.winfo_children():
                widget.destroy()
            setup_character_page(user[0])
        else:
            tk.Label(root, text="No user with that username exists.").pack(pady=10)
            top_ref.destroy()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_db(cursor, conn)


def sign_up():
    top = tk.Toplevel()
    top.title("Sign Up")
    tk.Label(top, text="Sign up for an account!").pack(pady=20)
    tk.Label(top, text="Email:").pack(pady=10)
    email_input = tk.Entry(top)
    email_input.pack(pady=10)
    tk.Label(top, text="Username:").pack(pady=10)
    username_input = tk.Entry(top)
    username_input.pack(pady=10)
    tk.Button(
        top, text="Sign Up",
        command=lambda: register_user(email_input.get() or None, username_input.get() or None, top)
    ).pack(pady=10)


def log_in():
    top = tk.Toplevel()
    top.title("Log In")
    tk.Label(top, text="Log in to your account!").pack(pady=20)
    tk.Label(top, text="Username:").pack(pady=10)
    username_input = tk.Entry(top)
    username_input.pack(pady=10)
    tk.Button(
        top, text="Log In",
        command=lambda: login_user(username_input.get() or None, top)
    ).pack(pady=10)


def setup_login_page():
    tk.Label(root, text="Welcome to Character Manager!").pack(pady=20)
    tk.Button(root, text="Sign Up", command=sign_up).pack(pady=10)
    tk.Button(root, text="Log In", command=log_in).pack(pady=10)


root = tk.Tk()
root.title("Character Manager")
root.geometry("400x300")

setup_login_page()

root.mainloop()