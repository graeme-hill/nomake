# nomake

**Note:** The script is currently unfinished and does not behave exactly as
described below. This documentation is more of a spec at this point.

Nomake is a simple build system that uses folder conventions and a module
system instead of project files or make files to compile a project. The goal is
not just to make build configuration easier, but also to change the way the
programmer designs the code without creating a dependecy of any IDE.

## Examples

### Example 1: Basic Project

There is only one module, so its `src` directory is in the root folder. No
arguments need to be passed to `nomake.py` and in this case `targets.py` is not
required.

#### Directory Structure

    -my_project
    --src
    ---one.h
    ---one.c
    ---two.h
    ---two.c
    --nomake.py

#### Build command

    ./nomake.py

#### Explanation

Since there is no `targets.py` file, nomake will assume that the root directory
is a module itself and compile the contents of `src`. Behind the scenes, the 
compiler's `-MM` option is used to derive dependencies from a source file. This
information is used to decide which source files need to be recompiled based on
the timestamps of any object files that are already in the `obj` directory. If
a file or any of its dependencies have changed since the last compile, then its
object file will be rebuilt, otherwise it does nothing to improve compilation
speed.

### Example 2: Multiple Targets

Since there are multiple modules (`Common`, `MacOSX`, `Linux`, and `Windows`)
targers must be defined in `targets.py`.

#### Directory Structure

    -my_project
    --common
    ---src
    ----one.h
    ----one.c
    ----two.h
    --mac
    ---src
    ----two.c
    --linux
    ---src
    ----two.c
    --windows
    ---src
    ----two.c
    --targets.py

#### targets.py

    (
        Platform(name='mac', modules=('common', 'mac')),
        Platform(name='windows', modules=('common', 'windows')),
        Platform(name='linux', modules=('common', 'linux'))
    )

#### Build Command

    ./nomake.py mac

or

    ./nomake.py linux

or

    ./nomake.py windows

#### Explanation

This is where nomake gets useful. Instead of sing a set of `ifdef`s to include
different code in each platform, independent modules can be defined for each
one. In this case, there is a different implementation of `two.c` for each OS.
