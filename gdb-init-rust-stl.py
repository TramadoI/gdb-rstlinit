import gdb, subprocess, re, os, argparse
from typing import Optional

class InitRustPrettyPrinter():
    """
    When compiled with -g, Rust produces binaries which contain a gdb_load_rust_pretty_printers.py in the .debug_gdb_scripts section.
    This makes gdb complain about missing scripts when run under plain gdb as opposed to the rust-gdb wrapper script.
    Distribution put this script into $INSTALL_ROOT/lib/rustlib/etc, which is someplace gdb would never look at by default.

    This class automatically adds the path to the gdb pretty printers to the gdb search path, so that gdb can find the pretty printers.
    Prerequisite for this to work however is that the PYTHONPATH environment variable is set to the $INSTALL_ROOT/lib/rustlib/etc directory.
    More information: https://github.com/rust-lang/rust/issues/33159
    """

    def __init__(self):
        rustc_sysroot = self.get_rustc_sysroot()

        if rustc_sysroot is not None:
            gdb_python_module_directory = os.path.join(rustc_sysroot, "lib", "rustlib", "etc")
            self.load_pretty_printers(gdb_python_module_directory)

    def get_rustc_sysroot(self) -> Optional[str]:
        try:
            result = subprocess.run(["rustc", "--print=sysroot"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Error: 'rustc --print=sysroot' failed with exit code {result.returncode}")

        except FileNotFoundError:
            print("Error: rustc command not found. Make sure Rust is installed and rustc is in your PATH")

        return None

    # This is useless if the PYTHONPATH variable is not set before gdb is run.
    def load_pretty_printers(self, gdb_python_module_directory: str) -> None:
        gdb.execute(f"add-auto-load-safe-path {gdb_python_module_directory}")
        gdb.execute(f"dir {gdb_python_module_directory}")

class InitRustStlCommand(gdb.Command):
    """
    A custom GDB command to automatically & correctly initialize the path of the Rust standard library for debugging, in order to be able to step into it with sources.
    Builds upon the solutions mentioned here: https://users.rust-lang.org/t/solved-how-to-step-into-std-source-code-when-debugging-in-vs-code/25319.
    Best used with a gdb.events.new_objfile.connect() event handler to automatically initialize the path when a new binary is loaded.

    For example in your .gdbinit:
    python
    gdb.execute('source /path/to/gdb-init-rust-stl.py')
    def on_new_objfile(event):
        gdb.execute('rinit -q') # -q to suppress the output

    gdb.events.new_objfile.connect(on_new_objfile)
    end

    This avoids manually typing 'rinit' every time you load a new binary.
    """

    QUIET = False
    FORCE = False

    def __init__(self):
        super(InitRustStlCommand, self).__init__("rinit", gdb.COMMAND_USER)

    def parse_args(self, arg: str) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--force", action="store_true", help="Force initialization even if not detected as a Rust binary")
        parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
        return parser.parse_known_args(gdb.string_to_argv(arg))

    def con_print(self, message: str) -> None:
        if not self.QUIET:
            print(message)

    def is_rust_binary(self, binary_path: str) -> bool:
        with open(binary_path, "rb") as file:
            file_data = file.read()

        rust_strings = [b"rust_begin_unwind", b"rust_eh_personality", b"/rustc/"]

        for rust_string in rust_strings:
            if re.search(rust_string, file_data):
                return True

        return False

    def get_rustup_home(self) -> Optional[str]:
        try:
            result = subprocess.run(["rustup", "show", "home"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.split()[0].strip()
            else:
                self.con_print(f"Error: 'rustup show home' failed with exit code {result.returncode}")

        except FileNotFoundError:
            self.con_print("Error: rustup command not found. Make sure Rust is installed and rustup is in your PATH")

        return None

    def get_active_rust_toolchain(self) -> Optional[str]:
        try:
            result = subprocess.run(["rustup", "show", "active-toolchain"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.split()[0].strip()
            else:
                self.con_print(f"Error: 'rustup show active-toolchain' failed with exit code {result.returncode}")

        except FileNotFoundError:
            self.con_print("Error: rustup command not found. Make sure Rust is installed and rustup is in your PATH")

        return None

    def get_rustlib_path(self, binary_path: str) -> Optional[str]:
        with open(binary_path, "rb") as file:
            data = file.read()

        rustlib_paths = re.findall(rb"/rustc/[^/]+/", data)

        if rustlib_paths:
            return rustlib_paths[0].decode("utf-8").strip()[:-1]

        return None

    def invoke(self, arg, from_tty):
        parsed_args, unknown_args = self.parse_args(arg)
        self.FORCE = parsed_args.force
        self.QUIET = parsed_args.quiet

        if unknown_args:
            self.con_write(f"Warning: Unknown arguments {unknown_args}")

        binary_path = gdb.current_progspace().filename
        if not self.FORCE and not self.is_rust_binary(binary_path):
            self.con_print("Error: Current binary was not detected to be a Rust binary. If thats a false positive rerun with the '-f' flag")
            return

        rustup_home = self.get_rustup_home()
        active_toolchain = self.get_active_rust_toolchain()

        if all(x is not None for x in [binary_path, rustup_home, active_toolchain]):

            toolchain_path = os.path.join(rustup_home, "toolchains", active_toolchain, "lib", "rustlib", "src", "rust")
            rustlib_path = self.get_rustlib_path(binary_path)

            if rustlib_path:
                gdb.execute(f"set substitute-path {rustlib_path} {toolchain_path}")
            else:
                self.con_print("Error: rustlib path not found in the binary")

InitRustStlCommand()
InitRustPrettyPrinter()
