#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HuggingFace LoRA Wizard – Upload/Download (RU/EN)
Version: 1.1.0 - Production Release
All critical bugs fixed and tested.
"""

import os
import sys
import re
import shutil
import subprocess
import datetime
import stat
import atexit
import signal
import time

# ============================================================================
# CLEANUP MANAGEMENT
# ============================================================================

# Global cleanup list for temporary directories
CLEANUP_DIRS = []

def cleanup_on_exit():
    """Clean up temporary directories on exit."""
    for dir_path in CLEANUP_DIRS:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"⚠️  Cleaned up: {dir_path}")
            except Exception:
                pass

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print()
    print("⚠️  Interrupted by user. Cleaning up...")
    cleanup_on_exit()
    sys.exit(1)

# Register cleanup handlers
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)


# ============================================================================
# SECURITY UTILITIES
# ============================================================================

def mask_sensitive_data(text, token):
    """
    Mask token in text for safe output.
    
    Args:
        text: Text that might contain sensitive data
        token: Token to mask
    
    Returns:
        Text with token replaced by masked version
    """
    if not token or len(token) < 8:
        return text
    
    # Replace token with masked version (show first 4 and last 4 chars)
    masked = f"{token[:4]}...{token[-4:]}"
    return text.replace(token, masked)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_repo_id(repo_id):
    """
    Validate repository ID format.
    
    Format: username/reponame or just reponame
    Allowed characters: alphanumeric, dash, underscore
    
    Args:
        repo_id: Repository ID to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Hugging Face style:
    # - repo_name or namespace/repo_name
    # - allowed chars: letters, numbers, '-', '_', '.'
    # - cannot start/end with '-' or '.'
    # - no consecutive '--' or '..'
    # - total length up to 96 chars
    if not repo_id or len(repo_id) > 96:
        err("❌ Invalid repository ID format.")
        print("   Repo ID length must be 1..96 characters")
        return False

    if repo_id.count("/") > 1:
        err("❌ Invalid repository ID format.")
        print("   Format: username/reponame or just reponame")
        return False

    parts = repo_id.split("/")
    segment_pattern = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]$|^[A-Za-z0-9]$')

    for part in parts:
        if not part:
            err("❌ Invalid repository ID format.")
            print("   Empty namespace or repository name")
            return False

        if not segment_pattern.match(part):
            err("❌ Invalid repository ID format.")
            print("   Allowed: letters, numbers, dash (-), underscore (_), dot (.)")
            print("   Name cannot start/end with '-' or '.'")
            return False

        if "--" in part or ".." in part:
            err("❌ Invalid repository ID format.")
            print("   '--' and '..' are not allowed")
            return False

    return True


# ============================================================================
# GIT OPERATIONS WITH TOKEN
# ============================================================================

def git_clone_with_token(repo_id, dest_dir, token):
    """
    Clone HuggingFace repository using token authentication.
    
    Args:
        repo_id: Repository ID (e.g., "username/repo")
        dest_dir: Destination directory
        token: HuggingFace access token
    
    Returns:
        True if successful, False otherwise
    """
    # Use OAuth2 token in URL for authentication
    clone_url = f"https://oauth2:{token}@huggingface.co/{repo_id}"
    
    # Clone with minimal output, disable terminal prompts
    result = subprocess.run(
        ["git", "clone", clone_url, dest_dir],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    )
    
    if result.returncode != 0:
        # Get error message and mask token
        err_msg = result.stderr.decode('utf-8', errors='ignore')
        err_msg = mask_sensitive_data(err_msg, token)
        err(f"Git clone failed: {err_msg}")
        return False
    
    return True


def git_clone_with_progress(repo_id, dest_dir, token):
    """
    Clone repository with simple progress indicator.
    
    Args:
        repo_id: Repository ID
        dest_dir: Destination directory  
        token: HuggingFace access token
    
    Returns:
        True if successful, False otherwise
    """
    clone_url = f"https://oauth2:{token}@huggingface.co/{repo_id}"
    
    say("⏳ Cloning repository...")
    
    # Start clone process
    process = subprocess.Popen(
        ["git", "clone", "--progress", clone_url, dest_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    )
    
    # Simple spinner animation
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    
    # Show spinner while cloning
    while process.poll() is None:
        print(f"\r{spinner[idx % len(spinner)]} Cloning...", end='', flush=True)
        idx += 1
        time.sleep(0.1)
    
    # Clear spinner line
    print("\r" + " " * 30 + "\r", end='', flush=True)
    
    if process.returncode != 0:
        # Mask token in any error output
        output = process.stdout.read() if process.stdout else ""
        output = mask_sensitive_data(output, token)
        err(f"Git clone failed: {output}")
        return False
    
    ok("✅ Repository cloned successfully")
    return True


# ============================================================================
# DOWNLOAD WITH PROGRESS
# ============================================================================

def download_file_with_progress(repo_id, filename, target_dir, token=None):
    """
    Download file from HuggingFace with progress indication.
    
    Args:
        repo_id: Repository ID
        filename: File to download
        target_dir: Target directory
        token: Optional token (uses default if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    from huggingface_hub import hf_hub_download
    
    try:
        print(f"⏳ Downloading: {filename}")
        
        # Download with default progress bar from huggingface_hub
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=target_dir,
            token=token
        )
        
        ok(f"✅ Downloaded: {filename}")
        return True
        
    except Exception as e:
        err_msg = str(e)
        if token:
            err_msg = mask_sensitive_data(err_msg, token)
        err(f"Download failed: {err_msg}")
        return False


def resolve_lora_target_dir(base_dir=None):
    """
    Resolve the best local directory for LoRA downloads.

    Priority:
    1) Existing directories that look like models/.../lora(s) or similar
    2) Existing models directory -> create models/loras
    3) Fallback create ./models/loras

    Args:
        base_dir: Starting directory for upward search

    Returns:
        tuple(path, status) where status in:
        - found_existing
        - created_in_models
        - created_fallback
        - error
    """
    base_dir = os.path.abspath(base_dir or os.getcwd())

    # Optional explicit override
    override_dir = os.getenv("LORA_TARGET_DIR") or os.getenv("LORAS_DIR")
    if override_dir:
        target = os.path.abspath(os.path.expanduser(override_dir))
        try:
            os.makedirs(target, exist_ok=True)
            return target, "found_existing"
        except Exception:
            return target, "error"

    ignore_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__"}

    def is_lora_like(name):
        low = name.lower()
        return ("lora" in low) or ("lycoris" in low)

    def score_path(path):
        low = path.lower().replace("\\", "/")
        parts = [p for p in low.split("/") if p]
        leaf = parts[-1] if parts else ""
        score = 0
        if leaf in ("loras", "lora", "lycoris"):
            score += 100
        elif is_lora_like(leaf):
            score += 70
        if "models" in parts:
            score += 40
        if len(parts) >= 2 and parts[-2] == "models":
            score += 30
        return score

    # Build search roots: current dir + parents (up to 6 levels)
    roots = []
    cur = base_dir
    for _ in range(7):
        if cur not in roots:
            roots.append(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    # Include common Linux workspace path if present
    if os.path.isdir("/workspace") and "/workspace" not in roots:
        roots.append("/workspace")

    lora_candidates = []
    models_dirs = []

    # Search limited depth to keep it fast
    for root in roots:
        if not os.path.isdir(root):
            continue
        root_depth = root.rstrip("/\\").count(os.sep)
        for walk_root, dirnames, _ in os.walk(root):
            depth = walk_root.rstrip("/\\").count(os.sep) - root_depth
            if depth > 4:
                dirnames[:] = []
                continue

            dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".")]

            for d in dirnames:
                full_path = os.path.join(walk_root, d)
                d_low = d.lower()
                if d_low == "models":
                    models_dirs.append(full_path)
                if is_lora_like(d_low):
                    lora_candidates.append(full_path)

    # 1) Existing lora-like directory (prefer models/.../loras)
    if lora_candidates:
        best = sorted(set(lora_candidates), key=lambda p: (score_path(p), -len(p)), reverse=True)[0]
        return best, "found_existing"

    # 2) Existing models dir -> create models/loras
    if models_dirs:
        best_models = sorted(set(models_dirs), key=lambda p: (-(p.count(os.sep)), len(p)))[0]
        target = os.path.join(best_models, "loras")
        try:
            os.makedirs(target, exist_ok=True)
            return target, "created_in_models"
        except Exception:
            pass

    # 3) Fallback: ./models/loras
    fallback = os.path.join(base_dir, "models", "loras")
    try:
        os.makedirs(fallback, exist_ok=True)
        return fallback, "created_fallback"
    except Exception:
        return fallback, "error"


# ============================================================================
# RETRY LOGIC
# ============================================================================

def retry_on_error(func, max_retries=3, delay=2):
    """
    Retry a function on failure with exponential backoff.
    
    Args:
        func: Function to retry (should take no arguments)
        max_retries: Maximum number of retry attempts
        delay: Initial delay in seconds (doubles each retry)
    
    Returns:
        Function result if successful
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                warn(f"⚠️  Attempt {attempt + 1}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Last attempt failed
                err(f"❌ All {max_retries} attempts failed.")
    
    # All retries exhausted
    raise last_exception


"""
============================================================================
USAGE EXAMPLES (DOCS ONLY - do not execute)
============================================================================

In main code, replace git clone calls:

OLD:
    result = subprocess.run(["git", "clone", f"https://huggingface.co/{repo_id}", repo_dir])
    if result.returncode != 0:
        err("Git clone failed.")
        sys.exit(1)

NEW (simple):
    if not git_clone_with_token(repo_id, repo_dir, token):
        sys.exit(1)

NEW (with progress):
    if not git_clone_with_progress(repo_id, repo_dir, token):
        sys.exit(1)

Replace download calls:

OLD:
    hf_hub_download(repo_id=selected_repo, filename=selected_file, local_dir=target_dir)

NEW:
    if not download_file_with_progress(selected_repo, selected_file, target_dir, token):
        sys.exit(1)
"""



# ============================================================================
# TOML CONFIG PARSER - Collect training info
# ============================================================================

def collect_training_info(run_dir):
    """
    Collect training configuration from .toml files in run directory.
    
    Searches for .toml files in run_dir and parent directories,
    extracts key training parameters.
    
    Args:
        run_dir: Path to the run directory with epoch folders
    
    Returns:
        dict with training parameters, or empty dict if nothing found
    """
    import configparser
    
    training_info = {}
    toml_files = []
    
    # Search for .toml files in run_dir and up to 3 levels up
    search_paths = [run_dir]
    parent = os.path.dirname(run_dir)
    for _ in range(3):
        if parent and parent != run_dir:
            search_paths.append(parent)
            parent = os.path.dirname(parent)
    
    # Also check common locations
    search_paths.extend([
        "/workspace",
        "/workspace/diffusion_pipe_working_folder",
        os.path.join(run_dir, ".."),
    ])
    
    for search_path in search_paths:
        if not os.path.isdir(search_path):
            continue
        try:
            for f in os.listdir(search_path):
                if f.endswith(".toml"):
                    full_path = os.path.join(search_path, f)
                    if full_path not in toml_files:
                        toml_files.append(full_path)
        except Exception:
            pass
    
    if not toml_files:
        return training_info
    
    # Parse toml files (simple parser without external dependencies)
    def parse_toml_simple(filepath):
        """Simple TOML parser for basic key=value pairs."""
        data = {}
        current_section = ""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Section header
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1].strip()
                        continue
                    # Key = value
                    if '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # Remove inline comments
                        if '#' in value:
                            value = value.split('#')[0].strip().strip('"').strip("'")
                        full_key = f"{current_section}.{key}" if current_section else key
                        data[full_key] = value
                        # Also store without section for easier access
                        data[key] = value
        except Exception:
            pass
        return data
    
    # Keys we're interested in
    interesting_keys = [
        # Network settings
        'network_dim', 'network_alpha', 'rank', 'alpha',
        'network_module', 'network_type',
        # Training settings
        'learning_rate', 'lr', 'unet_lr', 'text_encoder_lr',
        'max_train_epochs', 'max_train_steps', 'epochs',
        'train_batch_size', 'batch_size',
        'resolution', 'width', 'height',
        'optimizer_type', 'optimizer',
        'lr_scheduler', 'scheduler',
        'seed',
        # Model info
        'pretrained_model_name_or_path', 'model_path', 'base_model',
        'output_dir', 'output_name',
        # Dataset
        'train_data_dir', 'dataset_config',
        'caption_extension',
        # Other
        'mixed_precision', 'gradient_checkpointing',
        'save_every_n_epochs', 'save_model_as',
    ]
    
    # Collect data from all toml files
    for toml_file in toml_files:
        parsed = parse_toml_simple(toml_file)
        for key in interesting_keys:
            if key in parsed and key not in training_info:
                training_info[key] = parsed[key]
        # Also store which files were parsed
        if 'source_files' not in training_info:
            training_info['source_files'] = []
        training_info['source_files'].append(os.path.basename(toml_file))
    
    return training_info


def save_training_info(training_info, output_path):
    """
    Save training info to a text file.
    
    Args:
        training_info: dict with training parameters
        output_path: path to save the file
    
    Returns:
        True if saved, False otherwise
    """
    if not training_info:
        return False
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("  LoRA Training Information\n")
            f.write("  Collected by NiHao OFM LoRA Wizard\n")
            f.write("=" * 50 + "\n\n")
            
            # Group by category
            categories = {
                "Network Settings": ['network_dim', 'network_alpha', 'rank', 'alpha', 'network_module', 'network_type'],
                "Training Settings": ['learning_rate', 'lr', 'unet_lr', 'text_encoder_lr', 'max_train_epochs', 'max_train_steps', 'epochs', 'train_batch_size', 'batch_size', 'seed'],
                "Resolution": ['resolution', 'width', 'height'],
                "Optimizer & Scheduler": ['optimizer_type', 'optimizer', 'lr_scheduler', 'scheduler'],
                "Model": ['pretrained_model_name_or_path', 'model_path', 'base_model', 'output_dir', 'output_name'],
                "Dataset": ['train_data_dir', 'dataset_config', 'caption_extension'],
                "Other": ['mixed_precision', 'gradient_checkpointing', 'save_every_n_epochs', 'save_model_as'],
            }
            
            for category, keys in categories.items():
                found_keys = [(k, training_info[k]) for k in keys if k in training_info]
                if found_keys:
                    f.write(f"[{category}]\n")
                    for key, value in found_keys:
                        f.write(f"  {key} = {value}\n")
                    f.write("\n")
            
            # Source files
            if 'source_files' in training_info:
                f.write(f"[Source]\n")
                f.write(f"  Parsed from: {', '.join(training_info['source_files'])}\n")
                f.write(f"  Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
        return True
    except Exception:
        return False


# UI output helpers with emoji
def say(msg): 
    print(f"🟦 {msg}")
def ok(msg): 
    print(f"✅ {msg}")
def warn(msg): 
    print(f"⚠️  {msg}")
def err(msg): 
    print(f"❌ {msg}")

# Localization dictionary
TEXT = {
    "EN": {
        # Wizard banners
        "banner_title": "🧙 HuggingFace LoRA Wizard by NiHao OFM (EN)",
        "banner_subtitle": "   Upload/Download mode + repo selection + epochs",
        # Prompts and messages
        "choose_lang": "Choose language / Выберите язык:",
        "mode_question": "What do you want to do?",
        "mode_upload": "Upload",
        "mode_download": "Download",
        "invalid_choice": "Invalid choice.",
        "enter_choice": "👉 [1-2] (Enter=1): ",
        "enter_choice_alt": "👉 Select [1-2] (Enter=1): ",  # RU has "Выбор", EN often just the arrow
        "step_auth": "Step {current}/{total}: Checking HuggingFace authorization (token)...",
        "token_not_found": "Token not found. Please enter your HuggingFace access token:",
        "enter_token": "👉 Token: ",
        "token_empty": "Token is empty.",
        "token_save_fail": "Failed to save token",
        "token_saved": "Token saved.",
        "token_available": "Token already available.",
        "err_user_name": "Failed to get HF user name.",
        "user_ok": "HF user: {user}",
        "step_repo": "Step {current}/{total}: Repository",
        "repo_create_new": "Create new",
        "repo_use_existing": "Use existing",
        "enter_repo_choice": "👉 [1-2] (Enter=1): ",
        "enter_repo_name": "📦 Name of new repo (e.g., MyLoRA_v1): ",
        "name_empty": "Name is empty.",
        "repo_confirm": "Repo: {repo_id}",
        "repo_private_q": "🔒 Private? [Y/n] (Enter=Y): ",
        "repo_private": "Private.",
        "repo_public": "Public.",
        "creating_repo": "Creating repo (will continue if it exists)...",
        "enter_repo_id": "📦 Repo ID (user/name) or just name: ",
        "input_empty": "Empty input.",
        "your_repos": "Your repositories:",
        "no_repos_found": "No repositories found for user {user}.",
        "select_repo_or_manual": "👉 Select [1-{total}] or [M] to enter manually (Enter=1): ",
        "manual_entry": "Enter repo name manually:",
        "fetching_repos": "Fetching your repositories...",
        "step_local": "Step {current}/{total}: Local repository folder",
        "err_not_git": "Folder '{folder}' exists but is not a git repository.",
        "warn_local_exists": "Local repo already exists: {folder}",
        "local_use": "  [1] Use it (git pull)",
        "local_reclone": "  [2] Delete and re-clone",
        "enter_local_choice": "👉 [1-2] (Enter=1): ",
        "deleted_cloning": "Deleted. Cloning...",
        "using_local": "Using local repo.",
        "cloning_repo": "Cloning: https://huggingface.co/{repo_id}",
        "step_lfs": "Step {current}/{total}: Git LFS",
        "step_find_run": "Step {current}/{total}: Auto-searching run (epochXX/*.safetensors)",
        "searching_roots": "Searching in roots:",
        "no_run_found": "Autosearch did not find any run folder.",
        "enter_run_dir": "📁 Enter RUN_DIR (directory with epochXX): ",
        "not_found": "Not found: {path}",
        "found_runs": "Found run folders:",
        "epochs_label": "epochs",
        "modified_label": "modified",
        "select_run": "👉 Run number [1-{total}] (Enter=1): ",
        "repo_run_confirm": "Run: {path}",
        "step_epoch": "Step {current}/{total}: Select epochs to upload",
        "epochs_available": "Epochs available: {min} .. {max}",
        "epoch_from": "🔢 Epoch FROM (blank = auto): ",
        "epoch_to": "🔢 Epoch TO   (blank = auto): ",
        "must_be_number": "{field} must be a number",
        "from_gt_to": "FROM > TO — swapping.",
        "range_confirm": "Range: {start}..{end}",
        "file_inside_epoch": "📌 ABOUT FILE INSIDE epoch\nUsually 'adapter_model.safetensors'. Press Enter to accept the found name.\n",
        "enter_epoch_file": "📝 File name inside epoch folders (Enter to accept '{default}'): ",
        "no_epoch_files": "No .safetensors files found in the repository.",
        "adding_queue": "Queuing files for download...",
        "epoch_added": "epoch{num} added",
        "file_not_found": "File not found: {filename}",
        "no_files_range": "No files to download in the specified range.",
        "select_file_mode": "Step {current}/{total}: Choose files to download",
        "single_file": "Single file",
        "range_of_files": "Range of epoch files",
        "filename_filter": "🔎 Filename filter (press Enter for all): ",
        "no_match_filter": "No files matched filter. Showing all.",
        "select_file": "👉 Select file [1-{total}] (Enter=1): ",
        "file_label": "File: {file}",
        "step_download": "Step {current}/{total}: Download summary",
        "download_summary": "Downloaded {success} file(s) to {path}",
        "download_failures": "{fail} files failed to download.",
        "target_dir_multi": "Multiple 'loras' directories found. Please choose:",
        "select_directory": "👉 Select directory [1-{total}] (Enter=1): ",
        "using_dir": "Using directory: {dir}",
        "created_dir": "Created {dir}",
        "using_local_loras": "Using local './loras' directory.",
        "cannot_create_dir": "Cannot create directory {dir}",
        "download_failed": "Download failed.",
        "upload_summary": "Uploaded {count} files to repository {repo}.",
        "upload_skipped": "Some files were not found and were skipped.",
        "view_repo": "View your repository at https://huggingface.co/{repo}"
    },
    "RU": {
        # Wizard banners
        "banner_title": "🧙 HuggingFace LoRA Wizard by NiHao OFM (RU)",
        "banner_subtitle": "   Режим Upload/Download + выбор репо + эпохи",
        # Prompts and messages
        "choose_lang": "Choose language / Выберите язык:",
        "mode_question": "Что сделать?",
        "mode_upload": "Upload",      # Оставлено на английском для соответствия оригиналу
        "mode_download": "Download",
        "invalid_choice": "Неверный выбор.",
        "enter_choice": "👉 Выбор [1-2] (Enter=1): ",
        "enter_choice_alt": "👉 Выберите [1-2] (Enter=1): ",
        "step_auth": "Шаг {current}/{total}: Проверяю авторизацию HuggingFace (по токену)...",
        "token_not_found": "Токен не найден. Введите токен HuggingFace (с правами записи):",
        "enter_token": "👉 Токен: ",
        "token_empty": "Токен пустой.",
        "token_save_fail": "Не удалось сохранить токен",
        "token_saved": "Токен сохранён.",
        "token_available": "Токен уже доступен.",
        "err_user_name": "Не удалось получить имя пользователя HF.",
        "user_ok": "HF пользователь: {user}",
        "step_repo": "Шаг {current}/{total}: Репозиторий",
        "repo_create_new": "Создать новый",
        "repo_use_existing": "Использовать существующий",
        "enter_repo_choice": "👉 Выбор [1-2] (Enter=1): ",
        "enter_repo_name": "📦 Имя нового репозитория (пример: MyLoRA_v1): ",
        "name_empty": "Имя пустое.",
        "repo_confirm": "Repo: {repo_id}",
        "repo_private_q": "🔒 Приватный? [Y/n] (Enter=Y): ",
        "repo_private": "Приватный.",
        "repo_public": "Публичный.",
        "creating_repo": "Создаю репозиторий (если уже есть — продолжу)...",
        "enter_repo_id": "📦 Repo ID (owner/name) или просто name: ",
        "input_empty": "Пусто.",
        "your_repos": "Ваши репозитории:",
        "no_repos_found": "У пользователя {user} нет репозиториев.",
        "select_repo_or_manual": "👉 Выбор [1-{total}] или [M] ввести вручную (Enter=1): ",
        "manual_entry": "Введите имя репозитория вручную:",
        "fetching_repos": "Получаю список ваших репозиториев...",
        "step_local": "Шаг {current}/{total}: Локальная папка репозитория",
        "err_not_git": "Папка '{folder}' существует, но это не git-репозиторий.",
        "warn_local_exists": "Локальный репозиторий уже существует: {folder}",
        "local_use": "  [1] Использовать (git pull)",
        "local_reclone": "  [2] Удалить и клонировать заново",
        "enter_local_choice": "👉 Выбор [1-2] (Enter=1): ",
        "deleted_cloning": "Удалил. Клонирую...",
        "using_local": "Использую локальный репозиторий.",
        "cloning_repo": "Клонирую: https://huggingface.co/{repo_id}",
        "step_lfs": "Шаг {current}/{total}: Git LFS",
        "step_find_run": "Шаг {current}/{total}: Автопоиск run (epochXX/*.safetensors)",
        "searching_roots": "Ищу в корнях:",
        "no_run_found": "Автопоиск не нашёл run-папки.",
        "enter_run_dir": "📁 Введите RUN_DIR (где лежат папки epochXX): ",
        "not_found": "Не найдено: {path}",
        "found_runs": "Найдены run-папки:",
        "epochs_label": "эпох",
        "modified_label": "изменено",
        "select_run": "👉 Номер run [1-{total}] (Enter=1): ",
        "repo_run_confirm": "Run: {path}",
        "step_epoch": "Шаг {current}/{total}: Выбор эпох для загрузки",
        "epochs_available": "Доступные эпохи: {min} .. {max}",
        "epoch_from": "🔢 Эпоха ОТ (пусто = авто): ",
        "epoch_to": "🔢 Эпоха ДО (пусто = авто): ",
        "must_be_number": "{field} должен быть числом",
        "from_gt_to": "FROM > TO — меняю местами.",
        "range_confirm": "Диапазон: {start}..{end}",
        "file_inside_epoch": "📌 ПРО ФАЙЛ ВНУТРИ epoch\nОбычно 'adapter_model.safetensors'. Enter = принять найденный.\n",
        "enter_epoch_file": "📝 Имя файла в папках epoch (Enter для '{default}'): ",
        "no_epoch_files": "В репозитории не найдено файлов epoch*.safetensors.",
        "adding_queue": "Добавляю файлы в очередь на скачивание...",
        "epoch_added": "epoch{num} добавлен",
        "file_not_found": "Файл не найден: {filename}",
        "no_files_range": "В указанном диапазоне файлов нет.",
        "select_file_mode": "Шаг {current}/{total}: Выбор файлов для скачивания",
        "single_file": "Один файл",
        "range_of_files": "Диапазон epoch-файлов",
        "filename_filter": "🔎 Фильтр по имени файла (Enter для всех): ",
        "no_match_filter": "Файлы не найдены по фильтру. Показываю все.",
        "select_file": "👉 Выберите файл [1-{total}] (Enter=1): ",
        "file_label": "Файл: {file}",
        "step_download": "Шаг {current}/{total}: Итоги скачивания",
        "download_summary": "Скачано файлов: {success}. Путь: {path}",
        "download_failures": "Не скачано файлов: {fail}.",
        "target_dir_multi": "Найдено несколько папок 'loras'. Выберите нужную:",
        "select_directory": "👉 Выберите папку [1-{total}] (Enter=1): ",
        "using_dir": "Использую папку: {dir}",
        "created_dir": "Создано {dir}",
        "using_local_loras": "Использую локальную папку './loras'.",
        "cannot_create_dir": "Не удалось создать папку {dir}",
        "download_failed": "Ошибка при скачивании файла.",
        "upload_summary": "Загружено файлов: {count} (в репозиторий {repo}).",
        "upload_skipped": "Некоторые файлы не найдены и пропущены.",
        "view_repo": "Смотри репозиторий по адресу https://huggingface.co/{repo}"
    }
}

# Helper for localization
UI_LANG = "EN"  # will be set after language selection
def t(key, **kwargs):
    """Return translated text for current UI_LANG."""
    text = TEXT[UI_LANG].get(key, "")
    return text.format(**kwargs) if kwargs else text

if __name__ == "__main__":
    # --- Quiet boot setup ---
    quiet = False
    # Determine quiet mode from env or args (default QUIET_BOOT=1 if not specified)
    quiet_env = os.getenv("QUIET_BOOT", "1")
    if quiet_env == "1":
        quiet = True
    if quiet_env == "0":
        quiet = False
    if "--quiet" in sys.argv:
        quiet = True
        # Remove the flag to avoid confusion if any argument parsing later
        sys.argv.remove("--quiet")

    # Setup quiet logging if enabled
    if quiet:
        log_dir = "./nihao_wizard_logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        log_path = os.path.join(log_dir, f"{timestamp}.log")
        try:
            # Redirect stdout/stderr to log file
            log_file = open(log_path, "w", buffering=1)
            orig_stdout, orig_stderr = sys.stdout, sys.stderr
            sys.stdout = log_file
            sys.stderr = log_file
            # Log basic info
            print(f"[INFO] Python version: {sys.version.split()[0]}")
            print(f"[INFO] Platform: {sys.platform}")
            print(f"[INFO] Current directory: {os.getcwd()}")
            # Dependency checks (safe mode handling)
            # Check required commands and libraries
            if shutil.which("git") is None:
                err(f"Not found: git")
                raise RuntimeError("dep_error")
            if shutil.which("git-lfs") is None:
                err(f"Not found: git-lfs")
                raise RuntimeError("dep_error")
            # huggingface_hub library & CLI
            try:
                import huggingface_hub
            except ImportError:
                err(f"Not found: huggingface_hub (hf)")
                print("To install: pip3 install -U huggingface_hub")
                raise RuntimeError("dep_error")
            if shutil.which("hf") is None:
                err(f"Not found: hf (Hugging Face CLI missing)")
                print("To install: pip3 install -U huggingface_hub")
                raise RuntimeError("dep_error")
        except Exception as e:
            # If any initialization error occurs, restore output and alert user
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout, sys.stderr = orig_stdout, orig_stderr
            # If UI_LANG not set yet (before language selection), default to RU for error (as original script)
            lang_for_error = "RU"
            msg = "Startup error. See log:" if lang_for_error == "EN" else "Ошибка на старте. Лог:"
            err(f"{msg} {log_path}")
            sys.exit(1)
        finally:
            # Restore normal stdout/stderr before interactive prompts
            if 'orig_stdout' in locals():
                sys.stdout.flush()
                sys.stderr.flush()
                sys.stdout, sys.stderr = orig_stdout, orig_stderr
                if 'log_file' in locals():
                    log_file.close()
    else:
        # Non-quiet mode: still check dependencies
        if shutil.which("git") is None:
            err("Not found: git")
            sys.exit(1)
        if shutil.which("git-lfs") is None:
            err("Not found: git-lfs")
            sys.exit(1)
        try:
            import huggingface_hub
        except ImportError:
            err("Not found: huggingface_hub")
            print("To install: pip3 install -U huggingface_hub")
            sys.exit(1)
        if shutil.which("hf") is None:
            err("Not found: hf CLI")
            print("To install: pip3 install -U huggingface_hub")
            sys.exit(1)
    # --- End quiet boot ---

    # --- Language Selection ---
    # Print language menu in bilingual format
    print(t("choose_lang"))  # intentionally prints both languages from dict (string contains both)
    print("  [1] Русский (default)")
    print("  [2] English\n")
    lang_choice = input("👉 [1-2] (Enter=1): ").strip() or "1"
    if lang_choice not in ("1", "2"):
        # If invalid, default to 1
        lang_choice = "1"
    UI_LANG = "EN" if lang_choice == "2" else "RU"
    print()  # blank line

    # --- Wizard Banner ---
    print()
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║   Designed and produced by NiHao OFM          ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()
    print("======================================")
    print(t("banner_title"))
    print(t("banner_subtitle"))
    print("======================================")
    print()

    # --- Dependency Handling Message (if any) ---
    # (In AUTO mode, dependencies were auto-installed in run.sh; in SAFE mode, we've already ensured presence above)
    # We inform the user about dependency status:
    # If all dependencies were present (or installed), mimic original messaging.
    say(TEXT[UI_LANG]["mode_question"])  # e.g. "Что сделать?" or "What do you want to do?"

    # --- Mode Selection (Upload/Download) ---
    print(f"  [1] {TEXT[UI_LANG]['mode_upload']}")
    print(f"  [2] {TEXT[UI_LANG]['mode_download']}\n")
    mode_input = input(t("enter_choice")).strip() or "1"
    if mode_input not in ("1", "2"):
        # treat invalid as default 1
        warn(t("invalid_choice"))
        mode_input = "1"
    mode_action = "download" if mode_input == "2" else "upload"
    # Set total steps depending on mode
    if mode_action == "download":
        tot_steps = 4
    else:
        tot_steps = 6
    print()

    # --- Step 1: Hugging Face authentication (token) ---
    say(t("step_auth", current=1, total=tot_steps))
    # Use huggingface_hub utilities for token check/login
    from huggingface_hub import HfApi, login
    
    # Try to get token from multiple sources
    token = None
    
    # 1. Check environment variables
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    
    # 2. Try to get from HF cache
    if not token:
        try:
            # New way (huggingface_hub >= 0.14)
            from huggingface_hub.utils import get_token
            token = get_token()
        except (ImportError, Exception):
            # Old way - read from file
            token_path = os.path.expanduser("~/.huggingface/token")
            if os.path.exists(token_path):
                try:
                    with open(token_path) as f:
                        token = f.read().strip()
                except Exception:
                    pass
    
    # 3. Verify token works
    if token:
        try:
            api = HfApi()
            api.whoami(token=token)
            ok(t("token_available"))
        except Exception:
            warn("Cached token is invalid")
            token = None
    
    # 4. If no valid token, prompt user
    if not token:
        warn(t("token_not_found"))
        try:
            import getpass
            token_input = getpass.getpass(t("enter_token")) or ""
        except ImportError:
            token_input = input(t("enter_token")) or ""
        
        print()
        if token_input.strip() == "":
            err(t("token_empty"))
            sys.exit(1)
        
        token = token_input.strip()
        
        # Try to save token
        try:
            login(token=token, add_to_git_credential=False)
            ok(t("token_saved"))
        except Exception as e:
            warn(f"Could not save token: {str(e)}")
            warn("Token will be used for this session only")
    
    # 5. Get username
    try:
        api = HfApi()
        user_info = api.whoami(token=token)
        HF_USER = user_info["name"]
        ok(t("user_ok", user=HF_USER))
    except Exception as e:
        err(t("err_user_name"))
        err(f"Error: {str(e)}")
        sys.exit(1)

    # Setup Git credentials with HF token (to avoid interactive prompt)
    askpass_script = f"/tmp/hf_git_askpass_{os.getpid()}.sh"
    try:
        with open(askpass_script, "w") as f:
            f.write(f"#!/bin/sh\necho \"{token}\"\n")
        os.chmod(askpass_script, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception as e:
        # If we cannot create the askpass script, warn but continue (git might prompt)
        warn("Could not set up askpass script, you might be prompted for credentials.")
    else:
        os.environ["GIT_ASKPASS"] = askpass_script
        os.environ["GIT_TERMINAL_PROMPT"] = "0"
        # Ensure the askpass script is removed on exit
        import atexit
        atexit.register(lambda: os.path.isfile(askpass_script) and os.remove(askpass_script))

    # Proceed with mode-specific workflow
    if mode_action == "upload":
        # -------- Upload Mode Workflow --------
        # Step 2: Select or create repository
        say(t("step_repo", current=2, total=tot_steps))
        print(f"  [1] {t('repo_create_new')}")
        print(f"  [2] {t('repo_use_existing')}\n")
        repo_mode = input(t("enter_repo_choice")).strip() or "1"
        if repo_mode not in ("1", "2"):
            err(t("invalid_choice"))
            sys.exit(1)
        repo_id = ""
        repo_name = ""
        private_flag = False

        if repo_mode == "1":
            # Create new repository
            repo_name = input(t("enter_repo_name")).strip()
            repo_name = repo_name.replace(" ", "_")
            if repo_name == "":
                err(t("name_empty"))
                sys.exit(1)
            repo_id = f"{HF_USER}/{repo_name}"
            ok(t("repo_confirm", repo_id=repo_id))
            private_ans = input(t("repo_private_q")).strip() or "Y"
            if private_ans.lower().startswith("y"):
                private_flag = True
                ok(t("repo_private"))
            else:
                private_flag = False
                warn(t("repo_public"))
            say(t("creating_repo"))
            # Create repo via Hugging Face API (ignore if already exists)
            api = HfApi()
            try:
                api.create_repo(repo_id=repo_id, token=token, repo_type="model", private=private_flag, exist_ok=True)
                ok("✅ Repository created/verified" if UI_LANG == "EN" else "✅ Репозиторий создан/проверен")
            except Exception as e:
                err(f"Failed to create repository: {e}" if UI_LANG == "EN" else f"Не удалось создать репозиторий: {e}")
                sys.exit(1)
        else:
            # Use existing repository - show list of user's repos
            say(t("fetching_repos"))
            api = HfApi()
            repos = []
            try:
                model_list = api.list_models(author=HF_USER, token=token)
                for model in model_list:
                    repo_id_str = None
                    if hasattr(model, "modelId"):
                        repo_id_str = model.modelId
                    elif hasattr(model, "repo_id"):
                        repo_id_str = model.repo_id
                    elif hasattr(model, "id"):
                        repo_id_str = model.id
                    else:
                        repo_id_str = str(model)
                    if repo_id_str:
                        repos.append(repo_id_str)
            except Exception as e:
                warn(f"Could not fetch repos: {e}")
            
            if repos:
                # Show up to 10 repos
                display_repos = repos[:10]
                print()
                ok(t("your_repos"))
                for idx, rid in enumerate(display_repos, start=1):
                    print(f"  [{idx}] {rid}")
                if len(repos) > 10:
                    print(f"  ... (+{len(repos) - 10} more)")
                print(f"  [M] {t('manual_entry')}")
                print()
                
                repo_choice = input(t("select_repo_or_manual", total=len(display_repos))).strip() or "1"
                
                if repo_choice.lower() == "m":
                    # Manual entry
                    repo_id_input = input(t("enter_repo_id")).strip()
                    if repo_id_input == "":
                        err(t("input_empty"))
                        sys.exit(1)
                    if "/" not in repo_id_input:
                        repo_id = f"{HF_USER}/{repo_id_input}"
                    else:
                        repo_id = repo_id_input
                elif repo_choice.isdigit():
                    choice_num = int(repo_choice)
                    if choice_num < 1 or choice_num > len(display_repos):
                        err(t("invalid_choice"))
                        sys.exit(1)
                    repo_id = display_repos[choice_num - 1]
                else:
                    err(t("invalid_choice"))
                    sys.exit(1)
            else:
                # No repos found, ask for manual input
                warn(t("no_repos_found", user=HF_USER))
                repo_id_input = input(t("enter_repo_id")).strip()
                if repo_id_input == "":
                    err(t("input_empty"))
                    sys.exit(1)
                if "/" not in repo_id_input:
                    repo_id = f"{HF_USER}/{repo_id_input}"
                else:
                    repo_id = repo_id_input
            
            if not validate_repo_id(repo_id):
                sys.exit(1)
            ok(t("repo_confirm", repo_id=repo_id))
            repo_name = repo_id.split("/")[-1]
        print()

        # Step 3: Clone or update local repository folder
        say(t("step_local", current=3, total=tot_steps))
        repo_dir = repo_name
        # Validate existing folder
        if os.path.isdir(repo_dir) and not os.path.isdir(os.path.join(repo_dir, ".git")):
            err(t("err_not_git", folder=repo_dir))
            sys.exit(1)
        if os.path.isdir(os.path.join(repo_dir, ".git")):
            warn(t("warn_local_exists", folder=repo_dir))
            print(f"{t('local_use')}\n{t('local_reclone')}\n")
            local_mode = input(t("enter_local_choice")).strip() or "1"
            if local_mode not in ("1", "2"):
                local_mode = "1"
            if local_mode == "2":
                # Delete and re-clone
                try:
                    shutil.rmtree(repo_dir)
                except Exception:
                    pass
                ok(t("deleted_cloning"))
                CLEANUP_DIRS.append(repo_dir)
                if not git_clone_with_progress(repo_id, repo_dir, token):
                    sys.exit(1)
            else:
                ok(t("using_local"))
        else:
            ok(t("cloning_repo", repo_id=repo_id))
            CLEANUP_DIRS.append(repo_dir)
            if not git_clone_with_progress(repo_id, repo_dir, token):
                sys.exit(1)
        # Enter the repository directory
        try:
            os.chdir(repo_dir)
        except Exception as e:
            err(f"Cannot enter directory: {repo_dir}")
            sys.exit(1)
        # Pull latest changes (just in case, ignore errors)
        subprocess.run(["git", "pull"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Step 4: Git LFS setup
        say(t("step_lfs", current=4, total=tot_steps))
        # Configure git user if not set (use HF user and a default email)
        subprocess.run(["git", "config", "user.name", os.getenv("GIT_NAME", HF_USER)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", os.getenv("GIT_EMAIL", f"{HF_USER}@users.noreply.huggingface.co")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "lfs", "install"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "lfs", "track", "*.safetensors"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", ".gitattributes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Enable Git LFS"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Step 5: Auto-search for run directory containing epoch folders
        say(t("step_find_run", current=5, total=tot_steps))
        say(t("searching_roots"))
        # Initialize search roots
        search_roots = []
        if os.getenv("SEARCH_ROOTS"):
            # Split by spaces or newlines
            for r in re.split(r'[ \n]', os.getenv("SEARCH_ROOTS")):
                if r:
                    search_roots.append(r)
        else:
            search_roots = [
                "/workspace/output_folder",
                "/workspace/diffusion_pipe_working_folder/output_folder",
                "/workspace"
            ]
        for r in search_roots:
            if r:
                print(f"   - {r}")
        print()
        found_runs = []
        # Search up to depth 6 for any "epoch*/<file>.safetensors"
        def scan_for_runs(root, depth=0, max_depth=6):
            if depth > max_depth:
                return
            try:
                entries = os.listdir(root)
            except Exception:
                return
            for entry in entries:
                full_path = os.path.join(root, entry)
                if os.path.isdir(full_path):
                    # If this directory is an epoch folder with safetensors inside
                    if entry.startswith("epoch"):
                        # If any .safetensors file inside this epoch folder
                        try:
                            files_inside = os.listdir(full_path)
                        except Exception:
                            files_inside = []
                        for f in files_inside:
                            if f.endswith(".safetensors"):
                                run_dir_path = root  # parent of epoch folder
                                if run_dir_path not in found_runs:
                                    found_runs.append(run_dir_path)
                                break
                    # Recurse into subdirectories
                    scan_for_runs(full_path, depth+1, max_depth)
        for root in search_roots:
            if os.path.isdir(root):
                scan_for_runs(root, depth=0, max_depth=6)
        if not found_runs:
            warn(t("no_run_found"))
            run_dir = input(t("enter_run_dir")).strip()
            if run_dir == "" or not os.path.isdir(run_dir):
                err(t("not_found", path=run_dir or ""))
                sys.exit(1)
        else:
            ok(t("found_runs"))
            # Prepare labels for listing
            ep_label = t("epochs_label")
            mod_label = t("modified_label")
            # List found run directories with epoch count and last modified time
            for idx, path in enumerate(found_runs, start=1):
                # Count epoch subdirectories
                epoch_count = 0
                try:
                    subdirs = os.listdir(path)
                except Exception:
                    subdirs = []
                for d in subdirs:
                    if os.path.isdir(os.path.join(path, d)) and d.startswith("epoch"):
                        epoch_count += 1
                # Last modified time of the folder
                try:
                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    mod_time_str = "n/a"
                print(f"  [{idx}] {path}   ({ep_label}: {epoch_count})   ({mod_label}: {mod_time_str})")
            print()
            choice = input(t("select_run", total=len(found_runs))).strip() or "1"
            if not choice.isdigit():
                err(t("invalid_choice"))
                sys.exit(1)
            choice_num = int(choice)
            if choice_num < 1 or choice_num > len(found_runs):
                err(t("invalid_choice"))
                sys.exit(1)
            run_dir = found_runs[choice_num - 1]
            ok(t("repo_run_confirm", path=run_dir))
            print()

        # Step 6: Select epoch range and upload files
        # Determine LoRA file name inside epoch folders
        epoch_folders = [d for d in os.listdir(run_dir) if os.path.isdir(os.path.join(run_dir, d)) and d.startswith("epoch")]
        if not epoch_folders:
            err("No epoch folders found in run directory.")
            sys.exit(1)
        # Sort epoch folders by numeric order (extract number after 'epoch')
        epoch_folders.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else float('inf'))
        # Use the first epoch folder to find a .safetensors file name
        first_epoch_path = os.path.join(run_dir, epoch_folders[0])
        try:
            files_in_epoch = [f for f in os.listdir(first_epoch_path) if f.endswith(".safetensors")]
        except Exception:
            files_in_epoch = []
        if not files_in_epoch:
            err("No .safetensors file found in first epoch folder.")
            sys.exit(1)
        default_epoch_file = files_in_epoch[0]
        # If multiple files found, prefer one named 'adapter_model.safetensors' if present
        for f in files_in_epoch:
            if f.lower() == "adapter_model.safetensors":
                default_epoch_file = f
                break
        # Ask user if they want to use a different file name
        print(t("file_inside_epoch"), end="")  # Show info about file name
        custom_name = input(t("enter_epoch_file", default=default_epoch_file)).strip()
        epoch_file_name = custom_name if custom_name else default_epoch_file

        # Gather all epoch numbers available
        epoch_numbers = []
        for folder in epoch_folders:
            match = re.match(r'epoch(\d+)', folder)
            if match:
                epoch_numbers.append(int(match.group(1)))
        if not epoch_numbers:
            err("No epoch files found.")
            sys.exit(1)
        min_epoch = min(epoch_numbers)
        max_epoch = max(epoch_numbers)
        ok(t("epochs_available", min=min_epoch, max=max_epoch))
        # Prompt for range
        from_input = input(t("epoch_from")).strip()
        to_input = input(t("epoch_to")).strip()
        if from_input == "" and to_input == "":
            # Default range logic
            if max_epoch < 10:
                epoch_from = min_epoch
                epoch_to = max_epoch
            else:
                epoch_from = 10 if min_epoch < 10 else min_epoch
                epoch_to = 200 if max_epoch > 200 else max_epoch
        else:
            if from_input == "" or not from_input.isdigit():
                err(t("must_be_number", field="FROM"))
                sys.exit(1)
            if to_input == "" or not to_input.isdigit():
                err(t("must_be_number", field="TO"))
                sys.exit(1)
            epoch_from = int(from_input)
            epoch_to = int(to_input)
            if epoch_from > epoch_to:
                warn(t("from_gt_to"))
                epoch_from, epoch_to = epoch_to, epoch_from
        ok(t("range_confirm", start=epoch_from, end=epoch_to))
        # Copy selected epoch files into repo directory
        success_count = 0
        fail_count = 0
        for num in range(epoch_from, epoch_to + 1):
            src_file = os.path.join(run_dir, f"epoch{num}", epoch_file_name)
            dest_file = f"epoch{num}.safetensors"
            if os.path.isfile(src_file):
                try:
                    shutil.copy2(src_file, dest_file)
                except Exception as e:
                    fail_count += 1
                    warn(t("file_not_found", filename=os.path.basename(dest_file)))
                    continue
                success_count += 1
                ok(t("epoch_added", num=num))
            else:
                fail_count += 1
                warn(t("file_not_found", filename=os.path.basename(dest_file)))
        # Also include final model file if exists
        final_src = os.path.join(run_dir, "final.safetensors")
        if os.path.isfile(final_src):
            try:
                shutil.copy2(final_src, "final.safetensors")
            except Exception as e:
                warn(t("file_not_found", filename="final.safetensors"))
            else:
                success_count += 1
                ok("✅ final.safetensors added" if UI_LANG == "EN" else "✅ final.safetensors добавлен")
        if success_count == 0:
            err(t("no_files_range"))
            sys.exit(1)
        
        # Collect and save training info from .toml files
        say("Collecting training info from .toml files..." if UI_LANG == "EN" else "Собираю данные о тренировке из .toml файлов...")
        training_info = collect_training_info(run_dir)
        if training_info:
            if save_training_info(training_info, "training_info.txt"):
                ok("training_info.txt created" if UI_LANG == "EN" else "training_info.txt создан")
                success_count += 1
            else:
                warn("Could not save training_info.txt" if UI_LANG == "EN" else "Не удалось сохранить training_info.txt")
        else:
            warn("No .toml config files found" if UI_LANG == "EN" else "Файлы конфигурации .toml не найдены")
        
        # Commit and push to repository
        subprocess.run(["git", "add", "."], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Add LoRA files"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = subprocess.run(["git", "push"])
        if result.returncode != 0:
            err("Push failed.")
            sys.exit(1)
        
        # Remove from cleanup list after successful upload
        if repo_dir in CLEANUP_DIRS:
            CLEANUP_DIRS.remove(repo_dir)
        
        # Upload summary
        say(t("upload_summary", count=success_count, repo=repo_id))
        if fail_count > 0:
            warn(t("upload_skipped"))
        # Provide repository link
        ok(t("view_repo", repo=repo_id))
        
        # Thanks message
        print()
        print("  ╔═══════════════════════════════════════════════╗")
        print("  ║   Thanks for using NiHao OFM LoRA Wizard!     ║")
        print("  ║   Telegram: https://t.me/NiHaoOFM             ║")
        print("  ╚═══════════════════════════════════════════════╝")
        print()
    else:
        # -------- Download Mode Workflow --------
        # Step 2: List user repositories and select one to download from
        say(t("step_repo", current=2, total=tot_steps))
        api = HfApi()
        try:
            model_list = api.list_models(author=HF_USER)
        except Exception:
            err("Не удалось получить список репозиториев." if UI_LANG == "RU" else "Failed to retrieve repository list.")
            sys.exit(1)
        repos = []
        for model in model_list:
            # Each model might have .modelId or .repo_id attribute depending on huggingface_hub version
            repo_id_str = None
            if hasattr(model, "modelId"):
                repo_id_str = model.modelId
            elif hasattr(model, "repo_id"):
                repo_id_str = model.repo_id
            else:
                repo_id_str = str(model)
            if repo_id_str:
                repos.append(repo_id_str)
        if not repos:
            err(f"У пользователя {HF_USER} нет репозиториев." if UI_LANG == "RU" else f"No repositories found for user {HF_USER}.")
            sys.exit(1)
        for idx, rid in enumerate(repos, start=1):
            print(f"  [{idx}] {rid}")
        print()
        repo_choice = input(t("select_directory", total=len(repos))).strip() or "1"
        if not repo_choice.isdigit():
            err(t("invalid_choice"))
            sys.exit(1)
        repo_index = int(repo_choice)
        if repo_index < 1 or repo_index > len(repos):
            err(t("invalid_choice"))
            sys.exit(1)
        selected_repo = repos[repo_index - 1]
        ok(t("repo_confirm", repo_id=selected_repo))
        print()

        # Step 3: List files in selected repo and choose file(s) to download
        say(t("select_file_mode", current=3, total=tot_steps))
        print(f"  [1] {t('single_file')}")
        print(f"  [2] {t('range_of_files')}\n")
        file_mode = input(t("enter_choice")).strip() or "1"
        if file_mode not in ("1", "2"):
            err(t("invalid_choice"))
            sys.exit(1)
        # Retrieve list of .safetensors files in the repository
        try:
            files_list = api.list_repo_files(repo_id=selected_repo)
        except Exception:
            err("Не удалось получить список файлов репозитория." if UI_LANG == "RU" else "Failed to list files in repository.")
            sys.exit(1)
        files_list = [f for f in files_list if f.endswith(".safetensors")]
        if not files_list:
            err(t("no_epoch_files"))
            sys.exit(1)
        if file_mode == "1":
            # Single file download
            # Optional filename filter
            filt = input(t("filename_filter")).strip()
            filtered_files = files_list
            if filt:
                filtered_files = [f for f in files_list if filt.lower() in f.lower()]
                if not filtered_files:
                    warn(t("no_match_filter"))
                    filtered_files = files_list
            # Sort files (put final.safetensors first, then natural sort by number if present)
            if "final.safetensors" in filtered_files:
                # Place final.safetensors at top if exists
                filtered_files.remove("final.safetensors")
                filtered_files.sort(key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x)])
                choices = ["final.safetensors"] + filtered_files
            else:
                choices = sorted(filtered_files, key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x)])
            # Display choices
            for idx, fname in enumerate(choices, start=1):
                print(f"  [{idx}] {fname}")
            count = len(choices)
            print()
            file_choice = input(t("select_file", total=count)).strip() or "1"
            if not file_choice.isdigit():
                file_choice = "1"
            choice_num = int(file_choice)
            if choice_num < 1 or choice_num > count:
                err(t("invalid_choice"))
                sys.exit(1)
            selected_file = choices[choice_num - 1]
            ok(t("file_label", file=selected_file))
            # Determine local directory to save file (models/.../lora parser)
            target_dir, target_status = resolve_lora_target_dir(os.getcwd())
            if target_status == "error":
                err(t("cannot_create_dir", dir=target_dir))
                sys.exit(1)
            if target_status == "found_existing":
                ok(t("using_dir", dir=target_dir))
            else:
                ok(t("created_dir", dir=target_dir))
            # Download the selected file
            if not download_file_with_progress(selected_repo, selected_file, target_dir, token):
                sys.exit(1)
            downloaded_count = 1
            failed_count = 0
            # Step 4: Summary
            abs_path = os.path.abspath(target_dir)
            say(t("step_download", current=4, total=tot_steps))
            ok(t("download_summary", success=downloaded_count, path=abs_path))
            if failed_count > 0:
                warn(t("download_failures", fail=failed_count))
            
            # Thanks message
            print()
            print("  ╔═══════════════════════════════════════════════╗")
            print("  ║   Thanks for using NiHao OFM LoRA Wizard!     ║")
            print("  ║   Telegram: https://t.me/NiHaoOFM             ║")
            print("  ╚═══════════════════════════════════════════════╝")
            print()
        else:
            # Range of epoch files download
            # Filter epoch files from the list (those ending with 'epoch{num}.safetensors')
            epoch_files = [f for f in files_list if re.search(r'epoch\d+\.safetensors$', f)]
            if not epoch_files:
                err(t("no_epoch_files"))
                sys.exit(1)
            # Determine min and max epoch numbers
            epoch_nums = [int(re.search(r'epoch(\d+)\.safetensors$', f).group(1)) for f in epoch_files]
            min_epoch = min(epoch_nums)
            max_epoch = max(epoch_nums)
            ok(t("epochs_available", min=min_epoch, max=max_epoch))
            from_input = input(t("epoch_from")).strip()
            to_input = input(t("epoch_to")).strip()
            if from_input == "" and to_input == "":
                if max_epoch < 10:
                    epoch_from = min_epoch
                    epoch_to = max_epoch
                else:
                    epoch_from = 10 if min_epoch < 10 else min_epoch
                    epoch_to = 200 if max_epoch > 200 else max_epoch
            else:
                if from_input == "" or not from_input.isdigit():
                    err(t("must_be_number", field="FROM"))
                    sys.exit(1)
                if to_input == "" or not to_input.isdigit():
                    err(t("must_be_number", field="TO"))
                    sys.exit(1)
                epoch_from = int(from_input)
                epoch_to = int(to_input)
                if epoch_from > epoch_to:
                    warn(t("from_gt_to"))
                    epoch_from, epoch_to = epoch_to, epoch_from
            ok(t("range_confirm", start=epoch_from, end=epoch_to))
            # Determine file name prefix (prefix + num + .safetensors)
            epoch_files.sort(key=lambda x: int(re.search(r'epoch(\d+)', x).group(1)))
            if not epoch_files:
                err(t("no_epoch_files"))
                sys.exit(1)
            first_file = epoch_files[0]
            prefix = re.sub(r'[0-9]+\.safetensors$', '', first_file)
            # Queue files for download
            say(t("adding_queue"))
            files_to_download = []
            for num in range(epoch_from, epoch_to + 1):
                fname = f"{prefix}{num}.safetensors"
                if fname in epoch_files:
                    files_to_download.append(fname)
                    ok(t("epoch_added", num=num))
                else:
                    warn(t("file_not_found", filename=fname))
            if not files_to_download:
                err(t("no_files_range"))
                sys.exit(1)
            # Determine local directory to save files (models/.../lora parser)
            target_dir, target_status = resolve_lora_target_dir(os.getcwd())
            if target_status == "error":
                err(t("cannot_create_dir", dir=target_dir))
                sys.exit(1)
            if target_status == "found_existing":
                ok(t("using_dir", dir=target_dir))
            else:
                ok(t("created_dir", dir=target_dir))
            # Download files in the list
            from huggingface_hub import hf_hub_download
            success_count = 0
            fail_count = 0
            for fname in files_to_download:
                try:
                    hf_hub_download(repo_id=selected_repo, filename=fname, local_dir=target_dir)
                except Exception:
                    fail_count += 1
                    warn(t("download_failed") + f" ({fname})")
                else:
                    success_count += 1
            # Step 4: Summary of downloaded files
            abs_path = os.path.abspath(target_dir)
            say(t("step_download", current=4, total=tot_steps))
            if success_count > 0:
                ok(t("download_summary", success=success_count, path=abs_path))
            if fail_count > 0:
                warn(t("download_failures", fail=fail_count))
        
        # Thanks message
        print()
        print("  ╔═══════════════════════════════════════════════╗")
        print("  ║   Thanks for using NiHao OFM LoRA Wizard!     ║")
        print("  ║   Telegram: https://t.me/NiHaoOFM             ║")
        print("  ╚═══════════════════════════════════════════════╝")
        print()
