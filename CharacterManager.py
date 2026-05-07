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
        sql_command = (
            "SELECT c.character_id, c.user_id, c.character_name, c.armor, c.weapon, "
            "c.inventory, c.age, c.world_name, c.type_name, "
            "GROUP_CONCAT(a.attribute SEPARATOR ', ') "
            "FROM characters c "
            "LEFT JOIN character_attributes a ON c.character_id = a.character_id "
            "WHERE c.user_id = %s "
            "GROUP BY c.character_id"

        )
        cursor.execute(sql_command, (user_id,))
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


def fetch_attributes_for_character(character_id):
    cursor, conn = init_db()
    try:
        cursor.execute(
            "SELECT attribute FROM character_attributes WHERE character_id = %s",
            (character_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching attributes: {e}")
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

def get_all_world_counts(world_name=None):
    cursor, conn = init_db()
    try:
        cursor.execute("""
            SELECT GetCharacterCount(%s)
            FROM worlds
        """, (world_name,)) 
        result = cursor.fetchone()
        return result[0]
    except Exception as e:
        print(f"Error fetching world counts: {e}")
        return {}
    finally:
        close_db(cursor, conn)

def make_linked_dropdowns(parent, all_types, all_worlds,
                          initial_type=None, initial_world=None):
    
    world_counts = get_all_world_counts()

    display_worlds = [
        f"{w} ({get_all_world_counts(w)})" for w in all_worlds
    ]

    display_to_real = {
        f"{w} ({get_all_world_counts(w)})": w
        for w in all_worlds
    }

    type_var = tk.StringVar(value=initial_type or (all_types[0] if all_types else ""))

    if initial_world:
        initial_display_world = f"{initial_world} {world_counts.get(initial_world, 0)}"
    else:
        initial_display_world = display_worlds[0] if display_worlds else ""

    world_var = tk.StringVar(value=initial_display_world)

    type_frame = tk.Frame(parent)
    type_frame.pack(pady=5, padx=10)
    tk.Label(type_frame, text="Type:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
    tk.OptionMenu(type_frame, type_var, *all_types).pack(side=tk.LEFT, padx=5)

    world_frame = tk.Frame(parent)
    world_frame.pack(pady=5, padx=10)
    tk.Label(world_frame, text="World:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
    tk.OptionMenu(world_frame, world_var, *display_worlds).pack(side=tk.LEFT, padx=5)

    warn_var = tk.StringVar(value="")
    tk.Label(parent, textvariable=warn_var, fg="orange",
             wraplength=340, justify=tk.LEFT).pack(padx=10, pady=(0, 4))

    def _check_compatibility(*_):
        t = type_var.get()

        w_display = world_var.get()
        w = display_to_real.get(w_display, w_display)

        if not t or not w:
            warn_var.set("")
            return

        allowed_worlds = fetch_worlds_for_type(t)
        allowed_types = fetch_types_for_world(w)

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

    type_var.trace_add("write", _check_compatibility)
    world_var.trace_add("write", _check_compatibility)
    _check_compatibility()

    def is_compatible():
        return warn_var.get() == ""

    def get_selected_world():
        return display_to_real.get(world_var.get(), world_var.get())

    return type_var, world_var, get_selected_world, is_compatible


def refresh_character_page():
    for widget in root.winfo_children():
        widget.destroy()
    if current_user_id:
        setup_character_page(current_user_id)

def open_character_form(mode, user_id=None, character=None, details_window=None):
    window = tk.Toplevel()
    window.title("Create New Character" if mode == 'create' else "Edit Character")

    plain_fields = [
        ("Name",       "character_name"),
        ("Armor",      "armor"),
        ("Weapon",     "weapon"),
        ("Inventory",  "inventory"),
    ]

    entries = {}
    for label, key in plain_fields:
        frame = tk.Frame(window)
        frame.pack(pady=5, padx=10)
        tk.Label(frame, text=label + ":", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(frame, width=30)
        entry.pack(side=tk.LEFT, padx=5)
        if mode == 'edit':
            entry.insert(0, str(character.get(key, "")))
        entries[key] = entry

    frame = tk.Frame(window)
    frame.pack(pady=5, padx=10)
    age_label = tk.Label(frame, text="Age:", width=12, anchor=tk.W)
    age_label.pack(side=tk.LEFT, padx=5)
    age_entry = tk.Spinbox(frame, from_=0, to=1000, width=5)
    age_entry.pack(side=tk.LEFT, padx=5)
    if mode == 'edit':
        age_entry.delete(0, tk.END)
        age_entry.insert(0, str(character.get("age", 0)))

    attr_frame = tk.Frame(window)
    attr_frame.pack(pady=5, padx=10, fill=tk.X)
    tk.Label(attr_frame, text="Attributes:", width=12, anchor=tk.NW).pack(side=tk.LEFT, padx=5, pady=5)
    attrs_container = tk.Frame(attr_frame)
    attrs_container.pack(side=tk.LEFT, padx=5)

    attribute_entries = []

    def add_attribute_entry(value=""):
        entry = tk.Entry(attrs_container, width=30)
        entry.pack(pady=2)
        entry.insert(0, value)

        def _on_enter(event, ent=entry):
            if not ent.get().strip():
                return
            if ent is attribute_entries[-1]:
                add_attribute_entry("")

        entry.bind("<Return>", _on_enter)
        attribute_entries.append(entry)
        return entry

    if mode == 'edit':
        for attr in fetch_attributes_for_character(character['id']):
            add_attribute_entry(attr)
        add_attribute_entry("")
    else:
        add_attribute_entry("")

    all_types  = fetch_all_types()
    all_worlds = fetch_all_worlds()
    initial_type = character.get("type_name") if mode == 'edit' else None
    initial_world = character.get("world_name") if mode == 'edit' else None
    type_var, world_var, get_selected_world, is_compatible = make_linked_dropdowns(
        window, all_types, all_worlds,
        initial_type=initial_type,
        initial_world=initial_world,
    )

    err_label = tk.Label(window, text="", fg="red", wraplength=340)
    err_label.pack(padx=10)

    def save():
        if not is_compatible():
            err_label.config(text="Cannot save: resolve the Type / World incompatibility first.")
            return
        err_label.config(text="")

        data = {key: entries[key].get() for _, key in plain_fields}
        attrs = [entry.get().strip() for entry in attribute_entries if entry.get().strip()]
        data["attributes"] = "; ".join(attrs)
        data["age"]        = age_entry.get()
        data["type_name"]  = type_var.get()
        data["world_name"] = get_selected_world()

        cursor, conn = init_db()
        try:
            if mode == 'create':
                cursor.execute(
                    "INSERT INTO characters "
                    "(user_id, character_name, armor, weapon, inventory, age, world_name, type_name) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        user_id,
                        data["character_name"], data["armor"],
                        data["weapon"], data["inventory"],
                        data["age"], data["world_name"], data["type_name"],
    
                    )
                )
                cursor.execute("SELECT LAST_INSERT_ID()")
                character_id = cursor.fetchone()[0]
                for attr in attrs:
                    cursor.execute(
                        "INSERT INTO character_attributes (character_id, attribute) VALUES (%s, %s)",
                        (character_id, attr)
                    )
                window.destroy()
                root.after(500, refresh_character_page)
            else:
                cursor.execute(
                    "UPDATE characters SET character_name=%s, armor=%s, weapon=%s, "
                    "inventory=%s, age=%s, world_name=%s, type_name=%s "
                    "WHERE character_id=%s",
                    (
                        data["character_name"], data["armor"],data["weapon"],
                        data["inventory"], data["age"],
                        data["world_name"], data["type_name"], character['id']
                    ),
                )
                cursor.execute(
                    "DELETE FROM character_attributes WHERE character_id = %s",
                    (character['id'],)
                )
                for attr in attrs:
                    cursor.execute(
                        "INSERT INTO character_attributes (character_id, attribute) VALUES (%s, %s)",
                        (character['id'], attr)
                    )
                character.update(data)
                window.destroy()
                if details_window:
                    details_window.destroy()
                refresh_character_page()
        except Exception as e:
            err_label.config(text=f"Error: {type(e).__name__}: {e}")
        finally:
            close_db(cursor, conn)

    tk.Button(window, text="Save Character" if mode == 'create' else "Save Changes", command=save).pack(pady=10)

def edit_character(character_id, details_window):
    global characters
    character = next((c for c in characters if c["id"] == character_id), None)
    if not character:
        return
    open_character_form('edit', character=character, details_window=details_window)


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
    open_character_form('create', user_id=user_id)

def setup_admin_view():
    admin_window = tk.Toplevel()
    admin_window.title("Admin Panel")
    tk.Label(admin_window, text="Admin Panel - Manage Types and Worlds").pack(pady=20)
    cursor, conn = init_db()
    try:
        cursor.execute("""
            SELECT u.username, c.character_name, c.world_name, c.type_name
            FROM users u
            JOIN characters c ON u.user_id = c.user_id
            ORDER BY u.username
        """)
        results = cursor.fetchall()
        if results:
            for username, character_name, world_name, type_name in results:
                tk.Label(
                    admin_window,
                    text=f"User: {username} | Character: {character_name} | World: {world_name} | Type: {type_name}"
                ).pack(pady=5)
        else:
            tk.Label(admin_window, text="No characters found in the database.").pack(pady=10)
    
        close_db(cursor, conn)

    except Exception as e:
        tk.Label(admin_window, text=f"Error loading admin data: {e}").pack(pady=10)




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

    if user_id == 1:
        admin_button = tk.Button(root, text="Admin Panel", command=lambda: setup_admin_view())
        admin_button.pack(pady=10)

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
            "world_name":     character[7],
            "type_name":      character[8],
            "attributes":     character[9] or "",
        })
        character_list.insert(
            tk.END,
            f"Name: {character[2]} | Age: {character[6]} | Type: {character[8]} | World: {character[7]}"
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
root.geometry("800x800")

setup_login_page()

root.mainloop()