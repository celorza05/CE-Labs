"""Cutter — turns clip timestamps into finished vertical clips with ffmpeg.

Reads the Clipper's ``data/clips/clips.json`` plus the source media, and for each
clip: cuts the segment, reframes to vertical 9:16, and burns in captions from the
transcript. Outputs ``data/clips/out/<clip>.mp4`` for the Publisher.

Needs ``ffmpeg`` on PATH.
"""
