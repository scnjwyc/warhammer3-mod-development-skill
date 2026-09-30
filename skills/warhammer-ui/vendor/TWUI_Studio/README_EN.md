# TWUI Studio 0.22.2 — Total War: WARHAMMER III TWUI XML Editor

TWUI Studio is an unofficial visual TWUI XML editor for Total War: WARHAMMER III modding. It provides a component tree, approximate live preview, property and state/layout editing, original comparison, project saving, and XML-with-images export.

> **Project status: Maintenance mode**  
> The application and source are provided as-is. Bug reports and improvements are welcome, but updates and responses are not guaranteed.

## Required resource setup

TWUI Studio does not read resources directly from the game's `.pack` files.

1. Use **RPFM or AssetEditor** to extract the game's complete `ui` folder.
2. In TWUI Studio, open **Settings → Original UI Resources → Path settings**.
3. Select the extracted **top-level `ui` folder itself**—the folder containing directories such as `skins`, `campaign ui`, `battle ui`, and `templates`.

Example: `D:\ModData\ui`

Selecting only the game installation directory cannot expose XML or images stored inside `.pack` files. If needed, place extracted `sprite_anims` and `units` data at `ui\sprite_anims` and `ui\units`. The full game resource library is not bundled with this distribution or repository.

## Run from source

1. Install Python 3.10 or later. On Windows, include Tcl/Tk and the Python Launcher.
2. Extract the entire ZIP to a writable folder.
3. Run `START_WINDOWS.bat`.

The first run creates a virtual environment and installs Pillow, so it requires an internet connection. To run manually:

```text
python -m pip install -r requirements.txt
python app.py
```

## Build the Windows application

On Windows 10/11 with 64-bit Python 3.12, run `BUILD_WINDOWS.bat`. A successful build creates `exe_version_package/TWUI_Studio_0.22.2_Windows_x64.zip`.

## Basic workflow

1. Configure the extracted original `ui` folder.
2. Import a TWUI XML file or open the included example.
3. Select a component in the tree or canvas and edit it in Properties.
4. Use `Ctrl+Z` / `Ctrl+Shift+Z` for undo and redo.
5. Save a project or export XML + images.
6. Import the exported loose files with RPFM and verify the result in game.

The preview is not a complete game renderer. Verify Lua/CCO behavior, font-driven sizing, shaders, animation, clipping, and final layout in the game.

## Highlights

- Multiple TWUI XML document tabs and component trees
- Zoomable, pannable preview with original comparison
- Component ID, position, dimensions, docking, callbacks, CCO, images, States, and Layout editing
- Project save/restore with preservation-oriented XML editing
- LOC TSV and dynamic-text preview
- XML view, search, and copy tools
- XML and referenced-image export using original `ui/` paths
- Korean and English interface

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and validation notes.

## Examples and game resources

`examples/` contains a small XML, localization, and icon set used to demonstrate the program. It does not contain the complete game UI library. Rights in original game XML, images, and trademarks remain with Creative Assembly, SEGA, Games Workshop, and their respective owners.

## License

Viewing and modifying the source, and creating or redistributing derivative versions for non-commercial purposes, are permitted. Selling TWUI Studio or derivatives, offering them as a paid service, or otherwise exploiting them commercially is prohibited. This is a **source-available non-commercial license**, not an OSI-approved open-source license. See [LICENSE.txt](LICENSE.txt) for the complete terms.

Co-created by Steam Workshop mod creator **Backmechuisa & gpt-6 Astra**.

