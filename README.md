# Minesweeper (Python/Pygame)

A robust, standard-compliant implementation of the classic game Minesweeper, built entirely in Python using the Pygame library.

## Dependencies

- **Python**: 3.8+ recommended
- **Pygame**: 2.6+

To install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

Execute the main script from the root directory:
```bash
python main.py
```

## Features and Mechanics

### Difficulties
The game implements standard preset difficulties with a scaling grid structure:
- **Beginner**: 9x9 grid, 10 mines
- **Intermediate**: 16x16 grid, 40 mines
- **Expert**: 30x16 grid, 99 mines

**Custom Difficulty**:
Users can select "Custom" to specify an arbitrary grid size via an interactive dialog limit-clamped to between 5 and 50 columns, and 5 and 30 rows. 
The mine count `M` for custom grids is procedurally generated using the polynomial formula:
`M = floor(T * (0.12 + 0.00018 * T))`
*(where `T` is the total number of tiles `rows * cols`)*

### Core Logic
*   **Guaranteed Opening**: Mine generation is deferred until the user's first click. The algorithm explicitly excludes the clicked tile and its 8 immediate surrounding neighbors from mine deployment, guaranteeing at least a clear 3x3 initial opening.
*   **Recursive Reveal**: Clicking an empty tile triggers a flood-fill algorithm that recursively reveals contiguous empty tiles up to their numbered borders.

### User Interface & Experience
*   **Dynamic Scaling**: The Pygame window traps `VIDEORESIZE` events. The internal rendering surface calculates optimal cell square dimensions bounded dynamically by desktop bounds and the currently requested grid columns and rows.
*   **State Tracking**: 
    *   **Timer**: Starts on the first click. Displays fractional decimal precision on game resolution (win/loss).
    *   **Flag Counter**: Prevents deploying more flags than the instantiated mine threshold.
    *   **Database Best Times**: Logs optimal clear times for the predefined difficulties via a local `sqlite3` database (`times.db`), visually indicating records upon game completion.
*   **Visual Customization**: An integrated UI drop-down menu actively mutates local constants to one of 8 standardized RGB color themes, applying corresponding shading, highlights, and shadow algorithms.
*   **Styling and Aesthetics**: Replaced system default fonts with a pixelated `PressStart2P` typography natively rendered without anti-aliasing to provide a retro feel, accompanied by soft scale-in animations for tile reveals and item deployments.

## Project Structure
*   `main.py`: Core application payload hosting the game event loop, rendering pipeline, and object-oriented structure (`Game`, `Board`, `Button`, `Dropdown`, `TextInput`).
*   `constants.py`: Stores application constants including default dimensions, static bounds, and the `THEMES` color map dictionaries.
