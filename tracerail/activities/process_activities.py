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

    # For local development, we assume the definitions are in a sibling directory
    # to the `tracerail-core` project. This path needs to be updated for
    # containerized environments.
    # A more robust solution would use an absolute path from an env var.
    # The filename convention is assumed to be `process_name_v_version.yml`.
    filename = f"{process_name}_v{version}.yml".replace(".", "_")

    # This relative path is fragile and assumes execution from the root of the monorepo-style layout.
    # It will need to be configured correctly in the running environment (e.g., Docker WORKDIR).
    # We will search for the file in a conventional location.
    # Let's assume the definitions are mounted at `/app/process_definitions` in the container.
    definitions_dir = Path(activity.info().env.get("PROCESS_DEFINITIONS_PATH", "/app/process_definitions"))

    process_file = definitions_dir / filename

    activity.logger.info("Attempting to load from path", path=str(process_file))

    if not process_file.exists():
        raise FileNotFoundError(f"Process definition not found at {process_file}")

    with open(process_file, 'r') as f:
        definition = yaml.safe_load(f)

    activity.logger.info("Successfully loaded process definition.", process_name=process_name)
    return definition
