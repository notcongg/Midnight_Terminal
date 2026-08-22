from pathlib import Path

def display_path(path):
    home = Path.home()

    try:
        rel = path.relative_to(home)

        if rel == Path("."):
            return f"~/usr/{home.name}"

        return f"~/usr/{home.name}/{rel}".replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")