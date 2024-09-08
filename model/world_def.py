import io
from ascii_parse import parse_property

# WORLDDEF
# 	NEWWORLD 0
# 	ZONE 0
# 	EQGVERSION? NULL

class world_def:
    new_world:int
    zone:int
    eqg_version:tuple[int, None]

    def __init__(self, r:io.TextIOWrapper):
        records = parse_property(r, "NEWWORLD", 1)
        self.new_world = int(records[1])
        records = parse_property(r, "ZONE", 1)
        self.zone = int(records[1])
        records = parse_property(r, "EQGVERSION?", 1)
        self.eqg_version = (int(records[1]) if records[1] != "NULL" else None)





