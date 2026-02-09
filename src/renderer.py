"""
renderer.py - Display rendering logic
"""

from machine import Pin, I2C
import ssd1306
import config
import framebuf
import math

class Renderer:
    """Handles all display rendering operations"""
    
    def __init__(self):
        """Initialize display and rendering system"""
        # Initialize I2C
        self.i2c = I2C(0, scl=Pin(config.I2C_SCL), sda=Pin(config.I2C_SDA), 
                      freq=config.I2C_FREQ)
        
        # Initialize OLED display
        self.display = ssd1306.SSD1306_I2C(config.DISPLAY_WIDTH, 
                                           config.DISPLAY_HEIGHT, 
                                           self.i2c)
        
        # Clear display
        self.clear()
        self.show()
    
    def clear(self):
        """Clear the display buffer"""
        self.display.fill(0)
    
    def show(self):
        """Update the physical display with buffer contents"""
        self.display.show()
    
    def draw_character(self, character):
        """
        Draw a character on screen
        For now, draws as a simple filled rectangle
        """
        x, y = character.get_position()
        size = character.size
        
        # Draw filled rectangle for character
        self.display.fill_rect(x, y, size, size, 1)
        
        # Optional: Draw a border to make it look more distinct
        self.display.rect(x, y, size, size, 1)
    
    def draw_text(self, text, x, y, color=1):
        """Draw text at given position

        Args:
            color: 1 for white (default), 0 for black
        """
        self.display.text(text, x, y, color)
    
    def draw_rect(self, x, y, width, height, filled=False, color=1):
        """Draw a rectangle

        Args:
            color: 1 for white (default), 0 for black
        """
        if filled:
            self.display.fill_rect(x, y, width, height, color)
        else:
            self.display.rect(x, y, width, height, color)
    
    def draw_line(self, x1, y1, x2, y2, color=1):
        """Draw a line between two points

        Args:
            color: 1 for white (default), 0 for black
        """
        self.display.line(x1, y1, x2, y2, color)
    
    def draw_pixel(self, x, y, color=1):
        """Draw a single pixel

        Args:
            color: 1 for white (default), 0 for black
        """
        self.display.pixel(x, y, color)
    
    def draw_ui_frame(self):
        """Draw a UI frame around the screen (optional border)"""
        self.display.rect(0, 0, config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, 1)
    
    def draw_fps(self, fps):
        """Draw FPS counter in top-right corner"""
        fps_text = f"{fps:.1f}"
        # Clear small area for FPS
        self.display.fill_rect(config.DISPLAY_WIDTH - 25, 0, 25, 8, 0)
        self.display.text(fps_text, config.DISPLAY_WIDTH - 24, 0)

    def mirror_byte(self, b):
        """Reverse bits in a byte using parallel bit swapping"""
        b = (b & 0xF0) >> 4 | (b & 0x0F) << 4
        b = (b & 0xCC) >> 2 | (b & 0x33) << 2
        b = (b & 0xAA) >> 1 | (b & 0x55) << 1
        return b

    def mirror_sprite_h(self, byte_array, width, height):
        """Mirror a MONO_HLSB sprite horizontally, returns a new bytearray"""
        bytes_per_row = (width + 7) // 8
        result = bytearray(len(byte_array))
        padding = (8 - (width % 8)) % 8  # unused bits on the right of last byte

        for row in range(height):
            row_start = row * bytes_per_row
            # Reverse byte order within row and mirror bits in each byte
            for col in range(bytes_per_row):
                src_byte = byte_array[row_start + (bytes_per_row - 1 - col)]
                result[row_start + col] = self.mirror_byte(src_byte)

            # Shift row left to move padding from left side back to right
            if padding > 0:
                for col in range(bytes_per_row):
                    current = result[row_start + col]
                    next_byte = result[row_start + col + 1] if col + 1 < bytes_per_row else 0
                    result[row_start + col] = ((current << padding) | (next_byte >> (8 - padding))) & 0xFF

        return result

    def mirror_sprite_v(self, byte_array, width, height):
        """Mirror a MONO_HLSB sprite vertically, returns a new bytearray"""
        bytes_per_row = (width + 7) // 8
        result = bytearray(len(byte_array))

        for row in range(height):
            src_start = row * bytes_per_row
            dst_start = (height - 1 - row) * bytes_per_row
            result[dst_start:dst_start + bytes_per_row] = byte_array[src_start:src_start + bytes_per_row]

        return result

    def rotate_sprite(self, byte_array, width, height, angle):
        """Rotate a MONO_HLSB sprite by the given angle in degrees.

        Uses naive nearest-neighbor rotation. Pixel-perfect for 90° increments.

        Returns (rotated_bytearray, new_width, new_height)
        """
        # Convert to radians
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # Calculate new bounding box size
        new_width = int(abs(width * cos_a) + abs(height * sin_a) + 0.5)
        new_height = int(abs(width * sin_a) + abs(height * cos_a) + 0.5)

        # Ensure minimum size of 1
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        # Source and destination centers
        src_cx = width / 2
        src_cy = height / 2
        dst_cx = new_width / 2
        dst_cy = new_height / 2

        # Create result bytearray
        src_bytes_per_row = (width + 7) // 8
        dst_bytes_per_row = (new_width + 7) // 8
        result = bytearray(dst_bytes_per_row * new_height)

        # For each destination pixel, find source pixel (inverse mapping)
        for dy in range(new_height):
            for dx in range(new_width):
                # Translate to center-relative
                rx = dx - dst_cx
                ry = dy - dst_cy

                # Inverse rotation (rotate by -angle to find source)
                sx = rx * cos_a + ry * sin_a + src_cx
                sy = -rx * sin_a + ry * cos_a + src_cy

                # Round to nearest integer
                sx_int = int(sx + 0.5)
                sy_int = int(sy + 0.5)

                # Check bounds
                if 0 <= sx_int < width and 0 <= sy_int < height:
                    # Get source pixel (MONO_HLSB: MSB is leftmost)
                    src_byte_idx = sy_int * src_bytes_per_row + sx_int // 8
                    src_bit = 7 - (sx_int % 8)
                    pixel = (byte_array[src_byte_idx] >> src_bit) & 1

                    if pixel:
                        # Set destination pixel
                        dst_byte_idx = dy * dst_bytes_per_row + dx // 8
                        dst_bit = 7 - (dx % 8)
                        result[dst_byte_idx] |= (1 << dst_bit)

        return result, new_width, new_height

    def draw_debug_info(self, info_dict, start_y=0):
        """
        Draw debug information on screen
        info_dict: dictionary of label->value pairs
        """
        y = start_y
        for label, value in info_dict.items():
            text = f"{label}:{value}"
            self.display.text(text, 0, y)
            y += 8
            if y >= config.DISPLAY_HEIGHT:
                break

    def draw_sprite(self, byte_array, width, height, x, y, transparent=True, invert=False, transparent_color=0, mirror_h=False, mirror_v=False, rotate=0):
        """Draw a sprite at the given position

        Args:
            byte_array: bytearray containing the sprite bitmap
            width: sprite width in pixels
            height: sprite height in pixels
            x: x position on display
            y: y position on display
            transparent: if True, pixels matching transparent_color are transparent
            invert: if True, flip all pixel colors (white becomes black, etc.)
            transparent_color: which color to treat as transparent (0=black, 1=white)
            mirror_h: if True, flip the sprite horizontally
            mirror_v: if True, flip the sprite vertically
            rotate: rotation angle in degrees (clockwise)
        """

        # Mirror horizontally if requested
        if mirror_h:
            byte_array = self.mirror_sprite_h(byte_array, width, height)

        # Mirror vertically if requested
        if mirror_v:
            byte_array = self.mirror_sprite_v(byte_array, width, height)

        # Rotate if requested
        if rotate != 0:
            # Adjust position so sprite rotates around its center
            old_cx = x + width // 2
            old_cy = y + height // 2
            byte_array, width, height = self.rotate_sprite(byte_array, width, height, rotate)
            x = old_cx - width // 2
            y = old_cy - height // 2

        # Invert colors if requested
        if invert:
            byte_array = bytearray(b ^ 0xFF for b in byte_array)

        # Create a framebuffer from the sprite data
        sprite_fb = framebuf.FrameBuffer(
            byte_array,
            width,
            height,
            framebuf.MONO_HLSB  # or MONO_VLSB
        )

        if transparent:
            # Draw with transparency - pixels matching transparent_color are not drawn
            self.display.blit(sprite_fb, x, y, transparent_color)
        else:
            # Draw without transparency (overwrites everything)
            self.display.blit(sprite_fb, x, y)

    def draw_sprite_obj(self, sprite, x, y, frame=0, transparent=True, invert=False, mirror_h=False, mirror_v=False, rotate=0):
        """Draw a sprite object at the given position

        Args:
            sprite: dict with 'width', 'height', and 'frames' keys
                    optionally includes 'fill_frames' for solid fill behind outline
            x: x position on display
            y: y position on display
            frame: which frame to draw (default 0)
            transparent: if True, black pixels (0) are transparent
            invert: if True, flip all pixel colors
            mirror_h: if True, flip the sprite horizontally
            mirror_v: if True, flip the sprite vertically
            rotate: rotation angle in degrees (clockwise)
        """
        # If sprite has fill_frames, draw the fill first (in black)
        # Invert so white fill becomes black, use white as transparent color
        if "fill_frames" in sprite:
            self.draw_sprite(
                sprite["fill_frames"][frame],
                sprite["width"],
                sprite["height"],
                x, y,
                transparent=True,
                invert=True,
                transparent_color=1,
                mirror_h=mirror_h,
                mirror_v=mirror_v,
                rotate=rotate
            )

        self.draw_sprite(
            sprite["frames"][frame],
            sprite["width"],
            sprite["height"],
            x, y,
            transparent,
            invert,
            mirror_h=mirror_h,
            mirror_v=mirror_v,
            rotate=rotate
        )
