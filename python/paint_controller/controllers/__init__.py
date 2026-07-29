"""Controller package — device I/O adapters (TD-055).

Deliberately avoids package-level re-exports so importing one controller does
not drag the full ROS/PySide controller graph into memory.

Role: ROS/UDP/SSH pubs and status only. Must **not** take UI popup callbacks,
peer-device orchestration, or demo sequences (those belong in handlers /
``demo_sequence`` / *Actions).
"""
