import os
from pathlib import Path
import yaml
from temporalio import activity

@activity.defn(name="load_process_definition_activity")
async def load_process_definition(process_name: str, version: str) -> dict:
    """
    Loads a specific version of a process definition from a YAML file.

    This activity assumes that process definitions are stored in a known
    directory structure. In a real production system, this path would likely
    be an environment variable or a more robust discovery mechanism.

    Args:
        process_name: The name of the process to load (e.g., "expense_approval").
        version: The version of the process to load (e.g., "1.0.0").

    Returns:
        A dictionary containing the parsed process definition.
    """
    activity.logger.info(
        "Loading process definition",
        process_name=process_name,
        version=version,
    )

    # The filename convention is assumed to be `process_name_v_version.yml`.
    filename = f"{process_name}_v{version}.yml".replace(".", "_")

    # The worker's environment provides the path to the process definitions directory.
    # This makes the activity configurable and testable.
    definitions_path = os.getenv("PROCESS_DEFINITIONS_PATH", "process_definitions")
    definitions_dir = Path(definitions_path)

    process_file = definitions_dir / filename

    activity.logger.info("Attempting to load from path", path=str(process_file))

    if not process_file.exists():
        # In a container, the current working directory is /app.
        # We'll check for the definitions relative to that as a fallback.
        process_file_app = Path("/app") / definitions_dir / filename
        if process_file_app.exists():
            process_file = process_file_app
        else:
             raise FileNotFoundError(f"Process definition not found at '{process_file}' or '{process_file_app}'")


    with open(process_file, 'r') as f:
        definition = yaml.safe_load(f)

    activity.logger.info("Successfully loaded process definition.", process_name=process_name)
    return definition
