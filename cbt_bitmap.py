"""
Provides a class wrapping the return value of VDI.list_changed_blocks for
extracting useful information from the CBT bitmap.
"""

import base64

from bitstring import BitArray


# 64K blocks
BLOCK_SIZE = 64 * 1024


def _bitmap_to_extents(cbt_bitmap):
    """
    Given a CBT bitmap with 64K block size, this function will return the
    list of changed (offset in bytes, length in bytes) extents.

    Args:
        cbt_bitmap (bytes-like object): the bitmap to turn into extents

    Returns:
        An iterator containing the increasingly ordered sequence of the
        non-overlapping extents corresponding to this bitmap.
    """
    start = None
    bitmap = BitArray(cbt_bitmap)
    for i in range(0, len(bitmap)):
        if bitmap[i]:
            if start is None:
                start = i
                length = 1
            else:
                length += 1
        else:
            if start is not None:
                yield (start * BLOCK_SIZE, length * BLOCK_SIZE)
                start = None
    if start is not None:
        yield (start * BLOCK_SIZE, length * BLOCK_SIZE)


def _get_changed_blocks_size(cbt_bitmap):
    """
    Returns the overall size of the changed 64K blocks in the
    given bitmap in bytes.
    """
    bitmap = BitArray(cbt_bitmap)
    modified = 0
    for bit in bitmap:
        if bit:
            modified += 1
    return modified * BLOCK_SIZE


def _get_disk_size(cbt_bitmap):
    bitmap = BitArray(cbt_bitmap)
    return len(bitmap) * BLOCK_SIZE

def _get_extent_stats(extents):
    average_length = None
    max_length = None
    min_length = None
    changed_blocks_size = 0
    n = 0
    for (offset, length) in extents:
        n += 1
        changed_blocks_size += length
        max_length = length if max_length is None else max(max_length, length)
        min_length = length if min_length is None else min(min_length, length)
    average_length = None if n == 0 else (changed_blocks_size / n)
    return { 'average_extent_length': average_length,
             'max_extent_length': max_length,
             'min_extent_length': min_length,
             'changed_blocks_size': changed_blocks_size,
             'extents': n }

class CbtBitmap(object):
    """
    Wraps a base64-encoded CBT bitmap, as returned by
    VDI.list_changed_blocks, and provides methods for extracting various
    data from the bitmap.
    """
    def __init__(self, cbt_bitmap_b64):
        """
        Decodes the given base64-encoded CBT bitmap.
        """
        self.bitmap = base64.b64decode(cbt_bitmap_b64)

    def get_extents(self):
        """
        Returns an iterator containing the increasingly ordered sequence
        of the non-overlapping extents corresponding to this bitmap.
        """
        extents = _bitmap_to_extents(self.bitmap)
        return extents

    def get_statistics(self):
        """
        Return the size of the disk, and the total size of the changed
        blocks in a dictionary.
        """
        stats = _get_extent_stats(self.get_extents())
        stats["size"] = _get_disk_size(self.bitmap)
        return stats
