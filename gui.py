import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from Diag_Analyzer_v2 import main
from results import launch_results_window
from pathlib import Path
from tkinter import (
    Tk,
    Canvas,
    Entry,
    Button,
    PhotoImage,
    Label,
    Toplevel,
    StringVar,
    IntVar,
    Checkbutton,
    messagebox,
)
from datetime import datetime

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"


def relative_to_assets(path: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        # If running from a PyInstaller bundle, use the _MEIPASS directory
        return Path(sys._MEIPASS) / "assets" / "frame0" / Path(path)
    else:
        # Otherwise, use the normal assets path
        return ASSETS_PATH / Path(path)


window = Tk()
window.title("Secure Endpoint Diagnostic Analyzer")
file_path_var = StringVar()

# Track checkbox states
single_file_var = IntVar(value=1)  # Checked by default
directory_var = IntVar(value=0)
processes_var = IntVar(value=1)  # Checked by default
files_var = IntVar(value=1)  # Checked by default
extensions_var = IntVar(value=1)  # Checked by default
paths_var = IntVar(value=1)  # Checked by default

window.geometry("700x408")  # Increased width
window.configure(bg="#FFFFFF")

canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=408,
    width=700,
    bd=0,
    highlightthickness=0,
    relief="ridge",
)
canvas.place(x=0, y=0)

canvas.create_rectangle(1.0, 0.0, 371.0, 408.0, fill="#0489BA", outline="")
canvas.create_rectangle(1.0, 0.0, 705.0, 424.0, fill="#E6F5FB", outline="")
canvas.create_rectangle(0.0, 0.0, 374.0, 408.0, fill="#0489BA", outline="")

canvas.create_text(
    429.0, 39.0, anchor="nw", fill="#242424", font=("CiscoSansTT Bold", 20 * -1)
)
canvas.create_text(
    393.0,
    86.0,
    anchor="nw",
    text="Input Selection",
    fill="#242424",
    font=("CiscoSansTT", 15 * -1),
)
canvas.create_text(
    390.0,
    155.0,
    anchor="nw",
    text="Analysis Options",
    fill="#242424",
    font=("CiscoSansTT", 15 * -1),
)


def handle_submit():
    if not file_path_var.get():
        messagebox.showerror(
            "Missing File", "Please select a diagnostic file before submitting."
        )
        return

    # Populates a dictionary of selectable options and 0 or 1.
    options = {
        "processes": processes_var.get(),
        "files": files_var.get(),
        "extensions": extensions_var.get(),
        "paths": paths_var.get(),
        "start_time": start_time_var.get(),
        "single_file": single_file_var.get(),
        "directory": directory_var.get(),
    }

    results_dir = main(selected_file_path)
    window.withdraw()  # Hides this window
    launch_results_window(str(Path(results_dir) / "-summary.txt"), options, window)


# Submit Button
button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=handle_submit,
    relief="flat",
)
button_1.place(x=483.0, y=353.0, width=82.0, height=25.0)

canvas.create_text(
    40.0,
    52.0,
    anchor="nw",
    text="Diagnostic Analysis",
    fill="#FFFFFF",
    font=("CiscoSansTT Bold", 30 * -1),
)


def browse_file():
    from tkinter import filedialog

    global selected_file_path
    selected_file_path = filedialog.askopenfilename(
        title="Select Diagnostic File",
        filetypes=[("Compressed Files", "*.zip *.7z"), ("All Files", "*.*")],
    )
    if selected_file_path:
        print(f"Selected file: {selected_file_path}")
        file_path_var.set(selected_file_path)


def clear_checkboxes():
    processes_var.set(0)
    files_var.set(0)
    extensions_var.set(0)
    paths_var.set(0)
    single_file_var.set(0)
    directory_var.set(0)


# Browse Button
button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=browse_file,
    relief="flat",
)
button_2.place(x=391.0, y=118.0, width=53.0, height=16.0)

canvas.create_rectangle(468.0, 119.0, 659.0, 135.0, fill="#D9D9D9", outline="")

file_path_entry = Entry(
    window,
    textvariable=file_path_var,
    bd=0,
    bg="#D9D9D9",
    fg="#000000",
    highlightthickness=0,
    font=("CiscoSans", 10),
)
file_path_entry.place(x=470.0, y=120.0, width=185.0, height=15.0)

processes_cb = Checkbutton(
    window,
    text="Processes",
    variable=processes_var,
    bg="#E6F5FB",
    fg="#242424",
    font=("CiscoSansTT Medium", 12),
    relief="flat",
    highlightthickness=0,
    bd=0,
    activebackground="#E6F5FB",
    cursor="hand2",
)
processes_cb.place(x=570, y=200)

files_cb = Checkbutton(
    window,
    text="Files",
    variable=files_var,
    bg="#E6F5FB",
    fg="#242424",
    font=("CiscoSansTT Medium", 12),
    relief="flat",
    highlightthickness=0,
    bd=0,
    activebackground="#E6F5FB",
    cursor="hand2",
)
files_cb.place(x=570, y=222)

extensions_cb = Checkbutton(
    window,
    text="Extensions",
    variable=extensions_var,
    bg="#E6F5FB",
    fg="#242424",
    font=("CiscoSansTT Medium", 12),
    relief="flat",
    highlightthickness=0,
    bd=0,
    activebackground="#E6F5FB",
    cursor="hand2",
)
extensions_cb.place(x=570, y=247)

paths_cb = Checkbutton(
    window,
    text="Paths",
    variable=paths_var,
    bg="#E6F5FB",
    fg="#242424",
    font=("CiscoSansTT Medium", 12),
    relief="flat",
    highlightthickness=0,
    bd=0,
    activebackground="#E6F5FB",
    cursor="hand2",
)
paths_cb.place(x=570, y=272)

start_time_var = StringVar()


def open_start_time_popup():
    # Create a new popup window for entering the start time
    popup = Toplevel(window)
    popup.title("Enter Start Time")
    popup.geometry("300x100")
    popup.resizable(False, False)

    # Prompt the user with the expected input format
    Label(popup, text="Enter Start Time (e.g. May 20 12:01:04):").pack(pady=5)

    # Create a text entry field for the user to input time
    time_var = StringVar()
    entry = Entry(popup, textvariable=time_var, width=25)
    entry.pack(pady=5)
    entry.focus_set()  # Automatically focus the input field

    def submit():
        user_input = (
            time_var.get().strip()
        )  # Get user input and remove surrounding spaces

        try:
            # Get current year dynamically
            current_year = datetime.now().year

            # Parse the full time using the current year + user input
            # This allows flexibility while keeping consistent datetime comparison
            full_time = datetime.strptime(
                f"{current_year} {user_input}", "%Y %b %d %H:%M:%S"
            )

            # Store the parsed datetime for use in filtering log results later
            global parsed_start_time
            parsed_start_time = full_time

            # Update the label to show what the user entered (without the year)
            start_time_var.set(user_input)
            start_time_label.config(text=f"Start Time: {user_input}")

            popup.destroy()  # Close the popup after successful input
        except ValueError:
            # Show an error if the input format is incorrect
            messagebox.showerror(
                "Invalid Format", "Please enter time like: May 20 12:01:04"
            )

    # Submit button to trigger time parsing and validation
    submit_btn = Button(popup, text="Submit", command=submit)
    submit_btn.pack(pady=5)


start_time_label = Label(
    window,
    text="Set Start Time",
    bg="#D9D9D9",
    fg="#242424",
    font=("CiscoSans", 10),
    cursor="hand2",
)
start_time_label.place(x=390, y=183, width=100, height=20)
start_time_label.bind("<Button-1>", lambda e: open_start_time_popup())

# Clear Button
button_image_9 = PhotoImage(file=relative_to_assets("button_9.png"))
button_9 = Button(
    image=button_image_9,
    borderwidth=0,
    highlightthickness=0,
    command=clear_checkboxes,
    relief="flat",
)
button_9.place(x=605.0, y=313.0, width=50, height=14)

canvas.create_text(
    20.0,
    132.0,
    anchor="nw",
    text=(
        "This diagnostic analysis tool is designed to process Secure Endpoint diagnostic files.\n"
        "Initiate analysis by selecting a diagnostic file in either .7z or .zip format and configure your output preferences.\n\n"
        "For optimal results, please ensure that diagnostic files are complete and have not been modified.\n"
    ),
    fill="#FFFFFF",
    font=("CiscoSans Bold", 14 * -1),
    width=320,
)

window.resizable(False, False)
window.mainloop()
