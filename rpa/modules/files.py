"""File processing module for RPA framework."""

import os
import re
import shutil
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..core.logger import LoggerMixin


class FileModule(LoggerMixin):
    """Handle file system operations."""

    def list_files(
        self,
        directory: str,
        pattern: str = "*",
        recursive: bool = False,
    ) -> List[Path]:
        """List files in a directory matching a pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern (default: all files)
            recursive: Search subdirectories

        Returns:
            List of matching file paths
        """
        path = Path(directory)
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        self.logger.info(f"Found {len(files)} files matching '{pattern}' in {directory}")
        return files

    def copy(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
    ) -> str:
        """Copy a file or directory.

        Args:
            source: Source path
            destination: Destination path
            overwrite: Whether to overwrite existing files

        Returns:
            Destination path
        """
        src = Path(source)
        dst = Path(destination)

        if dst.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {destination}")

        if src.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=overwrite)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        self.logger.info(f"Copied {source} to {destination}")
        return str(dst)

    def move(self, source: str, destination: str) -> str:
        """Move a file or directory.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            New path
        """
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
        self.logger.info(f"Moved {source} to {destination}")
        return destination

    def delete(self, path: str, force: bool = False) -> bool:
        """Delete a file or directory.

        Args:
            path: Path to delete
            force: Delete non-empty directories

        Returns:
            True if successful
        """
        p = Path(path)
        if p.is_dir():
            if force:
                shutil.rmtree(path)
            else:
                p.rmdir()
        else:
            p.unlink()

        self.logger.info(f"Deleted {path}")
        return True

    def rename(self, path: str, new_name: str) -> str:
        """Rename a file or directory.

        Args:
            path: Current path
            new_name: New name (not full path)

        Returns:
            New path
        """
        p = Path(path)
        new_path = p.parent / new_name
        p.rename(new_path)
        self.logger.info(f"Renamed {path} to {new_path}")
        return str(new_path)

    def batch_rename(
        self,
        directory: str,
        pattern: str,
        replacement: str,
        regex: bool = False,
        dry_run: bool = False,
    ) -> List[tuple]:
        """Batch rename files in a directory.

        Args:
            directory: Directory containing files
            pattern: Pattern to match in filenames
            replacement: Replacement string
            regex: Use regex matching
            dry_run: Preview changes without renaming

        Returns:
            List of (old_name, new_name) tuples
        """
        changes = []
        path = Path(directory)

        for file in path.iterdir():
            if file.is_file():
                old_name = file.name
                if regex:
                    new_name = re.sub(pattern, replacement, old_name)
                else:
                    new_name = old_name.replace(pattern, replacement)

                if old_name != new_name:
                    changes.append((old_name, new_name))
                    if not dry_run:
                        file.rename(path / new_name)

        action = "Would rename" if dry_run else "Renamed"
        self.logger.info(f"{action} {len(changes)} files")
        return changes

    def organize_by_extension(
        self,
        source_dir: str,
        target_dir: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Organize files into folders by extension.

        Args:
            source_dir: Directory to organize
            target_dir: Target directory (default: same as source)

        Returns:
            Dict mapping extensions to list of moved files
        """
        source = Path(source_dir)
        target = Path(target_dir) if target_dir else source
        organized = {}

        for file in source.iterdir():
            if file.is_file():
                ext = file.suffix.lower().lstrip(".") or "no_extension"
                ext_dir = target / ext
                ext_dir.mkdir(exist_ok=True)

                new_path = ext_dir / file.name
                shutil.move(str(file), str(new_path))

                if ext not in organized:
                    organized[ext] = []
                organized[ext].append(file.name)

        self.logger.info(f"Organized files into {len(organized)} categories")
        return organized

    def organize_by_date(
        self,
        source_dir: str,
        target_dir: Optional[str] = None,
        date_format: str = "%Y/%m",
    ) -> Dict[str, List[str]]:
        """Organize files into folders by modification date.

        Args:
            source_dir: Directory to organize
            target_dir: Target directory (default: same as source)
            date_format: Folder structure format

        Returns:
            Dict mapping date folders to list of moved files
        """
        source = Path(source_dir)
        target = Path(target_dir) if target_dir else source
        organized = {}

        for file in source.iterdir():
            if file.is_file():
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                date_folder = mtime.strftime(date_format)
                date_dir = target / date_folder
                date_dir.mkdir(parents=True, exist_ok=True)

                new_path = date_dir / file.name
                shutil.move(str(file), str(new_path))

                if date_folder not in organized:
                    organized[date_folder] = []
                organized[date_folder].append(file.name)

        self.logger.info(f"Organized files into {len(organized)} date folders")
        return organized

    def get_info(self, path: str) -> dict:
        """Get file/directory information.

        Args:
            path: Path to examine

        Returns:
            Dict with file information
        """
        p = Path(path)
        stat = p.stat()

        return {
            "name": p.name,
            "path": str(p.absolute()),
            "size": stat.st_size,
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "extension": p.suffix,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "accessed": datetime.fromtimestamp(stat.st_atime),
        }

    def watch(
        self,
        directory: str,
        callback: Callable[[FileSystemEvent], None],
        patterns: Optional[List[str]] = None,
        recursive: bool = False,
    ) -> Observer:
        """Watch a directory for changes.

        Args:
            directory: Directory to watch
            callback: Function to call on file events
            patterns: File patterns to watch (e.g., ['*.txt', '*.csv'])
            recursive: Watch subdirectories

        Returns:
            Observer instance (call .stop() to stop watching)
        """
        class Handler(FileSystemEventHandler):
            def __init__(self, cb, patterns):
                self.callback = cb
                self.patterns = patterns

            def on_any_event(self, event):
                if self.patterns:
                    path = Path(event.src_path)
                    if not any(path.match(p) for p in self.patterns):
                        return
                self.callback(event)

        handler = Handler(callback, patterns)
        observer = Observer()
        observer.schedule(handler, directory, recursive=recursive)
        observer.start()

        self.logger.info(f"Started watching {directory}")
        return observer

    def create_directory(self, path: str, parents: bool = True) -> str:
        """Create a directory.

        Args:
            path: Directory path
            parents: Create parent directories

        Returns:
            Created directory path
        """
        Path(path).mkdir(parents=parents, exist_ok=True)
        self.logger.info(f"Created directory: {path}")
        return path

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        return Path(path).read_text(encoding=encoding)

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> str:
        """Write text content to a file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding=encoding)
        self.logger.info(f"Wrote {len(content)} characters to {path}")
        return path
