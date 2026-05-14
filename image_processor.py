"""
image_processor.py

Group Member: Jenish Gurung

"""

import cv2
import numpy as np
import random

from difference_region import DifferenceRegion


class ImageProcessor:
    """
    Loads an image, clones it, and injects exactly 5 clearly visible
    differences into the clone using OpenCV.

    Alteration types (5 total):
        1. strong_hue      - aggressive HSV hue rotation (~120 degrees)
        2. brightness      - large exposure push (+80) or pull (-70)
        3. saturation_swap - drains colour to grey OR boosts to vivid
        4. heavy_blur      - strong double Gaussian blur (31x31 kernel)
        5. colour_tint     - blends a solid vivid colour at 55% opacity

    Design choices for visibility:
        - Large patch sizes (80-140 px) so regions cover meaningful area
        - Strong alteration values so the eye picks up the change quickly
        - Feathered edges so each patch blends naturally (no hard border)
    """

    NUM_DIFFERENCES = 5   # Exactly 5 differences per round as required

    # Patch size range in pixels — larger patches are easier to spot
    MIN_REGION = 80
    MAX_REGION = 140

    def __init__(self):
        """
        Initialise with empty state.
        Images and regions are populated when load() is called.
        """
        self._original: np.ndarray | None = None
        self._modified: np.ndarray | None = None
        self._regions:  list[DifferenceRegion] = []

    # ── Public API ────────────────────────────────────────────────────

    def load(self, path: str) -> bool:
        """
        Read an image from disk and generate a modified clone with
        exactly NUM_DIFFERENCES clearly visible alterations.

        Parameters:
            path : full file path to the image (JPG, PNG, or BMP)

        Returns:
            True  if the image loaded and differences were generated
            False if the file could not be opened by OpenCV
        """
        img = cv2.imread(path)
        if img is None:
            return False
        self._original = img.copy()
        self._modified, self._regions = self._build_modified(img)
        return True

    @property
    def original(self) -> np.ndarray:
        """The unmodified original image as a NumPy BGR array."""
        return self._original

    @property
    def modified(self) -> np.ndarray:
        """The cloned image with 5 hidden differences applied."""
        return self._modified

    @property
    def regions(self) -> list[DifferenceRegion]:
        """List of the 5 DifferenceRegion objects for the current image."""
        return self._regions

    def display_pair(self, max_w: int, max_h: int) -> tuple:
        """
        Return (original_rgb, modified_rgb) — both images resized to fit
        inside max_w x max_h while preserving their aspect ratio.
        Converts from BGR (OpenCV) to RGB (Pillow/Tkinter) automatically.

        Parameters:
            max_w, max_h : maximum display dimensions in pixels
        """
        orig_rgb = cv2.cvtColor(
            self._fit(self._original, max_w, max_h), cv2.COLOR_BGR2RGB)
        mod_rgb  = cv2.cvtColor(
            self._fit(self._modified, max_w, max_h), cv2.COLOR_BGR2RGB)
        return orig_rgb, mod_rgb

    def scale_info(self, display_w: int, display_h: int) -> tuple:
        """
        Return (scale, offset_x, offset_y) for mapping image coordinates
        to canvas coordinates.

        Because images are centred inside the canvas, an offset is needed
        to correctly translate a canvas click back to image pixel position.

        Parameters:
            display_w, display_h : canvas dimensions in pixels
        """
        h, w  = self._original.shape[:2]
        scale = min(display_w / w, display_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        off_x = (display_w - new_w) // 2
        off_y = (display_h - new_h) // 2
        return scale, off_x, off_y

    def canvas_to_image(self, cx: int, cy: int,
                        display_w: int, display_h: int) -> tuple:
        """
        Convert a canvas pixel position (cx, cy) to the corresponding
        original image pixel position (ix, iy).

        This is used to translate the player's click on the Tkinter canvas
        into image-space coordinates that can be tested against regions.

        Parameters:
            cx, cy            : click position on the Tkinter canvas
            display_w/display_h : dimensions of the canvas widget
        """
        scale, off_x, off_y = self.scale_info(display_w, display_h)
        return int((cx - off_x) / scale), int((cy - off_y) / scale)

    # ── Core builder ──────────────────────────────────────────────────

    def _build_modified(
        self, original: np.ndarray
    ) -> tuple[np.ndarray, list[DifferenceRegion]]:
        """
        Clone the original image and place exactly NUM_DIFFERENCES
        non-overlapping, clearly visible alterations.

        One of each of the 5 alteration methods is used per round.
        Their order and positions are randomised every time an image loads.

        Parameters:
            original : the source image as a BGR NumPy array

        Returns:
            (modified image, list of DifferenceRegion objects)
        """
        modified = original.copy()
        h, w     = original.shape[:2]

        # All 5 alteration methods, shuffled so order is random each round
        methods = [
            self._strong_hue,
            self._brightness,
            self._saturation_swap,
            self._heavy_blur,
            self._colour_tint,
        ]
        random.shuffle(methods)

        placed:   list[DifferenceRegion] = []
        attempts: int = 0

        # Keep trying random positions until 5 non-overlapping ones are found
        while len(placed) < self.NUM_DIFFERENCES and attempts < 800:
            attempts += 1

            rw = random.randint(self.MIN_REGION, self.MAX_REGION)
            rh = random.randint(self.MIN_REGION, self.MAX_REGION)

            # Keep patches away from the very edge so feathering works
            margin = 10
            if w < rw + 2 * margin or h < rh + 2 * margin:
                continue
            rx = random.randint(margin, w - rw - margin)
            ry = random.randint(margin, h - rh - margin)

            # Reject this position if it overlaps any already-placed region
            candidate = DifferenceRegion(rx, ry, rw, rh, "")
            if any(candidate.overlaps(p) for p in placed):
                continue

            # Apply the alteration and record the region
            method    = methods[len(placed)]
            type_name = method.__name__.lstrip("_")
            region    = DifferenceRegion(rx, ry, rw, rh, type_name)
            method(modified, rx, ry, rw, rh)
            placed.append(region)

        return modified, placed

    # ── Feathered blending helper ─────────────────────────────────────

    @staticmethod
    def _blend_feathered(img: np.ndarray,
                         altered_roi: np.ndarray,
                         x: int, y: int,
                         w: int, h: int,
                         feather: int = 12) -> None:
        """
        Paste an altered patch into the image with a soft feathered edge
        so the difference doesn't have an obvious hard rectangular border.

        A gradient mask (0 to 1) is built that ramps from transparent at
        the edges to fully opaque in the centre. This blends the original
        and altered pixels smoothly near the patch boundary.

        Parameters:
            img        : the image to paste into (modified in place)
            altered_roi: the altered version of the patch
            x, y       : top-left corner of the patch
            w, h       : size of the patch
            feather    : number of pixels over which the blend fades
        """
        # Build a float alpha mask the same size as the ROI
        mask = np.ones((h, w), dtype=np.float32)

        # Ramp down opacity at each of the 4 edges
        for i in range(feather):
            alpha = i / feather
            if i < h:
                mask[i,     :] = np.minimum(mask[i,     :], alpha)
                mask[h-1-i, :] = np.minimum(mask[h-1-i, :], alpha)
            if i < w:
                mask[:,   i  ] = np.minimum(mask[:,   i  ], alpha)
                mask[:, w-1-i] = np.minimum(mask[:, w-1-i], alpha)

        mask3 = mask[:, :, np.newaxis]   # broadcast over BGR channels

        original_roi = img[y:y+h, x:x+w].astype(np.float32)
        altered_f    = altered_roi.astype(np.float32)
        blended      = original_roi * (1 - mask3) + altered_f * mask3
        img[y:y+h, x:x+w] = np.clip(blended, 0, 255).astype(np.uint8)

    # ── Alteration 1: Strong hue rotation ────────────────────────────

    def _strong_hue(self, img: np.ndarray,
                    x: int, y: int, w: int, h: int) -> None:
        """
        Rotate the hue of the patch by 100-140 degrees in HSV colour space.

        This turns greens purple, blues orange, etc. — a very noticeable
        colour shift that still looks like part of a real photograph.

        Parameters:
            img  : image to modify in place
            x, y : top-left corner of the patch
            w, h : patch dimensions
        """
        roi = img[y:y+h, x:x+w].copy()
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV).astype(np.int32)
        shift = random.choice([100, 110, 120, 130, 140])
        hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 180
        altered = cv2.cvtColor(
            np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
        self._blend_feathered(img, altered, x, y, w, h)

    # ── Alteration 2: Strong brightness push/pull ─────────────────────

    def _brightness(self, img: np.ndarray,
                    x: int, y: int, w: int, h: int) -> None:
        """
        Significantly lighten (+80) or darken (-70) the patch.

        The large exposure jump makes this obvious even in busy textures
        and is one of the easiest differences to spot.

        Parameters:
            img  : image to modify in place
            x, y : top-left corner of the patch
            w, h : patch dimensions
        """
        roi   = img[y:y+h, x:x+w].copy().astype(np.int32)
        delta = random.choice([80, 85, 90, -70, -75, -80])
        altered = np.clip(roi + delta, 0, 255).astype(np.uint8)
        self._blend_feathered(img, altered, x, y, w, h)

    # ── Alteration 3: Saturation swap ─────────────────────────────────

    def _saturation_swap(self, img: np.ndarray,
                         x: int, y: int, w: int, h: int) -> None:
        """
        Either fully desaturate the patch to near-grey, or push saturation
        to maximum (hyper-vivid colours). Both outcomes are unmistakeable.

        Randomly chooses between the two modes each round.

        Parameters:
            img  : image to modify in place
            x, y : top-left corner of the patch
            w, h : patch dimensions
        """
        roi = img[y:y+h, x:x+w].copy()
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV).astype(np.int32)

        if random.random() < 0.5:
            # Desaturate — grey patch stands out in a colourful image
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] - 220, 0, 255)
        else:
            # Over-saturate — garish vivid colours stand out immediately
            hsv[:, :, 1] = 255

        altered = cv2.cvtColor(
            np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
        self._blend_feathered(img, altered, x, y, w, h)

    # ── Alteration 4: Heavy blur ───────────────────────────────────────

    def _heavy_blur(self, img: np.ndarray,
                    x: int, y: int, w: int, h: int) -> None:
        """
        Apply a 31x31 Gaussian blur twice for a very strong smearing effect.

        Creates an obvious soft/blurred patch that stands out sharply
        against the surrounding sharp detail of a natural photograph.

        Parameters:
            img  : image to modify in place
            x, y : top-left corner of the patch
            w, h : patch dimensions
        """
        roi     = img[y:y+h, x:x+w].copy()
        blurred = cv2.GaussianBlur(roi, (31, 31), 0)
        blurred = cv2.GaussianBlur(blurred, (31, 31), 0)  # double blur for strength
        self._blend_feathered(img, blurred, x, y, w, h)

    # ── Alteration 5: Colour tint overlay ────────────────────────────

    def _colour_tint(self, img: np.ndarray,
                     x: int, y: int, w: int, h: int) -> None:
        """
        Blend a solid vivid colour over the patch at 55% opacity.

        Available tints: red, cyan, yellow, magenta, lime green, deep blue.
        The original image texture still shows through (45% original pixels),
        which makes it look like a colour filter rather than a solid block.

        Parameters:
            img  : image to modify in place
            x, y : top-left corner of the patch
            w, h : patch dimensions
        """
        tint_colours = [
            (0,   0,   220),   # red
            (220, 220,   0),   # cyan
            (0,   220, 220),   # yellow
            (220,   0, 220),   # magenta
            (0,   200,   0),   # lime green
            (200, 100,   0),   # deep blue
        ]
        colour = random.choice(tint_colours)
        roi    = img[y:y+h, x:x+w].copy().astype(np.float32)

        tint_layer    = np.full_like(roi, colour, dtype=np.float32)
        tint_strength = 0.55   # 55% tint colour, 45% original image
        altered_f     = roi * (1 - tint_strength) + tint_layer * tint_strength
        altered       = np.clip(altered_f, 0, 255).astype(np.uint8)
        self._blend_feathered(img, altered, x, y, w, h)

    # ── Utility ───────────────────────────────────────────────────────

    @staticmethod
    def _fit(img: np.ndarray, max_w: int, max_h: int) -> np.ndarray:
        """
        Resize an image to fit inside max_w x max_h while preserving
        its aspect ratio. Never upscales (scale is capped at 1.0).

        Parameters:
            img           : source image as a NumPy array
            max_w, max_h  : maximum output dimensions in pixels
        """
        h, w  = img.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        nw    = int(w * scale)
        nh    = int(h * scale)
        return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
