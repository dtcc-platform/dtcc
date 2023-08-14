# Development

## Coding style

DTCC Platform uses the coding style native to each language or domain.
This means, e.g., following the
[Style Guide](https://peps.python.org/pep-0008/)
for Python code, the
[C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
for C++ code, and the
[Google JSON Style Guide](https://google.github.io/styleguide/jsoncstyleguide.xml)
for JSON.

The following table summarizes the naming conventions used for DTCC
Platform.

|          | Python         | C++            | JavaScript    |
|----------|----------------|----------------|---------------|
| variable | `snake_case`   | `snake_case`   | `camelCase`   |
| function | `snake_case()` | `snake_case()` | `camelCase()` |
| class    | `PascalCase`   | `PascalCase`   | `CamelCase`   |
| module   | `snake_case`   |                |               |

In addition to this, DTCC Platform uses `kebab-case` for naming API endpoints,
branches and scripts. For JSON `camelCase` is used.

Scripts and binaries that are installed on the system should be named
`dtcc-foo-bar`. Scripts that are *not* installed on the system (typically
small utility scripts) should be named `foo-bar` (without `dtcc-`).

## Code formatting

For python code we use the `black` formatter. All python code should be run through `black` with default settings before commiting.  or instructions on how to set it up for Visual Studio Code, see for example.
https://dev.to/adamlombard/how-to-use-the-black-python-code-formatter-in-vscode-3lo0

## Git practices

DTCC Platform uses the following Git practices:

* The main (release) branch for each repository is named `main`.
* The development branch for each repository is named `develop`.
* All work should take place in separate branches (not directly in `develop` and certainly not in `main`).
* Branches for development (new features) should be named `dev/branch-name` where `branch-name` is a free form descriptive name.
* Branches for fixes (bugs, small things) should be named `fix/branch-name` where `branch-name` is a free form descriptive name.
* Branches that will (likely) not be merged but kept for reference should be named `old/branch-name` where `branch-name` is a free form descriptive name.
* Note that hypens should be used for naming (not underscore).
* When the work is done, make a pull request for merging the branch into `develop`.
* When the work has been merged, the branch should be deleted to keep things tidy.
* When making a release, `develop` is merged into `main` and a release is made from `main`.

## Versioning

DTCC Platform uses semantic versioning (SemVer). It uses a three-part number system in the format of MAJOR.MINOR.PATCH, where:

* MAJOR version is incremented for incompatible API changes.
* MINOR version is incremented for new features that are backwards-compatible.
* PATCH version is incremented for backwards-compatible bug fixes.

The version number is set in the `pyproject.toml` file for each repo.

During early development (before the release of 1.0.0) API changes are expected
to happen often and will not lead to incrementation of the MAJOR number (which
stays at 0). During this phase, the MINOR number will work in the same way as
the MAJOR version; that is, the MINOR number should be incremented for incompatible
API changes. Note that the MINOR number may then advance well beyond 9
(e.g. 0.29.1, 0.31.3, etc) before we release 1.0.0.

During early development, the MINOR number should stay the same for all
projects (repos) and post 1.0.0, the MAJOR number should stay the same.

## Tips & tricks

### Using Git submodules

When cloning a repository that may contain submodules, use

    git clone --recursive <url>

If you have already cloned a repository and want to load all submodules, use

    git submodule update --init

### Remote development with sshfs

Remote development is an alternative to local development (building
and running on the host system) and also an alternative to local
development in Docker containers (building and running inside a local
Docker container). The main idea is to build and run on a remote
system, either through an IDE (like Visual Studio Code) or in a
terminal using SSH. Below follows some simple steps for setting up
remote development using SSH on a Mac.

First, install macFUSE needed for mounting remote filesystems via SSH:

    brew install --cask macfuse

Then, mount the desired remote directory using the `sshfs` command,
something like this:

    sshfs -o allow_other,default_permissions logg@compute.dtcc.chalmers.se:/scratch/logg /Users/logg/scratch/compute

For simplicity, this can be put in a little script named
`mount-compute` stored on the local machine:

    #!/usr/bin/env bash
    USER=logg
    SERVER=compute.dtcc.chalmers.se
    LOCAL=/Users/logg/scratch/compute
    REMOTE=compute/scratch/logg
    sshfs -o allow_other,default_permissions $USER@$SERVER:$REMOTE $LOCAL

Note that this should *not* be run as root (using `sudo`) since this
will give you problems with permissions (not able to write files). Also
note that you should not use `~` in the paths since this might be
expanded in the shell and confuse `sshfs` (causing it to hang by
setting up some circular mounting). Instead, full absolute paths
should be used.

The corresponding script for unmounting the remote directory is
`umount-compute`:

    #!/usr/bin/env bash
    LOCAL=/Users/logg/scratch/compute
    umount $LOCAL

Or just run the `umount` command on the directory.

Once the remote directory has been mounted, the remote directory is
available on the local system. Fire up your editor on the local system
to edit source files and do everything else in one or more terminals
to the remote system: `git`, `cmake`, `make` etc.

### Remote development in VS Code

On the left-side menu, go to Remote Explorer, on the SSH line press the + sign and add `username@develop.dtcc.chalmers.se` for the case of user `username` and the host being `develop.dtcc.chalmers.se`

![image](https://user-images.githubusercontent.com/125367195/231126612-d6031bce-ca2d-4340-b0e5-9e728da57238.png)

Then after `develop.dtcc.chalmers.se` appears in the list, click on the connect to current (right arrow) or new window (plus with folder) signs respectively.

![image](https://user-images.githubusercontent.com/125367195/231126959-d1dc6498-576b-42aa-95ce-aff8df80c110.png)

Then you can use `Open...` for opening a folder/file (eg `/home/username/dtcc-builder`) and `Terminal-> New terminal` to have a new terminal connected.

Another CI test, Wednesday!!
