"""
Modern CustomTkinter-based GUI for JobPulse application.
Provides a clean, theme-switchable interface for job searching and management.
"""

import logging
import threading
import webbrowser
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk
from dateutil import parser as date_parser

from jobpulse import locations, orm, scraper

logger = logging.getLogger(__name__)

# ============================================================================
# Theme Configuration
# ============================================================================

THEMES = {
    "Dark Blue": {"mode": "dark", "color": "blue"},
    "Dark Green": {"mode": "dark", "color": "green"},
    "Light Blue": {"mode": "light", "color": "blue"},
    "Light Green": {"mode": "light", "color": "green"},
}

DEFAULT_THEME = "Dark Blue"


# ============================================================================
# Main Application Window
# ============================================================================


def create_main_window() -> ctk.CTk:
    """Create and configure the main application window."""

    # Initialize database
    orm.init_database()

    # Load theme preference from database and apply BEFORE creating window
    saved_theme = orm.get_config("theme", DEFAULT_THEME)
    theme_config = THEMES.get(saved_theme, THEMES[DEFAULT_THEME])

    # Apply theme settings BEFORE creating any widgets
    ctk.set_appearance_mode(theme_config["mode"])
    ctk.set_default_color_theme(theme_config["color"])
    logger.info(f"Applied theme: {saved_theme}")

    # Create main window
    window = ctk.CTk()
    window.title("JobPulse - Job Search Manager")
    window.geometry("1200x700")

    # Store application state
    window.app_state = {
        "current_view": "home",
        "search_results": None,
        "saved_jobs": [],
        "applications": [],
        "content_frame": None,
        "main_frame": None,
        "current_page": 1,
        "results_per_page": 10,
        "search_params": {},
    }

    # Create menu bar
    create_menu_bar(window)

    # Create main content area
    create_main_content(window)

    return window


def apply_theme(theme_name: str) -> None:
    """Save the selected theme (requires app restart to take effect)."""
    # Save theme preference to database
    orm.set_config("theme", theme_name, "User interface theme")
    logger.info(f"Theme preference saved: {theme_name}")


def create_menu_bar(window: ctk.CTk) -> None:
    """Create the top menu bar with theme options."""

    menu_frame = ctk.CTkFrame(window, height=40, corner_radius=0)
    menu_frame.pack(fill="x", padx=0, pady=0)
    menu_frame.pack_propagate(False)

    # App title
    title_label = ctk.CTkLabel(menu_frame, text="JobPulse", font=ctk.CTkFont(size=14, weight="bold"))
    title_label.pack(side="left", padx=16)

    current_theme = orm.get_config("theme", DEFAULT_THEME)

    theme_menu = ctk.CTkOptionMenu(
        menu_frame,
        values=list(THEMES.keys()),
        command=lambda choice: on_theme_change(choice, window),
        width=120,
        height=30,
    )
    theme_menu.set(current_theme)
    theme_menu.pack(side="right", padx=(5, 16))


def restart_application(window: ctk.CTk) -> None:
    """Restart the application to apply theme changes."""
    import os
    import sys

    # Close current window
    window.destroy()

    # Close resources
    scraper.close_http_client()
    orm.close_database()

    # Restart the application
    python = sys.executable
    os.execl(python, python, *sys.argv)


def on_theme_change(theme_name: str, window: ctk.CTk) -> None:
    """Handle theme change event."""
    apply_theme(theme_name)

    # Show restart notification
    notification = ctk.CTkToplevel(window)
    notification.title("Theme Changed")
    notification.geometry("450x200")
    notification.transient(window)
    notification.grab_set()

    # Center the notification
    notification.update_idletasks()
    x = window.winfo_x() + (window.winfo_width() - notification.winfo_width()) // 2
    y = window.winfo_y() + (window.winfo_height() - notification.winfo_height()) // 2
    notification.geometry(f"+{x}+{y}")

    msg_label = ctk.CTkLabel(
        notification,
        text=f"Theme '{theme_name}' saved!\n\nPlease restart the application\nfor the theme to take effect.",
        font=ctk.CTkFont(size=14),
        justify="center",
    )
    msg_label.pack(pady=(30, 20))

    button_frame = ctk.CTkFrame(notification, fg_color="transparent")
    button_frame.pack(pady=(0, 20))

    restart_button = ctk.CTkButton(
        button_frame,
        text="Restart Now",
        command=lambda: restart_application(window),
        width=120,
        height=36,
        fg_color="green",
        hover_color="darkgreen",
    )
    restart_button.pack(side="left", padx=5)

    ok_button = ctk.CTkButton(button_frame, text="Later", command=notification.destroy, width=100, height=36)
    ok_button.pack(side="left", padx=5)


def create_main_content(window: ctk.CTk) -> None:
    """Create the main content area of the application."""

    # Main container
    main_frame = ctk.CTkFrame(window, corner_radius=0)
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    window.app_state["main_frame"] = main_frame

    # Left sidebar
    create_sidebar(main_frame)

    # Right content area
    create_content_area(main_frame)


def create_sidebar(parent: ctk.CTkFrame) -> None:
    """Create the left sidebar with navigation and controls."""

    sidebar = ctk.CTkFrame(parent, width=240, corner_radius=0)
    sidebar.pack(side="left", fill="y", padx=0, pady=0)
    sidebar.pack_propagate(False)

    # Profile section header
    profile_header = ctk.CTkLabel(
        sidebar,
        text="User Profile",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=("gray10", "gray90"),  # Dark text for light mode, light text for dark mode
    )
    profile_header.pack(pady=(12, 10), padx=16)

    # Profile configure button
    profile_button = ctk.CTkButton(
        sidebar, text="⚙ Configure Profile", command=open_profile_config, height=40, font=ctk.CTkFont(size=14)
    )
    profile_button.pack(pady=12, padx=16, fill="x")

    # Active profile display
    active_profile_frame = ctk.CTkFrame(sidebar)
    active_profile_frame.pack(pady=12, padx=16, fill="x")

    profiles = orm.get_all_profiles()
    if profiles:
        profile = profiles[0]
        profile_info = ctk.CTkLabel(
            active_profile_frame,
            text=f"Active: {profile['name']}\n{profile.get('email', 'No email')}",
            font=ctk.CTkFont(size=14),
            text_color=("gray20", "gray80"),  # Adaptive color for both themes
        )
        profile_info.pack(pady=12)
    else:
        no_profile = ctk.CTkLabel(
            active_profile_frame,
            text="No profile configured",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),  # Adaptive gray
        )
        no_profile.pack(pady=12)

    # Divider
    divider = ctk.CTkFrame(sidebar, height=1, fg_color=("gray70", "gray30"))
    divider.pack(fill="x", padx=16, pady=50)

    # Navigation buttons
    nav_header = ctk.CTkLabel(
        sidebar,
        text="Navigation",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=("gray10", "gray90"),  # Dark text for light mode, light text for dark mode
    )
    nav_header.pack(pady=(12, 10), padx=16)

    # Get root window reference
    root_window = parent.winfo_toplevel()

    nav_buttons = [
        ("🏠 Home", lambda: show_home_view(root_window)),
        ("🔍 Search Jobs", lambda: show_search_view(root_window)),
        ("💼 My Applications", lambda: show_applications_view(root_window)),
        ("⭐ Saved Jobs", lambda: show_saved_jobs_view(root_window)),
        ("📊 Dashboard", lambda: show_dashboard_view(root_window)),
    ]

    for text, command in nav_buttons:
        btn = ctk.CTkButton(
            sidebar,
            text=text,
            command=command,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),  # Dark text for light mode, light text for dark mode
            anchor="w",
        )
        btn.pack(pady=5, padx=16, fill="x")

    # Settings button at bottom
    settings_button = ctk.CTkButton(
        sidebar,
        text="⚙ Settings",
        command=lambda: show_dashboard_view(root_window),
        height=40,
        font=ctk.CTkFont(size=14),
        fg_color="transparent",
        hover_color=("gray70", "gray30"),
        text_color=("gray10", "gray90"),  # Dark text for light mode, light text for dark mode
    )
    settings_button.pack(side="bottom", pady=12, padx=16, fill="x")


def create_content_area(parent: ctk.CTkFrame) -> None:
    """Create the main content area."""

    content_frame = ctk.CTkFrame(parent, corner_radius=0)
    content_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)

    # Welcome header
    header = ctk.CTkLabel(content_frame, text="Welcome to JobPulse", font=ctk.CTkFont(size=48, weight="bold"))
    header.pack(pady=(12, 20))

    # Description
    description = ctk.CTkLabel(
        content_frame,
        text="Your intelligent job search companion\n\nGet started by configuring your profile and searching for jobs",
        font=ctk.CTkFont(size=14),
        justify="center",
    )
    description.pack(pady=12)

    # Search section
    search_frame = ctk.CTkFrame(content_frame, width=600)
    search_frame.pack(pady=20, padx=16)

    search_label = ctk.CTkLabel(search_frame, text="Quick Search", font=ctk.CTkFont(size=14, weight="bold"))
    search_label.pack(pady=(12, 10))

    # Search inputs
    input_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
    input_frame.pack(pady=12, padx=16)

    keyword_entry = ctk.CTkEntry(
        input_frame, placeholder_text="Job title or keyword", width=300, height=40, font=ctk.CTkFont(size=14)
    )
    keyword_entry.pack(pady=5)

    location_var = ctk.StringVar(value="Any Location")
    location_options = ["Any Location"] + [city["name"] for city in locations.CITY_ID_MAP]
    location_menu = ctk.CTkOptionMenu(
        input_frame, variable=location_var, values=location_options, width=300, height=40
    )
    location_menu.pack(pady=5)

    # Get root window
    root_window = content_frame.winfo_toplevel()

    search_button = ctk.CTkButton(
        input_frame,
        text="🔍 Search Jobs",
        command=lambda: perform_search(root_window, keyword_entry.get(), location_var.get()),
        width=300,
        height=40,
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    search_button.pack(pady=20)

    # Store content frame reference
    root_window.app_state["content_frame"] = content_frame

    # Stats section
    stats_frame = ctk.CTkFrame(content_frame)
    stats_frame.pack(pady=20, padx=16, fill="x")

    stats_label = ctk.CTkLabel(stats_frame, text="Statistics", font=ctk.CTkFont(size=14, weight="bold"))
    stats_label.pack(pady=(12, 10))

    stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
    stats_container.pack(pady=12, padx=16)

    # Get real stats
    stats_data = get_user_statistics()
    stats = [
        ("Jobs Saved", str(stats_data["saved_jobs"])),
        ("Applications", str(stats_data["applications"])),
        ("Interviews", str(stats_data["interviews"])),
    ]

    for i, (label, value) in enumerate(stats):
        stat_box = ctk.CTkFrame(stats_container, width=150)
        stat_box.grid(row=0, column=i, padx=10, pady=12)

        value_label = ctk.CTkLabel(stat_box, text=value, font=ctk.CTkFont(size=14, weight="bold"))
        value_label.pack(pady=(12, 5))

        label_text = ctk.CTkLabel(stat_box, text=label, font=ctk.CTkFont(size=14), text_color=("gray30", "gray70"))
        label_text.pack(pady=(0, 15))


def open_profile_config() -> None:
    """Open the profile configuration dialog."""

    config_window = ctk.CTkToplevel()
    config_window.title("Configure Profile")
    config_window.geometry("500x600")
    config_window.transient()
    config_window.grab_set()

    # Header
    header = ctk.CTkLabel(config_window, text="User Profile Configuration", font=ctk.CTkFont(size=14, weight="bold"))
    header.pack(pady=(12, 10))

    # Description
    desc = ctk.CTkLabel(
        config_window,
        text="Configure your profile details and job preferences",
        font=ctk.CTkFont(size=14),
        text_color=("gray30", "gray70"),
    )
    desc.pack(pady=(0, 20))

    # Scrollable form frame
    form_frame = ctk.CTkScrollableFrame(config_window, width=450, height=400)
    form_frame.pack(pady=12, padx=24, fill="both", expand=True)

    # Placeholder message
    placeholder_label = ctk.CTkLabel(
        form_frame,
        text="Profile configuration fields will be added here.\n\n"
        "This will include:\n"
        "• Personal information\n"
        "• Contact details\n"
        "• Job preferences\n"
        "• Skills and experience\n"
        "• Salary expectations\n"
        "• Location preferences",
        font=ctk.CTkFont(size=14),
        justify="left",
    )
    placeholder_label.pack(pady=12, padx=16)

    # Button frame
    button_frame = ctk.CTkFrame(config_window, fg_color="transparent")
    button_frame.pack(pady=20, padx=24, fill="x")

    cancel_button = ctk.CTkButton(
        button_frame, text="Cancel", command=config_window.destroy, width=120, fg_color="gray40", hover_color="gray30"
    )
    cancel_button.pack(side="left", padx=5)

    save_button = ctk.CTkButton(
        button_frame, text="Save Profile", command=lambda: on_save_profile(config_window), width=120
    )
    save_button.pack(side="right", padx=5)


def on_save_profile(window: ctk.CTkToplevel) -> None:
    """Handle profile save action."""
    # Placeholder - will be implemented with actual form fields
    print("Profile saved (placeholder)")
    window.destroy()


# ============================================================================
# View Functions
# ============================================================================


def clear_content(window: ctk.CTk) -> ctk.CTkFrame:
    """Clear the current content area and return a new frame."""
    if window.app_state["content_frame"]:
        old_frame = window.app_state["content_frame"]
        # Clear the reference first to prevent access during destruction
        window.app_state["content_frame"] = None
        
        # Process all pending events
        window.update_idletasks()
        window.update()
        
        # Destroy all children first to prevent widget update errors
        try:
            for child in old_frame.winfo_children():
                try:
                    child.destroy()
                except:
                    pass
        except:
            pass
        
        # Now destroy the frame itself
        try:
            old_frame.destroy()
        except Exception as e:
            logger.warning(f"Error destroying content frame: {e}")

    main_frame = window.app_state["main_frame"]
    content_frame = ctk.CTkFrame(main_frame, corner_radius=0)
    content_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)
    window.app_state["content_frame"] = content_frame
    return content_frame


def show_home_view(window: ctk.CTk) -> None:
    """Display the home/welcome view."""
    content_frame = clear_content(window)
    window.app_state["current_view"] = "home"

    # Welcome header
    header = ctk.CTkLabel(content_frame, text="Welcome to JobPulse", font=ctk.CTkFont(size=48, weight="bold"))
    header.pack(pady=(12, 20))

    # Description
    description = ctk.CTkLabel(
        content_frame,
        text="Your intelligent job search companion\n\nGet started by configuring your profile and searching for jobs",
        font=ctk.CTkFont(size=14),
        justify="center",
    )
    description.pack(pady=12)

    # Search section
    search_frame = ctk.CTkFrame(content_frame, width=600)
    search_frame.pack(pady=20, padx=16)

    search_label = ctk.CTkLabel(search_frame, text="Quick Search", font=ctk.CTkFont(size=14, weight="bold"))
    search_label.pack(pady=(12, 10))

    # Search inputs
    input_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
    input_frame.pack(pady=12, padx=16)

    keyword_entry = ctk.CTkEntry(
        input_frame, placeholder_text="Job title or keyword", width=300, height=40, font=ctk.CTkFont(size=14)
    )
    keyword_entry.pack(pady=5)

    location_var = ctk.StringVar(value="Any Location")
    location_options = ["Any Location"] + [city["name"] for city in locations.CITY_ID_MAP]
    location_menu = ctk.CTkOptionMenu(
        input_frame, variable=location_var, values=location_options, width=300, height=40
    )
    location_menu.pack(pady=5)

    search_button = ctk.CTkButton(
        input_frame,
        text="🔍 Search Jobs",
        command=lambda: perform_search(window, keyword_entry.get(), location_var.get()),
        width=300,
        height=40,
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    search_button.pack(pady=20)

    # Stats section
    stats_frame = ctk.CTkFrame(content_frame)
    stats_frame.pack(pady=20, padx=16, fill="x")

    stats_label = ctk.CTkLabel(stats_frame, text="Statistics", font=ctk.CTkFont(size=14, weight="bold"))
    stats_label.pack(pady=(12, 10))

    stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
    stats_container.pack(pady=12, padx=16)

    # Get real stats
    stats_data = get_user_statistics()
    stats = [
        ("Jobs Saved", str(stats_data["saved_jobs"])),
        ("Applications", str(stats_data["applications"])),
        ("Interviews", str(stats_data["interviews"])),
    ]

    for i, (label, value) in enumerate(stats):
        stat_box = ctk.CTkFrame(stats_container, width=150)
        stat_box.grid(row=0, column=i, padx=10, pady=12)

        value_label = ctk.CTkLabel(stat_box, text=value, font=ctk.CTkFont(size=14, weight="bold"))
        value_label.pack(pady=(12, 5))

        label_text = ctk.CTkLabel(stat_box, text=label, font=ctk.CTkFont(size=14), text_color=("gray30", "gray70"))
        label_text.pack(pady=(0, 15))


def show_search_view(window: ctk.CTk) -> None:
    """Display the job search view."""
    content_frame = clear_content(window)
    window.app_state["current_view"] = "search"

    # Scrollable container
    scroll_frame = ctk.CTkScrollableFrame(content_frame, width=1000, height=750)
    scroll_frame.pack(pady=12, padx=16, fill="both", expand=True)

    # Header
    header = ctk.CTkLabel(scroll_frame, text="Search Jobs", font=ctk.CTkFont(size=48, weight="bold"))
    header.pack(pady=(12, 20))

    # Centered search form container
    form_wrapper = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    form_wrapper.pack(pady=12, padx=16)

    # Search form
    search_frame = ctk.CTkFrame(form_wrapper, width=700)
    search_frame.pack(pady=12)

    form_container = ctk.CTkFrame(search_frame, fg_color="transparent")
    form_container.pack(pady=20, padx=24)

    # Keyword field
    ctk.CTkLabel(form_container, text="Keyword:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    keyword_entry = ctk.CTkEntry(form_container, placeholder_text="e.g., Software Engineer", width=600, height=44)
    keyword_entry.pack(pady=(0, 10))

    # Location field with autocomplete
    ctk.CTkLabel(form_container, text="Location:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    location_var = ctk.StringVar(value="")
    location_options = ["Any Location"] + [city["name"] for city in locations.CITY_ID_MAP]
    location_menu = ctk.CTkOptionMenu(
        form_container, variable=location_var, values=location_options, width=600, height=44
    )
    location_var.set("Any Location")  # Set default
    location_menu.pack(pady=(0, 10))

    # Job Type
    ctk.CTkLabel(form_container, text="Job Type:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    job_type_var = ctk.StringVar(value="")
    job_type_menu = ctk.CTkOptionMenu(
        form_container,
        variable=job_type_var,
        values=["", "FullTime", "PartTime", "Contract", "Intern"],
        width=600,
        height=44,
    )
    job_type_menu.pack(pady=(0, 10))

    # Job Level
    ctk.CTkLabel(form_container, text="Job Level:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    job_level_var = ctk.StringVar(value="")
    job_level_menu = ctk.CTkOptionMenu(
        form_container, variable=job_level_var, values=["", "Entry", "Mid", "Top"], width=600, height=44
    )
    job_level_menu.pack(pady=(0, 10))

    # Posted Within
    ctk.CTkLabel(form_container, text="Posted Within:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    posted_within_var = ctk.StringVar(value="")
    posted_within_menu = ctk.CTkOptionMenu(
        form_container,
        variable=posted_within_var,
        values=["", "Today", "Last 2 days", "Last 3 days", "Last 4 days", "Last 5 days"],
        width=600,
        height=44,
    )
    posted_within_menu.pack(pady=(0, 10))

    # Experience Range
    ctk.CTkLabel(form_container, text="Experience (Years):", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    exp_frame = ctk.CTkFrame(form_container, fg_color="transparent")
    exp_frame.pack(anchor="w", pady=(0, 10))
    
    exp_start_var = ctk.StringVar(value="0")
    ctk.CTkLabel(exp_frame, text="Min:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
    exp_start_entry = ctk.CTkEntry(exp_frame, textvariable=exp_start_var, width=80, height=44)
    exp_start_entry.pack(side="left", padx=(0, 20))
    
    exp_end_var = ctk.StringVar(value="0")
    ctk.CTkLabel(exp_frame, text="Max:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
    exp_end_entry = ctk.CTkEntry(exp_frame, textvariable=exp_end_var, width=80, height=44)
    exp_end_entry.pack(side="left")

    # Salary Range
    ctk.CTkLabel(form_container, text="Salary Range (BDT):", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    salary_frame = ctk.CTkFrame(form_container, fg_color="transparent")
    salary_frame.pack(anchor="w", pady=(0, 10))
    
    salary_start_var = ctk.StringVar(value="0")
    ctk.CTkLabel(salary_frame, text="Min:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
    salary_start_entry = ctk.CTkEntry(salary_frame, textvariable=salary_start_var, width=120, height=44)
    salary_start_entry.pack(side="left", padx=(0, 20))
    
    salary_end_var = ctk.StringVar(value="0")
    ctk.CTkLabel(salary_frame, text="Max:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
    salary_end_entry = ctk.CTkEntry(salary_frame, textvariable=salary_end_var, width=120, height=44)
    salary_end_entry.pack(side="left")

    # Workplace (Remote/Work from home)
    ctk.CTkLabel(form_container, text="Work Arrangement:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 2))
    workplace_var = ctk.StringVar(value="")
    workplace_menu = ctk.CTkOptionMenu(
        form_container,
        variable=workplace_var,
        values=["", "Work from Home", "Office"],
        width=600,
        height=44,
    )
    workplace_menu.pack(pady=(0, 10))

    # Fresher Jobs
    fresher_var = ctk.BooleanVar(value=False)
    fresher_checkbox = ctk.CTkCheckBox(
        form_container,
        text="Fresher Jobs Only",
        variable=fresher_var,
        font=ctk.CTkFont(size=14)
    )
    fresher_checkbox.pack(anchor="w", pady=(5, 10))

    # Search button
    search_btn = ctk.CTkButton(
        form_container,
        text="\ud83d\udd0d Search Jobs",
        command=lambda: perform_advanced_search(
            window,
            keyword_entry.get(),
            location_var.get(),
            job_type_var.get(),
            job_level_var.get(),
            posted_within_var.get(),
            exp_start_var.get(),
            exp_end_var.get(),
            salary_start_var.get(),
            salary_end_var.get(),
            workplace_var.get(),
            fresher_var.get()
        ),
        width=600,
        height=40,
        font=ctk.CTkFont(size=15, weight="bold"),
    )
    search_btn.pack(pady=20)


def perform_search(window: ctk.CTk, keyword: str, location: str = "", job_type: str = "", job_level: str = "", page: int = 1) -> None:
    """Execute job search and display results."""
    if not keyword or not keyword.strip():
        show_message(window, "Error", "Please enter a keyword to search")
        return

    # Sanitize parameters - convert None to empty string and handle "Any Location" placeholder
    location = "" if (location is None or location == "Location" or location == "Any Location") else location
    job_type = "" if job_type is None else job_type
    job_level = "" if job_level is None else job_level

    # Store search parameters
    if page == 1:
        window.app_state["current_page"] = 1
        window.app_state["search_params"] = {
            "keyword": keyword.strip(),
            "location": location,
            "job_type": job_type,
            "job_level": job_level,
        }

    # Show loading message
    loading_window = show_loading(window, "Searching for jobs...")

    def search_thread():
        try:
            # Get results per page from state
            per_page = window.app_state.get("results_per_page", 10)
            
            # Perform search with API pagination
            results = scraper.search_jobs(
                keyword=keyword.strip(),
                location=location,
                job_type=job_type,
                job_level=job_level,
                page=page,
                results_per_page=per_page
            )

            # Store results object (not just jobs)
            window.app_state["search_results"] = results
            window.app_state["current_page"] = page

            # Schedule GUI updates on main thread
            def update_ui():
                try:
                    loading_window.destroy()
                except:
                    pass
                show_results_view(window)
            
            window.after(0, update_ui)

        except Exception as e:
            # Schedule error handling on main thread
            def show_error():
                try:
                    loading_window.destroy()
                except:
                    pass
                show_message(window, "Error", f"Search failed: {str(e)}")
            
            window.after(0, show_error)
            logger.error(f"Search error: {e}", exc_info=True)

    # Run search in background thread
    thread = threading.Thread(target=search_thread, daemon=True)
    thread.start()


def perform_advanced_search(
    window: ctk.CTk,
    keyword: str,
    location: str = "",
    job_type: str = "",
    job_level: str = "",
    posted_within: str = "",
    exp_start: str = "0",
    exp_end: str = "0",
    salary_start: str = "0",
    salary_end: str = "0",
    workplace: str = "",
    is_fresher: bool = False,
    page: int = 1
) -> None:
    """Execute advanced job search with all filters."""
    if not keyword or not keyword.strip():
        show_message(window, "Error", "Please enter a keyword to search")
        return

    # Sanitize parameters - convert None to empty string
    location = "" if location is None else location
    job_type = "" if job_type is None else job_type
    job_level = "" if job_level is None else job_level
    posted_within = "" if posted_within is None else posted_within
    workplace = "" if workplace is None else workplace
    exp_start = "0" if exp_start is None else exp_start
    exp_end = "0" if exp_end is None else exp_end
    salary_start = "0" if salary_start is None else salary_start
    salary_end = "0" if salary_end is None else salary_end

    # Convert string inputs to integers
    try:
        exp_start_int = int(exp_start) if exp_start and exp_start.strip() else 0
        exp_end_int = int(exp_end) if exp_end and exp_end.strip() else 0
        salary_start_int = int(salary_start) if salary_start and salary_start.strip() else 0
        salary_end_int = int(salary_end) if salary_end and salary_end.strip() else 0
    except ValueError as e:
        show_message(window, "Error", f"Please enter valid numbers for experience and salary: {e}")
        return

    # Map posted_within display text to API values
    posted_map = {
        "": "",
        "Today": "1",
        "Last 2 days": "2",
        "Last 3 days": "3",
        "Last 4 days": "4",
        "Last 5 days": "5"
    }
    posted_within_api = posted_map.get(posted_within, "")

    # Map workplace display text to API values
    workplace_api = "1" if workplace == "Work from Home" else ""

    # Store search parameters
    if page == 1:
        window.app_state["current_page"] = 1
        window.app_state["search_params"] = {
            "keyword": keyword.strip(),
            "location": location,
            "job_type": job_type,
            "job_level": job_level,
            "posted_within": posted_within,
            "exp_start": exp_start,
            "exp_end": exp_end,
            "salary_start": salary_start,
            "salary_end": salary_end,
            "workplace": workplace,
            "is_fresher": is_fresher,
        }

    # Show loading message
    loading_window = show_loading(window, "Searching for jobs...")

    def search_thread():
        try:
            # Get results per page from state
            per_page = window.app_state.get("results_per_page", 10)
            
            # Perform search with API pagination
            results = scraper.search_jobs(
                keyword=keyword.strip(),
                location=location,
                job_type=job_type,
                job_level=job_level,
                posted_within=posted_within_api,
                experience_start=exp_start_int,
                experience_end=exp_end_int,
                salary_start=salary_start_int,
                salary_end=salary_end_int,
                workplace=workplace_api,
                is_fresher=is_fresher,
                page=page,
                results_per_page=per_page
            )

            # Store results object
            window.app_state["search_results"] = results
            window.app_state["current_page"] = page

            # Schedule GUI updates on main thread
            def update_ui():
                try:
                    loading_window.destroy()
                except:
                    pass
                show_results_view(window)
            
            window.after(0, update_ui)

        except Exception as e:
            # Schedule error handling on main thread
            def show_error():
                try:
                    loading_window.destroy()
                except:
                    pass
                show_message(window, "Error", f"Search failed: {str(e)}")
            
            window.after(0, show_error)
            logger.error(f"Advanced search error: {e}", exc_info=True)

    # Run search in background thread
    thread = threading.Thread(target=search_thread, daemon=True)
    thread.start()


def show_results_view(window: ctk.CTk) -> None:
    """Display search results with pagination."""
    content_frame = clear_content(window)
    window.app_state["current_view"] = "results"

    results = window.app_state.get("search_results")
    if not results:
        return
    
    current_page = window.app_state.get("current_page", 1)
    per_page = window.app_state.get("results_per_page", 10)
    
    # Get data from API results
    total_jobs = results.common.total_records_found  # Total across all pages
    page_jobs = results.all_jobs  # Jobs in current page
    total_pages = max(1, results.common.totalpages)  # Use API's total pages

    # Header
    header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    header_frame.pack(fill="x", pady=(12, 10), padx=16)

    header = ctk.CTkLabel(
        header_frame,
        text=f"Search Results ({total_jobs} jobs found)",
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    header.pack(side="left")

    # Results per page selector
    per_page_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    per_page_frame.pack(side="right", padx=10)
    
    ctk.CTkLabel(
        per_page_frame,
        text="Show:",
        font=ctk.CTkFont(size=14)
    ).pack(side="left", padx=(0, 5))
    
    per_page_var = ctk.StringVar(value=str(per_page))
    per_page_menu = ctk.CTkOptionMenu(
        per_page_frame,
        variable=per_page_var,
        values=["5", "10", "20", "50"],
        command=lambda choice: change_results_per_page(window, int(choice)),
        width=80,
        height=36
    )
    per_page_menu.pack(side="left")

    back_btn = ctk.CTkButton(
        header_frame, text="← Back to Search", command=lambda: show_search_view(window), width=150, height=40
    )
    back_btn.pack(side="right", padx=10)

    # Pagination info (always show)
    pagination_top = ctk.CTkFrame(content_frame, fg_color=("gray85", "gray20"))
    pagination_top.pack(fill="x", pady=(10, 10), padx=16)
    
    if total_pages > 1:
        create_pagination_controls(pagination_top, window, current_page, total_pages)
    else:
        # Show page info even with single page
        page_info = ctk.CTkLabel(
            pagination_top,
            text=f"Showing all {total_jobs} results (Page 1 of 1)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        page_info.pack(pady=12)

    # Results list (scrollable)
    results_scroll = ctk.CTkScrollableFrame(content_frame, width=1200, height=550)
    results_scroll.pack(pady=5, padx=16, fill="both", expand=True)

    if not page_jobs:
        no_results = ctk.CTkLabel(
            results_scroll,
            text="No jobs found. Try different keywords or filters.",
            font=ctk.CTkFont(size=14),
            text_color=("gray30", "gray70"),
        )
        no_results.pack(pady=50)
        return

    # Display current page jobs
    for job in page_jobs:
        create_job_card(results_scroll, job, window)
    
    # Pagination controls (bottom) - always show for consistency
    if total_pages > 1:
        pagination_bottom = ctk.CTkFrame(content_frame, fg_color=("gray85", "gray20"))
        pagination_bottom.pack(fill="x", pady=(10, 12), padx=16)
        create_pagination_controls(pagination_bottom, window, current_page, total_pages)


def create_pagination_controls(parent: ctk.CTkFrame, window: ctk.CTk, current_page: int, total_pages: int) -> None:
    """Create pagination controls."""
    pagination_frame = ctk.CTkFrame(parent, fg_color="transparent")
    pagination_frame.pack(pady=10)
    
    # Previous button
    prev_btn = ctk.CTkButton(
        pagination_frame,
        text="← Previous",
        command=lambda: go_to_page(window, current_page - 1),
        width=120,
        height=40,
        state="normal" if current_page > 1 else "disabled",
        font=ctk.CTkFont(size=14)
    )
    prev_btn.pack(side="left", padx=8)
    
    # Page info
    page_label = ctk.CTkLabel(
        pagination_frame,
        text=f"Page {current_page} of {total_pages}",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    page_label.pack(side="left", padx=20)
    
    # Next button
    next_btn = ctk.CTkButton(
        pagination_frame,
        text="Next →",
        command=lambda: go_to_page(window, current_page + 1),
        width=120,
        height=40,
        state="normal" if current_page < total_pages else "disabled",
        font=ctk.CTkFont(size=14)
    )
    next_btn.pack(side="left", padx=8)


def go_to_page(window: ctk.CTk, page: int) -> None:
    """Navigate to a specific page by fetching from API."""
    params = window.app_state.get("search_params", {})
    if params:
        # Check if advanced search parameters exist
        if "posted_within" in params:
            perform_advanced_search(
                window,
                params.get("keyword", ""),
                params.get("location", ""),
                params.get("job_type", ""),
                params.get("job_level", ""),
                params.get("posted_within", ""),
                params.get("exp_start", "0"),
                params.get("exp_end", "0"),
                params.get("salary_start", "0"),
                params.get("salary_end", "0"),
                params.get("workplace", ""),
                params.get("is_fresher", False),
                page=page
            )
        else:
            perform_search(
                window,
                params.get("keyword", ""),
                params.get("location", ""),
                params.get("job_type", ""),
                params.get("job_level", ""),
                page=page
            )


def change_results_per_page(window: ctk.CTk, new_per_page: int) -> None:
    """Change the number of results displayed per page."""
    window.app_state["results_per_page"] = new_per_page
    window.app_state["current_page"] = 1
    # Re-fetch from API with new page size
    params = window.app_state.get("search_params", {})
    if params:
        # Check if advanced search parameters exist
        if "posted_within" in params:
            perform_advanced_search(
                window,
                params.get("keyword", ""),
                params.get("location", ""),
                params.get("job_type", ""),
                params.get("job_level", ""),
                params.get("posted_within", ""),
                params.get("exp_start", "0"),
                params.get("exp_end", "0"),
                params.get("salary_start", "0"),
                params.get("salary_end", "0"),
                params.get("workplace", ""),
                params.get("is_fresher", False),
                page=1
            )
        else:
            perform_search(
                window,
                params.get("keyword", ""),
                params.get("location", ""),
                params.get("job_type", ""),
                params.get("job_level", ""),
                page=1
        )


def create_job_card(parent: ctk.CTkFrame, job, window: ctk.CTk) -> None:
    """Create a job card widget."""
    card = ctk.CTkFrame(parent, corner_radius=10)
    card.pack(pady=12, padx=16, fill="x")

    # Job content frame
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=16, pady=20)

    # Title and company
    title_label = ctk.CTkLabel(content, text=job.jobTitle, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
    title_label.pack(anchor="w", pady=(0, 5))

    company_label = ctk.CTkLabel(
        content, text=f"\ud83c\udfe2 {job.companyName}", font=ctk.CTkFont(size=14), text_color="gray70", anchor="w"
    )
    company_label.pack(anchor="w", pady=(0, 10))

    # Details row
    details_frame = ctk.CTkFrame(content, fg_color="transparent")
    details_frame.pack(fill="x", pady=(0, 10))

    if job.location:
        loc_label = ctk.CTkLabel(
            details_frame,
            text=f"\ud83d\udccd {job.location}",
            font=ctk.CTkFont(size=14),
            text_color=("gray30", "gray70"),
        )
        loc_label.pack(side="left", padx=(0, 20))

    if job.experience:
        exp_label = ctk.CTkLabel(
            details_frame,
            text=f"\ud83d\udcbc {job.experience}",
            font=ctk.CTkFont(size=14),
            text_color=("gray30", "gray70"),
        )
        exp_label.pack(side="left", padx=(0, 20))

    if job.deadline:
        deadline_label = ctk.CTkLabel(
            details_frame, text=f"\u23f0 Deadline: {job.deadline}", font=ctk.CTkFont(size=14), text_color="orange"
        )
        deadline_label.pack(side="left")

    # Buttons
    button_frame = ctk.CTkFrame(content, fg_color="transparent")
    button_frame.pack(fill="x", pady=(12, 0))

    view_btn = ctk.CTkButton(
        button_frame,
        text="\ud83d\udd17 View Details",
        command=lambda j=job: webbrowser.open(j.get_job_url()),
        width=130,
        height=40,
        font=ctk.CTkFont(size=14),
    )
    view_btn.pack(side="left", padx=(0, 10))

    save_btn = ctk.CTkButton(
        button_frame,
        text="\u2b50 Save Job",
        command=lambda j=job: save_job_to_db(window, j),
        width=120,
        height=40,
        font=ctk.CTkFont(size=14),
        fg_color="green",
        hover_color="darkgreen",
    )
    save_btn.pack(side="left", padx=(0, 10))

    apply_btn = ctk.CTkButton(
        button_frame,
        text="\u2713 Mark Applied",
        command=lambda j=job: mark_job_applied(window, j),
        width=130,
        height=40,
        font=ctk.CTkFont(size=14),
        fg_color="blue",
        hover_color="darkblue",
    )
    apply_btn.pack(side="left")


def show_saved_jobs_view(window: ctk.CTk) -> None:
    """Display saved jobs."""
    content_frame = clear_content(window)
    window.app_state["current_view"] = "saved"

    # Header
    header = ctk.CTkLabel(content_frame, text="Saved Jobs", font=ctk.CTkFont(size=48, weight="bold"))
    header.pack(pady=(12, 20))

    # Get saved jobs from database
    session = orm.get_session()
    try:
        jobs = session.query(orm.Job).filter_by(is_active=True).order_by(orm.Job.created_at.desc()).all()

        if not jobs:
            no_jobs = ctk.CTkLabel(
                content_frame,
                text="No saved jobs yet.\n\nSearch for jobs and save your favorites!",
                font=ctk.CTkFont(size=14),
                text_color=("gray30", "gray70"),
                justify="center",
            )
            no_jobs.pack(pady=120)
            return

        # Results list
        results_scroll = ctk.CTkScrollableFrame(content_frame, width=1200, height=700)
        results_scroll.pack(pady=12, padx=16, fill="both", expand=True)

        for job in jobs:
            create_saved_job_card(results_scroll, job, window)

    finally:
        session.close()


def create_saved_job_card(parent: ctk.CTkFrame, job, window: ctk.CTk) -> None:
    """Create a saved job card widget."""
    card = ctk.CTkFrame(parent, corner_radius=10)
    card.pack(pady=12, padx=16, fill="x")

    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=16, pady=20)

    # Title
    title_label = ctk.CTkLabel(content, text=job.title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
    title_label.pack(anchor="w", pady=(0, 5))

    # Company
    company_label = ctk.CTkLabel(
        content, text=f"\ud83c\udfe2 {job.company}", font=ctk.CTkFont(size=14), text_color="gray70", anchor="w"
    )
    company_label.pack(anchor="w", pady=(0, 10))

    # Details
    if job.location or job.salary_range:
        details_text = ""
        if job.location:
            details_text += f"\ud83d\udccd {job.location}  "
        if job.salary_range:
            details_text += f"\ud83d\udcb5 {job.salary_range}"

        details_label = ctk.CTkLabel(
            content, text=details_text, font=ctk.CTkFont(size=14), text_color=("gray30", "gray70")
        )
        details_label.pack(anchor="w", pady=(0, 10))

    # Buttons
    button_frame = ctk.CTkFrame(content, fg_color="transparent")
    button_frame.pack(fill="x", pady=(12, 0))

    if job.url:
        view_btn = ctk.CTkButton(
            button_frame, text="\ud83d\udd17 View Job", command=lambda: webbrowser.open(job.url), width=120, height=40
        )
        view_btn.pack(side="left", padx=(0, 10))

    remove_btn = ctk.CTkButton(
        button_frame,
        text="\u274c Remove",
        command=lambda j_id=job.id: remove_saved_job(window, j_id),
        width=100,
        height=40,
        fg_color="red",
        hover_color="darkred",
    )
    remove_btn.pack(side="left")


def show_applications_view(window: ctk.CTk) -> None:
    """Display job applications."""
    content_frame = clear_content(window)
    window.app_state["current_view"] = "applications"

    # Header
    header = ctk.CTkLabel(content_frame, text="My Applications", font=ctk.CTkFont(size=48, weight="bold"))
    header.pack(pady=(12, 20))

    # Get applications
    session = orm.get_session()
    try:
        applications = (
            session.query(orm.JobApplication, orm.Job)
            .join(orm.Job)
            .order_by(orm.JobApplication.created_at.desc())
            .all()
        )

        if not applications:
            no_apps = ctk.CTkLabel(
                content_frame,
                text="No applications yet.\n\nMark jobs as applied to track them here!",
                font=ctk.CTkFont(size=14),
                text_color=("gray30", "gray70"),
                justify="center",
            )
            no_apps.pack(pady=120)
            return

        # Applications list
        apps_scroll = ctk.CTkScrollableFrame(content_frame, width=1200, height=700)
        apps_scroll.pack(pady=12, padx=16, fill="both", expand=True)

        for app, job in applications:
            create_application_card(apps_scroll, app, job, window)

    finally:
        session.close()


def create_application_card(parent: ctk.CTkFrame, app, job, window: ctk.CTk) -> None:
    """Create an application card widget."""
    card = ctk.CTkFrame(parent, corner_radius=10)
    card.pack(pady=12, padx=16, fill="x")

    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=16, pady=20)

    # Job title
    title_label = ctk.CTkLabel(content, text=job.title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
    title_label.pack(anchor="w", pady=(0, 5))

    # Company and status
    info_frame = ctk.CTkFrame(content, fg_color="transparent")
    info_frame.pack(fill="x", pady=(0, 10))

    company_label = ctk.CTkLabel(
        info_frame, text=f"\ud83c\udfe2 {job.company}", font=ctk.CTkFont(size=14), text_color="gray70"
    )
    company_label.pack(side="left", padx=(0, 20))

    status_colors = {
        "interested": "orange",
        "applied": "blue",
        "interview": "purple",
        "rejected": "red",
        "accepted": "green",
    }
    status_color = status_colors.get(app.status, "gray")

    status_label = ctk.CTkLabel(
        info_frame,
        text=f"\u25cf {app.status.title()}",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=status_color,
    )
    status_label.pack(side="left")

    # Date
    date_label = ctk.CTkLabel(
        content,
        text=f"Added: {app.created_at.strftime('%b %d, %Y')}",
        font=ctk.CTkFont(size=14),
        text_color=("gray30", "gray70"),
    )
    date_label.pack(anchor="w", pady=(0, 10))

    # Notes if available
    if app.notes:
        notes_label = ctk.CTkLabel(content, text=f"Notes: {app.notes}", font=ctk.CTkFont(size=14), anchor="w")
        notes_label.pack(anchor="w", pady=(0, 10))

    # Buttons
    button_frame = ctk.CTkFrame(content, fg_color="transparent")
    button_frame.pack(fill="x", pady=(12, 0))

    if job.url:
        view_btn = ctk.CTkButton(
            button_frame, text="\ud83d\udd17 View Job", command=lambda: webbrowser.open(job.url), width=120, height=40
        )
        view_btn.pack(side="left", padx=(0, 10))

    # Status update dropdown
    status_var = ctk.StringVar(value=app.status)
    status_menu = ctk.CTkOptionMenu(
        button_frame,
        variable=status_var,
        values=["interested", "applied", "interview", "rejected", "accepted"],
        command=lambda s, a_id=app.id, lbl=status_label: update_application_status_ui(window, a_id, s, lbl),
        width=150,
        height=40,
    )
    status_menu.pack(side="left")


def show_dashboard_view(window: ctk.CTk) -> None:
    """Display dashboard with statistics."""
    content_frame = clear_content(window)
    window.app_state["current_view"] = "dashboard"

    # Header
    header = ctk.CTkLabel(content_frame, text="Dashboard", font=ctk.CTkFont(size=48, weight="bold"))
    header.pack(pady=(12, 20))

    # Get statistics
    stats = get_user_statistics()

    # Scrollable container for dashboard content
    scroll_frame = ctk.CTkScrollableFrame(content_frame, width=1200, height=700)
    scroll_frame.pack(pady=12, padx=16, fill="both", expand=True)

    # Stats grid
    stats_grid = ctk.CTkFrame(scroll_frame)
    stats_grid.pack(pady=20, padx=100, fill="x")

    stat_items = [
        ("Total Saved Jobs", stats["saved_jobs"], "blue"),
        ("Total Applications", stats["applications"], "green"),
        ("Interviews", stats["interviews"], "purple"),
        ("Offers Received", stats["offers"], "gold"),
    ]

    for i, (label, value, color) in enumerate(stat_items):
        stat_box = ctk.CTkFrame(stats_grid, width=250, height=150, fg_color=color)
        stat_box.grid(row=i // 2, column=i % 2, padx=16, pady=12, sticky="nsew")
        stat_box.grid_propagate(False)

        value_label = ctk.CTkLabel(
            stat_box, text=str(value), font=ctk.CTkFont(size=48, weight="bold"), text_color="white"
        )
        value_label.pack(pady=(25, 5))

        label_text = ctk.CTkLabel(stat_box, text=label, font=ctk.CTkFont(size=14), text_color="white")
        label_text.pack()

    stats_grid.grid_columnconfigure(0, weight=1)
    stats_grid.grid_columnconfigure(1, weight=1)

    # Recent activity
    activity_label = ctk.CTkLabel(scroll_frame, text="Recent Activity", font=ctk.CTkFont(size=14, weight="bold"))
    activity_label.pack(pady=(12, 20))

    activity_frame = ctk.CTkFrame(scroll_frame, width=900)
    activity_frame.pack(pady=12, padx=100, fill="x")

    # Show recent applications
    session = orm.get_session()
    try:
        recent = (
            session.query(orm.JobApplication, orm.Job)
            .join(orm.Job)
            .order_by(orm.JobApplication.created_at.desc())
            .limit(5)
            .all()
        )

        if recent:
            for app, job in recent:
                activity_item = ctk.CTkLabel(
                    activity_frame,
                    text=f"\u2022 {app.status.title()}: {job.title} at {job.company} - {app.created_at.strftime('%b %d')}",
                    font=ctk.CTkFont(size=14),
                    anchor="w",
                )
                activity_item.pack(anchor="w", padx=16, pady=5)
        else:
            no_activity = ctk.CTkLabel(
                activity_frame, text="No recent activity", font=ctk.CTkFont(size=14), text_color=("gray30", "gray70")
            )
            no_activity.pack(pady=12)

    finally:
        session.close()


# ============================================================================
# Helper Functions
# ============================================================================


def get_user_statistics() -> Dict[str, int]:
    """Get user statistics from database."""
    session = orm.get_session()
    try:
        saved_jobs = session.query(orm.Job).filter_by(is_active=True).count()
        applications = session.query(orm.JobApplication).count()
        interviews = session.query(orm.JobApplication).filter_by(status="interview").count()
        offers = session.query(orm.JobApplication).filter_by(status="accepted").count()

        return {"saved_jobs": saved_jobs, "applications": applications, "interviews": interviews, "offers": offers}
    finally:
        session.close()


def save_job_to_db(window: ctk.CTk, job) -> None:
    """Save a job to the database."""
    try:
        # Parse deadline
        deadline = None
        if job.deadlineDB:
            try:
                deadline = job.deadlineDB
            except:
                pass

        # Parse posted date
        posted_date = None
        if job.publishDate:
            try:
                posted_date = job.publishDate
            except:
                pass

        job_data = {
            "external_id": job.Jobid,
            "title": job.jobTitle,
            "company": job.companyName,
            "location": job.location,
            "experience_required": job.experience,
            "description": job.jobContext or "",
            "posted_date": posted_date,
            "deadline": deadline,
            "url": job.get_job_url(),
            "source": "bdjobs",
        }

        job_id = orm.save_job(job_data)
        show_message(window, "Success", f"Job saved: {job.jobTitle}")
        logger.info(f"Saved job {job_id}: {job.jobTitle}")

    except Exception as e:
        show_message(window, "Error", f"Failed to save job: {str(e)}")
        logger.error(f"Error saving job: {e}", exc_info=True)


def mark_job_applied(window: ctk.CTk, job) -> None:
    """Mark a job as applied and save to database."""
    try:
        # First save the job
        deadline = None
        if job.deadlineDB:
            try:
                deadline = job.deadlineDB
            except:
                pass

        posted_date = None
        if job.publishDate:
            try:
                posted_date = job.publishDate
            except:
                pass

        job_data = {
            "external_id": job.Jobid,
            "title": job.jobTitle,
            "company": job.companyName,
            "location": job.location,
            "experience_required": job.experience,
            "description": job.jobContext or "",
            "posted_date": posted_date,
            "deadline": deadline,
            "url": job.get_job_url(),
            "source": "bdjobs",
        }

        job_id = orm.save_job(job_data)

        # Get or create default profile
        profiles = orm.get_all_profiles()
        if not profiles:
            profile_id = orm.create_profile({"name": "Default User", "email": "user@example.com"})
        else:
            profile_id = profiles[0]["id"]

        # Create application
        orm.create_application(profile_id, job_id, status="applied", notes="")

        show_message(window, "Success", f"Marked as applied: {job.jobTitle}")
        logger.info(f"Marked job {job_id} as applied")

    except Exception as e:
        show_message(window, "Error", f"Failed to mark as applied: {str(e)}")
        logger.error(f"Error marking job as applied: {e}", exc_info=True)


def remove_saved_job(window: ctk.CTk, job_id: int) -> None:
    """Remove a saved job from database."""
    try:
        session = orm.get_session()
        try:
            job = session.query(orm.Job).filter_by(id=job_id).first()
            if job:
                job.is_active = False
                session.commit()
                show_message(window, "Success", "Job removed from saved jobs")
                show_saved_jobs_view(window)  # Refresh view
        finally:
            session.close()
    except Exception as e:
        show_message(window, "Error", f"Failed to remove job: {str(e)}")
        logger.error(f"Error removing job: {e}", exc_info=True)


def update_application_status_ui(window: ctk.CTk, app_id: int, new_status: str, status_label: ctk.CTkLabel) -> None:
    """Update application status."""
    try:
        orm.update_application_status(app_id, new_status)
        logger.info(f"Updated application {app_id} status to {new_status}")
        
        # Update just the status label color and text
        status_colors = {
            "interested": "orange",
            "applied": "blue",
            "interview": "purple",
            "rejected": "red",
            "accepted": "green",
        }
        status_color = status_colors.get(new_status, "gray")
        status_label.configure(text=f"● {new_status.title()}", text_color=status_color)
        
    except Exception as e:
        show_message(window, "Error", f"Failed to update status: {str(e)}")
        logger.error(f"Error updating status: {e}", exc_info=True)


def show_message(window: ctk.CTk, title: str, message: str) -> None:
    """Show a message dialog."""
    dialog = ctk.CTkToplevel(window)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.transient(window)
    dialog.grab_set()

    # Center dialog
    dialog.update_idletasks()
    x = window.winfo_x() + (window.winfo_width() - dialog.winfo_width()) // 2
    y = window.winfo_y() + (window.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")

    msg_label = ctk.CTkLabel(dialog, text=message, font=ctk.CTkFont(size=14), wraplength=350)
    msg_label.pack(pady=20, padx=16)

    ok_button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=100)
    ok_button.pack(pady=12)


def show_loading(window: ctk.CTk, message: str) -> ctk.CTkToplevel:
    """Show a loading dialog."""
    loading = ctk.CTkToplevel(window)
    loading.title("Please Wait")
    loading.geometry("350x150")
    loading.transient(window)
    loading.grab_set()

    # Center loading dialog
    loading.update_idletasks()
    x = window.winfo_x() + (window.winfo_width() - loading.winfo_width()) // 2
    y = window.winfo_y() + (window.winfo_height() - loading.winfo_height()) // 2
    loading.geometry(f"+{x}+{y}")

    msg_label = ctk.CTkLabel(loading, text=message, font=ctk.CTkFont(size=14))
    msg_label.pack(pady=20)

    progress = ctk.CTkProgressBar(loading, mode="indeterminate", width=300)
    progress.pack(pady=12)
    progress.start()

    return loading


# ============================================================================
# Application Entry Point
# ============================================================================


def run_application() -> None:
    """Initialize and run the application."""
    try:
        window = create_main_window()
        window.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise
    finally:
        scraper.close_http_client()
        orm.close_database()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    run_application()
