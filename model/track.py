import io
from ascii_parse import parse_property


# TRACKINSTANCE "C01AELFC01A_ELF_TRACK"
# 	TAGINDEX 0
# 	SPRITE "ELF_DMSPRITEDEF"
# 	DEFINITION "C01AELFC01A_ELF_TRACKDEF"
# 	DEFINITIONINDEX 0
# 	INTERPOLATE 0
# 	REVERSE 0
# 	SLEEP? NULL

class track:
    tag:str
    tag_index:int
    sprite:str
    definition:str
    definition_index:int
    interpolate:int
    reverse:int
    sleep: tuple[str, None]

    def __init__(self, tag:str, r:io.TextIOWrapper):
        self.tag = tag
        records = parse_property(r, "TAGINDEX", 1)
        self.tag_index = int(records[1])
        records = parse_property(r, "SPRITE", 1)
        self.sprite = records[1]
        records = parse_property(r, "DEFINITION", 1)
        self.definition = records[1]
        records = parse_property(r, "DEFINITIONINDEX", 1)
        self.definition_index = int(records[1])
        records = parse_property(r, "INTERPOLATE", 1)
        self.interpolate = int(records[1])
        records = parse_property(r, "REVERSE", 1)
        self.reverse = int(records[1])
        records = parse_property(r, "SLEEP?", 1)
        self.sleep = (records[1] if records[1] != "NULL" else None)

