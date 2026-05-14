"""
difference_region.py
Data model for a single difference region on the modified image.

Group Member: Jenish Gurung

"""


class DifferenceRegion:
    """
    Represents one rectangular region where the modified image
    differs from the original.

    Demonstrates encapsulation: all internal data uses private _attributes
    exposed only through read-only properties, except 'found' which has
    a setter so GameState can update it.
    """

    def __init__(self, x: int, y: int, w: int, h: int, diff_type: str):
        """
        Initialise a difference region.

        Parameters:
            x, y      : top-left corner of the region in image coordinates
            w, h      : width and height of the patch in pixels
            diff_type : name of the alteration applied (e.g. 'strong_hue')
        """
        self._x         = x
        self._y         = y
        self._w         = w
        self._h         = h
        self._diff_type = diff_type
        self._found     = False   # True once the player locates this difference

    # ── Properties ────────────────────────────────────────────────────

    @property
    def x(self) -> int:
        """Left edge of the region in image pixels."""
        return self._x

    @property
    def y(self) -> int:
        """Top edge of the region in image pixels."""
        return self._y

    @property
    def w(self) -> int:
        """Width of the region in image pixels."""
        return self._w

    @property
    def h(self) -> int:
        """Height of the region in image pixels."""
        return self._h

    @property
    def diff_type(self) -> str:
        """Name of the OpenCV alteration type applied to this region."""
        return self._diff_type

    @property
    def found(self) -> bool:
        """True if the player has already found this difference."""
        return self._found

    @found.setter
    def found(self, value: bool) -> None:
        """Allows GameState to mark this region as found after a correct click."""
        self._found = bool(value)

    @property
    def center(self) -> tuple:
        """
        Return (cx, cy) centre point of this region.
        Used for drawing circles and for click hit-testing.
        """
        return (self._x + self._w // 2, self._y + self._h // 2)

    @property
    def radius(self) -> int:
        """
        Approximate circle radius that visually covers this region.
        Adds 10 px padding so the drawn ring is slightly larger than the patch.
        """
        return max(self._w, self._h) // 2 + 10

    # ── Public methods ────────────────────────────────────────────────

    def contains_point(self, px: int, py: int, tolerance: int = 30) -> bool:
        """
        Return True if a player click at (px, py) falls within this region.

        Uses circular distance from the region centre so the hit area feels
        natural. The tolerance margin forgives slightly off-centre clicks.

        Parameters:
            px, py    : click coordinates in image space (not canvas space)
            tolerance : extra leniency in pixels beyond the region radius
        """
        cx, cy = self.center
        dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
        return dist <= self.radius + tolerance

    def overlaps(self, other: "DifferenceRegion", padding: int = 20) -> bool:
        """
        Return True if this region overlaps another region (with padding gap).

        Called by ImageProcessor while placing 5 differences to ensure
        none of the patches touch or overlap each other.

        Parameters:
            other   : another DifferenceRegion to compare against
            padding : minimum pixel gap required between the two regions
        """
        return not (
            self._x + self._w + padding <= other.x
            or other.x + other.w + padding <= self._x
            or self._y + self._h + padding <= other.y
            or other.y + other.h + padding <= self._y
        )

    def __repr__(self) -> str:
        """Human-readable string for debugging purposes."""
        return (
            f"DifferenceRegion(type={self._diff_type!r}, "
            f"x={self._x}, y={self._y}, "
            f"w={self._w}, h={self._h}, "
            f"found={self._found})"
        )
