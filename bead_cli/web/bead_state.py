from enum import Enum


class BeadState(Enum):
    PHANTOM = 0,
    # (red) unknown bead
    SUPERSEDED = 1,
    # (grey) not latest in cluster
    UP_TO_DATE = 2,
    # (green) latest and all its inputs are also referencing an UP_TO_DATE
    OUT_OF_DATE = 3,
    # (yellow) latest in cluster, but needs updating, because of newer input version
