"""
game_state.py


Defines:
  BaseGame   – abstract base class (inheritance / polymorphism root)
  GameState  – concrete subclass managing per-round and cumulative state

Group member: Roshan Gautam
Student ID: S394913
"""

from difference_region import DifferenceRegion


class BaseGame:
    """
    Abstract base class defining the game interface.

    Provides shared constants and the reset_round contract
    that subclasses must implement (polymorphism).
    """

    MAX_MISTAKES    = 3
    TOTAL_DIFFS     = 5

    def __init__(self):
        self._cumulative_score: int  = 0
        self._mistakes:         int  = 0
        self._locked:           bool = False   # True when mistakes maxed out
        self._revealed:         bool = False

    # ── Read-only properties ──────────────────────────────────────────
    @property
    def cumulative_score(self) -> int:
        return self._cumulative_score

    @property
    def mistakes(self) -> int:
        return self._mistakes

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def revealed(self) -> bool:
        return self._revealed

    # ── Abstract contract ─────────────────────────────────────────────
    def reset_round(self) -> None:
        """Reset per-image state. Must be overridden by subclass."""
        raise NotImplementedError


class GameState(BaseGame):
    """
    Concrete game-state class.

    Inherits from BaseGame and adds:
      - ImageProcessor composition
      - Per-click validation logic
      - Reveal-all functionality
      - Cumulative score tracking across multiple images
    """

    def __init__(self):
        super().__init__()
        # Lazily set when an image is loaded
        self._processor = None
        self._loaded    = False

    # ── Setup ─────────────────────────────────────────────────────────
    def attach_processor(self, processor) -> None:
        """
        Attach an ImageProcessor after it has successfully loaded
        an image.  Resets the round automatically.
        """
        self._processor = processor
        self._loaded    = True
        self.reset_round()

    # ── Polymorphic override ──────────────────────────────────────────
    def reset_round(self) -> None:
        """
        Reset per-round counters.
        Cumulative score is intentionally preserved.
        """
        self._mistakes  = 0
        self._locked    = False
        self._revealed  = False
        if self._processor:
            for r in self._processor.regions:
                r.found = False

    # ── Read-only helpers ─────────────────────────────────────────────
    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def processor(self):
        return self._processor

    @property
    def regions(self) -> list:
        return self._processor.regions if self._processor else []

    @property
    def found_count(self) -> int:
        return sum(1 for r in self.regions if r.found)

    @property
    def remaining_count(self) -> int:
        return self.TOTAL_DIFFS - self.found_count

    @property
    def all_found(self) -> bool:
        return self.found_count == self.TOTAL_DIFFS

    # ── Game actions ──────────────────────────────────────────────────
    def register_click(self, img_x: int, img_y: int) -> dict:
        """
        Process a player click at image-space coordinates.

        Returns a result dict:
          hit        – True if a difference was found
          region     – the matched DifferenceRegion (or None)
          mistake    – True if the click was a miss
          locked     – True if the round is now over (max mistakes)
          all_found  – True if all differences are now found
        """
        if not self._loaded or self._locked or self._revealed:
            return {
                "hit": False, "region": None,
                "mistake": False, "locked": self._locked,
                "all_found": False,
            }

        for region in self.regions:
            if not region.found and region.contains_point(img_x, img_y):
                region.found         = True
                self._cumulative_score += 1
                return {
                    "hit":       True,
                    "region":    region,
                    "mistake":   False,
                    "locked":    False,
                    "all_found": self.all_found,
                }

        # Miss
        self._mistakes += 1
        if self._mistakes >= self.MAX_MISTAKES:
            self._locked = True

        return {
            "hit":       False,
            "region":    None,
            "mistake":   True,
            "locked":    self._locked,
            "all_found": False,
        }

    def reveal_all(self) -> None:
        """
        Mark all remaining differences as revealed.
        Locks the round so no further clicks are processed.
        """
        self._revealed = True
        self._locked   = True