"""Registry and startup validation for the game's five modes."""
from dataclasses import dataclass


class ModeNotImplementedError(ValueError):
    """Raised when a registered mode has no gameplay implementation yet."""


@dataclass(frozen=True)
class GameMode:
    """Metadata for one selectable game mode."""

    id: str
    name: str
    selection_key: str
    implemented: bool
    description: str


class GameModeManager:
    """List, select, and start registered modes."""

    DEFAULT_MODES = (
        GameMode(
            id="classic",
            name="Classic",
            selection_key="1",
            implemented=True,
            description="Collect food, grow, and avoid collisions.",
        ),
        GameMode(
            id="obstacle",
            name="Obstacle",
            selection_key="2",
            implemented=False,
            description="Navigate around obstacles.",
        ),
        GameMode(
            id="power_up",
            name="Power-Up",
            selection_key="3",
            implemented=False,
            description="Collect temporary power-ups.",
        ),
        GameMode(
            id="two_player_battle",
            name="Two-Player Battle",
            selection_key="4",
            implemented=True,
            description="Compete with a second player on the same board.",
        ),
        GameMode(
            id="survival",
            name="Survival",
            selection_key="5",
            implemented=False,
            description="Survive as the challenge increases.",
        ),
    )

    def __init__(self):
        self._modes = {mode.id: mode for mode in self.DEFAULT_MODES}
        self._selection_keys = {
            mode.selection_key: mode.id for mode in self.DEFAULT_MODES
        }

    def list_modes(self):
        """Return all registered modes in menu order."""
        return self.DEFAULT_MODES

    def select_mode(self, mode_id):
        """Resolve a mode by id, display name, or its menu selection key."""
        if not isinstance(mode_id, str):
            raise ValueError("mode must be selected by name, id, or menu key")
        requested = mode_id.strip().lower()
        if requested in self._selection_keys:
            requested = self._selection_keys[requested]
        else:
            requested = requested.replace("-", "_").replace(" ", "_")
        try:
            return self._modes[requested]
        except KeyError as exc:
            raise ValueError(f"unknown game mode: {mode_id!r}") from exc

    def create_game(self, mode_id, **game_options):
        """Create a session for an implemented mode, or report it unavailable."""
        mode = self.select_mode(mode_id)
        if not mode.implemented:
            raise ModeNotImplementedError(
                f"{mode.name} Mode is registered but is not implemented yet."
            )

        # Import locally to keep the registry independent from engine startup.
        if mode.id == "two_player_battle":
            from engine.two_player_game_state import TwoPlayerGameState

            return TwoPlayerGameState(mode=mode.id, **game_options)

        from engine.game_state import GameState

        return GameState(mode=mode.id, **game_options)
