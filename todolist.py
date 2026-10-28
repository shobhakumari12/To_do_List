import tkinter as tk
from tkinter import ttk
import json
import os
from time import localtime
from datetime import datetime, date

# --- Constants ---
FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

# --- Data ---
tasks = []
is_editing = False  # Track state for the Return/Enter key
current_edit_index = None

# --- File handling ---
def save_tasks():
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)

def load_tasks():
    if os.path.exists(FILENAME):
        try:
            # Use 'with' to guarantee the file closes properly
            with open(FILENAME, "r", encoding="utf-8") as f:
                # Handle completely empty files gracefully
                content = f.read().strip()
                if not content:
                    return []
                raw_tasks = json.loads(content)
                
            new_tasks = []
            for t in raw_tasks:
                if isinstance(t, list) and len(t) == 3:
                    new_tasks.append(t)
                elif isinstance(t, list) and len(t) == 2:

                    new_tasks.append([t[0], t[1], ""])
                else:
                    new_tasks.append(["Normal", t, ""])

            return new_tasks
        except (json.JSONDecodeError, OSError):
            # We will show the alert box after root is initialized to prevent UI bugs
            return []
    return []

# --- Tkinter setup ---
root = tk.Tk()
root.title("📝 My To-Do List App")
root.geometry("600x700")
root.resizable(False, False)
root.config(bg="#f0f0f0")

# --- Functions ---
def alert_box(title, message):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("300x150")
    win.resizable(False, False)
    # Ensure the popup stays on top
    win.transient(root)
    win.grab_set()
    
    tk.Label(win, text=title, font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(win, text=message, font=("Arial", 11)).pack(pady=5)
    tk.Button(win, text="OK", command=win.destroy).pack(pady=10)

def get_color(status):
    return {
        "Urgent": "#F6707C",
        "Important": "#FDDD75",
        "Normal": "#FFFFFF"
    }.get(status, "white")




def refresh_listbox():
    task_listbox.delete(0, tk.END)

    search_text = search_entry.get().strip().lower()
    selected_priority = priority_filter.get()

    for status, name, due_date in tasks:
        # Filter by task name
        if search_text and search_text not in name.lower():
            continue

        # Filter by priority
        if selected_priority != "All priorities":
            if status != selected_priority:
                continue

        # Display due date when available
        display_name = name
        if due_date:
            display_name += f" | Due: {due_date}"

        task_listbox.insert(tk.END, display_name)
        index = task_listbox.size() - 1

        if name.startswith("✓ "):
            task_listbox.itemconfig(
                index, fg="gray", bg=get_color(status)
            )
        elif due_date:
            due = datetime.strptime(due_date, "%d/%m/%Y").date()
            if due < date.today():
             task_listbox.itemconfig(
            index, fg="white", bg="#d9534f"
             )
            else:
              task_listbox.itemconfig(
              index, bg=get_color(status), fg="black"
            )
        else:
            task_listbox.itemconfig(
                index, bg=get_color(status), fg="black"
            )



def handle_return_key(event):
    """Routes the Enter key dynamically depending on app state."""
    if is_editing:
        save_edit(current_edit_index)
    else:
        add_task()


def add_task():
    name = task_entry.get().strip()
    status = combo.get()
    due_date = due_date_entry.get().strip()

    # Validate due date if provided
    if due_date:
        try:
            datetime.strptime(due_date, "%d/%m/%Y")
        except ValueError:
            alert_box(
                "Date Error",
                "Enter a valid date in DD/MM/YYYY format."
            )
            return

    # Validate task name
    if not name:
        alert_box("Task Error", "Please enter a task!")
        return

    # Create timestamp
    hour, minute = localtime()[3], localtime()[4]
    day, month, year = localtime()[2], localtime()[1], localtime()[0]
    timestamp = f"{day:02}/{month:02}/{year} {hour:02}:{minute:02} : "
    full_name = timestamp + name

    # Save task
    tasks.append([status, full_name, due_date])
    refresh_listbox()
    save_tasks()

    # Clear input fields
    task_entry.delete(0, tk.END)
    due_date_entry.delete(0, tk.END)



def delete_task():
    try:
        selected_index = task_listbox.curselection()[0]
        search_text = search_entry.get().strip().lower()
        selected_priority = priority_filter.get()

        visible_tasks = []

        for index, (status, name, due_date) in enumerate(tasks):
            if search_text and search_text not in name.lower():
                continue

            if selected_priority != "All priorities" and status != selected_priority:
                continue

            visible_tasks.append(index)

        task_index = visible_tasks[selected_index]
        tasks.pop(task_index)

        refresh_listbox()
        save_tasks()
        cancel_edit()

    except IndexError:
        alert_box("Task Error", "Please select a task to delete!")


def clear_all_tasks():
    tasks.clear()
    refresh_listbox()
    save_tasks()
    cancel_edit()


def mark_complete():
    try:
        index = task_listbox.curselection()[0]
        status, name, due_date = tasks[index]

        if not name.startswith("✓ "):
            tasks[index][1] = "✓ " + name
            refresh_listbox()
            save_tasks()

    except IndexError:
        alert_box(
            "Task Error",
            "Please select a task to mark as complete!"
        )



def edit_task():
    global is_editing, current_edit_index

    try:
        index = task_listbox.curselection()[0]
        name = tasks[index][1]
        due_date = tasks[index][2]

        if " : " in name:
            name_parts = name.split(" : ", 1)
            name = name_parts[1]

            if name.startswith("✓ "):
                name = name[2:]

        task_entry.delete(0, tk.END)
        task_entry.insert(0, name)

        due_date_entry.delete(0, tk.END)
        due_date_entry.insert(0, due_date)

        combo.set(tasks[index][0])

        is_editing = True
        current_edit_index = index

        add_button.config(
            text="Save Edit",
            bg="#0275d8",
            command=lambda: save_edit(index)
        )

    except IndexError:
        alert_box("Task Error", "Please select a task to edit!")



def save_edit(index):
    global is_editing, current_edit_index

    name = task_entry.get().strip()
    status = combo.get()
    due_date = due_date_entry.get().strip()

    if not name:
        alert_box("Task Error", "Please enter a task!")
        return

    if due_date:
        try:
            datetime.strptime(due_date, "%d/%m/%Y")
        except ValueError:
            alert_box(
                "Date Error",
                "Enter a valid date in DD/MM/YYYY format."
            )
            return

    hour, minute = localtime()[3], localtime()[4]
    day, month, year = localtime()[2], localtime()[1], localtime()[0]
    timestamp = f"{day:02}/{month:02}/{year} {hour:02}:{minute:02} : "
    full_name = timestamp + name

    tasks[index] = [status, full_name, due_date]
    refresh_listbox()
    save_tasks()
    cancel_edit()



def cancel_edit():
    global is_editing, current_edit_index

    is_editing = False
    current_edit_index = None

    task_entry.delete(0, tk.END)
    due_date_entry.delete(0, tk.END)
    combo.set("Normal")

    add_button.config(
        text="Add Task",
        bg="#5cb85c",
        command=add_task
    )

    

# --- Header ---
tk.Label(
    root,
    text="📝 My To-Do List",
    font=("Arial", 18, "bold"),
    bg="#4a7c9e",
    fg="white"
).pack(fill=tk.X, pady=15)

# --- Input field ---
# --- Input field ---
input_frame = tk.Frame(root, bg="#f0f0f0")
input_frame.pack(pady=10)

# --- Search field ---
search_frame = tk.Frame(root, bg="#f0f0f0")
search_frame.pack(pady=5)

tk.Label(
    search_frame,
    text="Search Tasks:",
    font=("Arial", 11),
    bg="#f0f0f0"
).pack(side=tk.LEFT, padx=5)

search_entry = tk.Entry(
    search_frame,
    width=35,
    font=("Arial", 11)
)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind("<KeyRelease>", lambda event: refresh_listbox())

# --- Due date input ---
due_date_frame = tk.Frame(root, bg="#f0f0f0")
due_date_frame.pack(pady=5)

tk.Label(
    due_date_frame,
    text="Due Date (DD/MM/YYYY):",
    font=("Arial", 10),
    bg="#f0f0f0"
).pack(side=tk.LEFT, padx=5)

due_date_entry = tk.Entry(
    due_date_frame,
    width=15,
    font=("Arial", 10)
)
due_date_entry.pack(side=tk.LEFT, padx=5)


# --- Priority filter ---
priority_filter = ttk.Combobox(
    search_frame,
    values=["All priorities", "Normal", "Important", "Urgent"],
    state="readonly",
    width=15
)
priority_filter.set("All priorities")
priority_filter.pack(side=tk.LEFT, padx=5)
priority_filter.bind("<<ComboboxSelected>>", lambda event: refresh_listbox())


task_entry = tk.Entry(input_frame, width=30, font=("Arial", 12), bd=2, relief=tk.GROOVE)
task_entry.pack(side=tk.LEFT, padx=10, ipady=5)
task_entry.bind("<Return>", handle_return_key) # Updated binding

combo = ttk.Combobox(
    input_frame,
    values=["Normal", "Important", "Urgent"],
    state="readonly",
    width=10
)
combo.set("Normal")
combo.pack(side=tk.LEFT, padx=10)

add_button = tk.Button(
    input_frame,
    text="Add Task",
    width=12,
    font=("Arial", 11, "bold"),
    bg="#5cb85c",
    fg="white",
    activebackground="#4cae4c",
    bd=0,
    cursor="hand2",
    command=add_task
)
add_button.pack(side=tk.LEFT)

# --- Task list ---
list_frame = tk.Frame(root, bg="#f0f0f0")
list_frame.pack(pady=10, padx=20)

scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

task_listbox = tk.Listbox(
    list_frame,
    width=50,
    height=15,
    font=("Arial", 11),
    bd=2,
    relief=tk.SUNKEN,
    selectmode=tk.SINGLE,
    activestyle='none',
    bg="white",
    selectbackground="#d4e6f1",
    selectforeground="black",
    yscrollcommand=scrollbar.set
)
task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=task_listbox.yview)

# --- Buttons ---
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=20)

tk.Button(btn_frame, text="✓ Mark Complete", width=15, font=("Arial", 10, "bold"),
          bg="#5bc0de", fg="white", activebackground="#46b8da", bd=0, cursor="hand2",
          command=mark_complete).grid(row=0, column=0, padx=8)

tk.Button(btn_frame, text="✎ Edit", width=15, font=("Arial", 10, "bold"),
          bg="#0275d8", fg="white", activebackground="#025aa5", bd=0, cursor="hand2",
          command=edit_task).grid(row=0, column=1, padx=8)

tk.Button(btn_frame, text="✕ Delete", width=15, font=("Arial", 10, "bold"),
          bg="#d9534f", fg="white", activebackground="#c9302c", bd=0, cursor="hand2",
          command=delete_task).grid(row=0, column=2, padx=8)

tk.Button(btn_frame, text="Clear All", width=15, font=("Arial", 10, "bold"),
          bg="#f0ad4e", fg="white", activebackground="#ec971f", bd=0, cursor="hand2",
          command=clear_all_tasks).grid(row=1, column=1, pady=8)

# --- Load tasks & display ---
tasks = load_tasks()
refresh_listbox()

root.protocol("WM_DELETE_WINDOW", lambda: (save_tasks(), root.destroy()))
root.mainloop()
