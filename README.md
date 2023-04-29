`gdb-rstlinit` is a small `gdb` utility, that automatically points GDB to the correct Rust STL sources of your active toolchain via the `rinit` command.
It also correctly sets up the path to the `gdb_load_rust_pretty_printers.py` (in the `.debug_gdb_scripts` section when compiled with debug symbols).
More information [about this](https://github.com/rust-lang/rust/issues/33159).

## Setup ##

Be sure to have the `rust-src` component of your respective toolchain installed.

```bash
rustup component add rust-src
```

Clone this repository and run the setup.
```bash
git clone git@github.com:TramadoI/gdb-rstlinit.git
cd gdb-rstlinit && chmod +x setup.sh
./setup.sh
```

This will source the Python script and set up a hook to run this utility everytime an object file is loaded, so you dont have to type `rinit` everytime you start debugging.
For the pretty printing to work correctly, the `PYTHONPATH` variable NEEDS to be set to `$RUSTUP_HOME/toolchains/<your toolchain>/lib/rustlib/etc`.

## Why? ##

Currently, `gdb` is not able to detect the correct path to the Rust STL source, when stepping into a library function.
You'll encounter something akin to this when stepping into `Vec::new()` for example:
```
; id = {0x00000180}, range = [0x0000000100002760-0x00000001000027b0), name="_$LT$alloc..vec..Vec$LT$T$GT$$GT$::new::h50925563cb2ee1ff", mangled="_ZN33_$LT$alloc..vec..Vec$LT$T$GT$$GT$3new17h50925563cb2ee1ffE"
; Source location: /rustc/9fda7c2237db910e41d6a712e9a2139b352e558b/src/liballoc/vec.rs:329
100002760: 55                         pushq  %rbp
100002761: 48 89 E5                   movq   %rsp, %rbp
100002764: 48 83 EC 20                subq   $0x20, %rsp
```
To be able to see the sources, you need to substitute the `rustc/<hash>/` with the actual path to your sources, which are in `$RUSTUP_HOME/toolchains/<your toolchain>/lib/rustlib/src/rust`.

Substituing this path manually in `gdb` or in your `.gdbinit` via `set substitute-path <from> <to>` ([specifying gdb source directories](https://sourceware.org/gdb/onlinedocs/gdb/Source-Path.html#set-substitute_002dpath)) works but is tedious, because the hash will change everytime you update your toolchain. This is especially annoying, when working with the nightly build (as I do).

For more information see [this post on the Rust user forum](https://users.rust-lang.org/t/solved-how-to-step-into-std-source-code-when-debugging-in-vs-code/25319/2).

Alternatively `rust-gdb` would also work, but that would mean not being able to use `gef`, `pwndbg` or `peda` (which I consider almost essential).

## Notes ##

While I've tried to make this as platform agnostic as possible, I've only tested it on Linux. Might need some tweaks on other operating systems.
