import os
import platform


def install_desktop_file(
    template: str,
    name: str,
    icon_folder: str,
    bin_folder: str,
    terminal: bool,
    startup_wm_class: str | None,
    options: str = "",
) -> str:
    """Write a .desktop entry under XDG_DATA_HOME/applications/ and return its path.

    Raises NotImplementedError on non-Linux platforms.
    """
    if platform.system() != "Linux":
        raise NotImplementedError("Desktop-file installation is only supported on Linux.")

    simple_name = name.lower().replace(" ", "-").replace(os.path.sep, "-")
    resolved_wm_class = startup_wm_class or f"crx_mpnasdandanpmm_{simple_name}"

    home = os.environ.get("HOME", os.path.expanduser("~"))
    xdg_share = os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share"))
    xdg_app_data = os.path.join(xdg_share, "applications")
    os.makedirs(xdg_app_data, exist_ok=True)

    content = template.format(
        icon_folder=icon_folder,
        bin_folder=bin_folder,
        name=name,
        terminal=str(terminal).lower(),
        StartupWMClass=resolved_wm_class,
        options=options,
    )

    desktop_filepath = os.path.join(xdg_app_data, f"{simple_name}.desktop")
    with open(desktop_filepath, "w") as f:
        f.write(content)

    return desktop_filepath
