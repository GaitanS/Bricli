import gzip
import os
import shutil

from django.conf import settings
from django.contrib.staticfiles.management.commands.collectstatic import Command as CollectStaticCommand
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Collect static files with optimization (minification and compression)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minify",
            action="store_true",
            help="Minify CSS and JavaScript files",
        )
        parser.add_argument(
            "--gzip",
            action="store_true",
            help="Create gzipped versions of static files",
        )
        # Add all the standard collectstatic arguments
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--ignore",
            action="append",
            default=[],
            dest="ignore_patterns",
            metavar="PATTERN",
            help="Ignore files or directories matching this glob-style " "pattern. Use multiple times to ignore more.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do everything except modify the filesystem.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear the existing files using the storage " "before trying to copy or link the original file.",
        )
        parser.add_argument(
            "--link",
            action="store_true",
            help="Create a symbolic link to each file instead of copying.",
        )
        parser.add_argument(
            "--no-post-process",
            action="store_false",
            dest="post_process",
            help="Do NOT post process collected files.",
        )
        parser.add_argument(
            "--no-default-ignore",
            action="store_false",
            dest="use_default_ignore_patterns",
            help="Don't ignore the common private glob-style patterns (defaults to False).",
        )

    def handle(self, *args, **options):
        # First run the standard collectstatic command
        collect_command = CollectStaticCommand()
        collect_command.handle(*args, **options)

        # Then apply optimizations
        if options["minify"]:
            self.minify_files()

        if options["gzip"]:
            self.gzip_files()

    def minify_files(self):
        """Minify CSS and JavaScript files"""
        try:
            import cssmin
            import jsmin
        except ImportError:
            self.stdout.write(
                self.style.WARNING(
                    "cssmin and jsmin packages are required for minification. " "Install with: pip install cssmin jsmin"
                )
            )
            return

        static_root = settings.STATIC_ROOT
        if not static_root or not os.path.exists(static_root):
            self.stdout.write(self.style.ERROR("STATIC_ROOT not found. Run collectstatic first."))
            return

        # Minify CSS files
        for root, dirs, files in os.walk(static_root):
            for file in files:
                file_path = os.path.join(root, file)

                if file.endswith(".css") and not file.endswith(".min.css"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()

                        minified = cssmin.cssmin(content)

                        # Create minified version
                        min_file_path = file_path.replace(".css", ".min.css")
                        with open(min_file_path, "w", encoding="utf-8") as f:
                            f.write(minified)

                        self.stdout.write(f"Minified: {file}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed to minify {file}: {e}"))

                elif file.endswith(".js") and not file.endswith(".min.js"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()

                        minified = jsmin.jsmin(content)

                        # Create minified version
                        min_file_path = file_path.replace(".js", ".min.js")
                        with open(min_file_path, "w", encoding="utf-8") as f:
                            f.write(minified)

                        self.stdout.write(f"Minified: {file}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed to minify {file}: {e}"))

    def gzip_files(self):
        """Create gzipped versions of static files"""
        static_root = settings.STATIC_ROOT
        if not static_root or not os.path.exists(static_root):
            self.stdout.write(self.style.ERROR("STATIC_ROOT not found. Run collectstatic first."))
            return

        extensions_to_gzip = [".css", ".js", ".html", ".txt", ".xml", ".json"]

        for root, dirs, files in os.walk(static_root):
            for file in files:
                file_path = os.path.join(root, file)

                if any(file.endswith(ext) for ext in extensions_to_gzip):
                    try:
                        with open(file_path, "rb") as f_in:
                            with gzip.open(f"{file_path}.gz", "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        self.stdout.write(f"Gzipped: {file}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed to gzip {file}: {e}"))
