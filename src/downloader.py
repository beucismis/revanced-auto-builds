import json
import logging
from pathlib import Path
from src import (
    utils,
    apkpure,
    session,
    uptodown,
    apkmirror
)

def download_resource(url: str, name: str = None) -> Path:
    with session.get(url, stream=True) as res:
        res.raise_for_status()
        final_url = res.url

        if not name:
            name = utils.extract_filename(res, fallback_url=final_url)

        filepath = Path(name)
        total_size = int(res.headers.get('content-length', 0))
        downloaded_size = 0

        with filepath.open("wb") as file:
            for chunk in res.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)

        logging.info(
            f"URL: {final_url} [{downloaded_size}/{total_size}] -> \"{filepath}\" [1]"
        )

    return filepath

def download_required(source: str) -> tuple[list[Path], str]:
    source_path = Path("sources") / f"{source}.json"
    with source_path.open() as json_file:
        repos_info = json.load(json_file)

    name = repos_info[0]["name"]
    downloaded_files = []

    for repo_info in repos_info[1:]:
        user = repo_info['user']
        repo = repo_info['repo']
        tag = repo_info['tag']

        release = utils.detect_github_release(user, repo, tag)
        for asset in release["assets"]:
            if asset["name"].endswith(".asc"):
                continue
            filepath = download_resource(asset["browser_download_url"])
            downloaded_files.append(filepath)

    return downloaded_files, name

def download_platform(app_name: str, platform: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    """
    Download APK from a specific platform.
    
    Args:
        app_name: Name of the app
        platform: Platform name (apkmirror, apkpure, uptodown)
        cli: Path to CLI jar
        patches: Path to patches file
        arch: Architecture (optional)
    
    Returns:
        Tuple of (filepath, version) or (None, None) if failed
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        Exception: For other errors
    """
    try:
        config_path = Path("apps") / platform / f"{app_name}.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open() as json_file:
            config = json.load(json_file)
        
        # Override arch if specified
        if arch:
            config['arch'] = arch

        # Get version from config or determine supported version
        version = config.get("version")
        
        # If version is empty string or None, determine it
        if not version:
            # First try to get supported version from patches
            try:
                version = utils.get_supported_version(config['package'], cli, patches)
                logging.info(f"Determined supported version from patches: {version}")
            except Exception as e:
                logging.debug(f"Could not determine version from patches: {e}")
                version = None
        
        # If still no version, try to get latest from platform
        if not version:
            platform_module = globals()[platform]
            version = platform_module.get_latest_version(app_name, config)
            logging.info(f"Using latest version from {platform}: {version}")
        
        # If STILL no version, this is a problem
        if not version:
            raise ValueError(f"Could not determine version for {app_name} on {platform}")
        
        platform_module = globals()[platform]
        download_link = platform_module.get_download_link(version, app_name, config)
        
        if not download_link:
            raise ValueError(f"Could not get download link for {app_name} v{version} on {platform}")
        
        logging.info(f"Downloading {app_name} v{version} from {platform}...")
        filepath = download_resource(download_link)
        
        return filepath, version 

    except FileNotFoundError as e:
        # Re-raise FileNotFoundError so caller can handle it
        raise
    except Exception as e:
        logging.error(f"Error downloading from {platform}: {e}")
        return None, None

# Update the specific download functions
def download_apkmirror(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    """Download from APKMirror. Raises FileNotFoundError if config missing."""
    return download_platform(app_name, "apkmirror", cli, patches, arch)

def download_apkpure(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    """Download from APKPure. Raises FileNotFoundError if config missing."""
    return download_platform(app_name, "apkpure", cli, patches, arch)

def download_uptodown(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    """Download from Uptodown. Raises FileNotFoundError if config missing."""
    return download_platform(app_name, "uptodown", cli, patches, arch)

def download_apkeditor() -> Path:
    release = utils.detect_github_release("REAndroid", "APKEditor", "latest")

    for asset in release["assets"]:
        if asset["name"].startswith("APKEditor") and asset["name"].endswith(".jar"):
            return download_resource(asset["browser_download_url"])

    raise RuntimeError("APKEditor .jar file not found in the latest release")
