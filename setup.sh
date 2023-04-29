#!/bin/bash
set -e

# Define the path to the gdb-init-rust-stl.py file
GDB_INIT_RUST_STL_PATH="$(pwd)/gdb-init-rust-stl.py"

# Check if the gdb-init-rust-stl.py file exists
if [ ! -f "$GDB_INIT_RUST_STL_PATH" ]; then
    echo "Error: gdb-init-rust-stl.py not found at the specified path!"
    exit 1
fi

# Backup existing gdbinit
if [ -f "${HOME}/.gdbinit" ]; then
    mv "${HOME}/.gdbinit" "${HOME}/.gdbinit.bk"
fi

# Source the gdb-init-rust-stl.py file in the .gdbinit file
echo "source $GDB_INIT_RUST_STL_PATH" >> ${HOME}/.gdbinit

# Add the hook that runs rinit on every new object file
cat << 'EOF' >> ${HOME}/.gdbinit
python
def on_new_objfile(event):
    gdb.execute('rinit -q')

gdb.events.new_objfile.connect(on_new_objfile)
end
EOF

echo "Setup complete. GDB will now automatically run rinit on every new object file."
