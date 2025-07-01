from pathlib import Path
import os
import tkinter as tk
import tkinter.filedialog as fd
import sys
from tkinter import (
    Toplevel,
    Label,
    IntVar,
    Scrollbar,
    Frame,
)


def open_popup(current_window, parent_window):
    # Hide results window
    current_window.withdraw()

    # Re-show the original GUI window
    if parent_window:
        parent_window.deiconify()

    # Close the results window entirely
    current_window.destroy()


def get_section_from_summary(subheading, filepath):
    # Check if file exists
    if not os.path.isfile(filepath):
        print(f"Error: '{filepath}' not found.")
        return []

    # Read and extract section
    lines = []
    with open(filepath, "r") as f:
        in_section = False
        for line in f:
            if line.strip() == subheading:
                in_section = True
                continue  # Skip the subheading itself
            if in_section:
                if line.strip().endswith(":") and line.strip() != subheading:
                    break
                if line.strip() == "":
                    continue
                lines.append(line.rstrip())
    return lines


def get_latest_summary_path():
    results_dir = Path.cwd() / "results"

    if not results_dir.exists() or not results_dir.is_dir():
        raise FileNotFoundError("No 'results' directory found.")

    # Get only timestamped subdirectories
    timestamped_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    if not timestamped_dirs:
        raise FileNotFoundError("No timestamped subdirectories found in 'results'.")

    # Use max() for better performance
    latest_dir = max(timestamped_dirs, key=lambda d: d.name)

    summary_path = latest_dir / "-summary.txt"
    if not summary_path.exists():
        raise FileNotFoundError(f"No summary.txt found in {latest_dir}")

    return summary_path


def launch_results_window(file_path, options, parent_window=None):
    result_win = Toplevel(parent_window)
    result_win.title("Results")
    result_win.geometry("1300x863")  # Increased width
    result_win.configure(bg="#FFFFFF")
    result_win.resizable(False, False)

    # Ensure program exits when the window is closed
    result_win.protocol("WM_DELETE_WINDOW", lambda: sys.exit())

    # Header outside the scrollable section
    Label(
        result_win,
        text="Diagnostic Analyzer Results",
        bg="#FFFFFF",
        fg="#000000",
        font=("CiscoSansTT", 30),
    ).place(
        x=60, y=20
    )  # Positioned at the top of the window

    # Create a scrollable frame
    container = Frame(result_win, bg="#FFFFFF")
    container.place(x=60, y=80, width=1170, height=578)  # Adjusted position

    canvas = tk.Canvas(
        container, bg="#FFFFFF", width=1150, height=578
    )  # Adjusted width
    scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas, bg="#FFFFFF")

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Bind mouse scroll wheel to scroll the canvas
    def on_mouse_wheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Initialize checkbox variables with default checked state
    single_file_var = IntVar(value=1)
    processes_var = IntVar(value=1)
    files_var = IntVar(value=1)
    extensions_var = IntVar(value=1)
    paths_var = IntVar(value=1)

    # Checks for activated selection to display
    active_sections = []
    if options.get("processes"):
        active_sections.append("Processes:")
    if options.get("files"):
        active_sections.append("Files:")
    if options.get("extensions"):
        active_sections.append("Extensions:")
    if options.get("paths"):
        active_sections.append("Paths:")

    summary_path = get_latest_summary_path()
    summary_text = "\n\n".join(
        f"{heading}\n" + "\n".join(get_section_from_summary(heading, summary_path))
        for heading in active_sections
    )

    Label(
        scrollable_frame,
        text=summary_text or "No results to display for selected options.",
        bg="#FFFFFF",
        fg="#000000",
        font=("CiscoSansTT", 10),
        wraplength=1150,  # Adjusted wraplength
        justify="left",
    ).pack(pady=10)

    back_button = tk.Button(
        result_win,
        text="Back",
        bd=0,
        command=lambda: open_popup(result_win, parent_window),
        highlightthickness=0,
        relief="flat",
        bg="#FFFFFF",
        activebackground="#FFFFFF",
    )
    back_button.place(
        x=1130.0,
        y=750.0,
        width=100.0,
        height=40.0,  # Adjusted position and size for visibility
    )

    export_button = tk.Button(
        result_win,
        text="Export Results",
        command=lambda: popup_export_file(result_win, summary_text),
        bd=0,
        highlightthickness=0,
        relief="flat",
        bg="#FFFFFF",
        activebackground="#FFFFFF",
    )
    export_button.place(
        x=1020.0,
        y=750.0,
        width=120.0,
        height=40.0,  # Adjusted position and size for alignment
    )


# Allows user to save the results shown in a local .txt file.
def popup_export_file(parent, content_to_export):
    popup = tk.Toplevel(parent)
    popup.title("Export Results")
    popup.geometry("400x200")
    label = tk.Label(popup, text="Click below to save your results file.")
    label.pack(pady=20)

    def save_file():
        file_path = fd.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file_path:
            with open(file_path, "w") as f:
                f.write(content_to_export)
            tk.Label(popup, text="File saved!", fg="green").pack()

    save_btn = tk.Button(popup, text="Save File", command=save_file)
    save_btn.pack(pady=10)

    close_btn = tk.Button(popup, text="Close", command=popup.destroy)
    close_btn.pack(pady=10)
