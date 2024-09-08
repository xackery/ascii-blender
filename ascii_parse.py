import io, shlex

def parse_property(r:io.TextIOWrapper=None, property:str="", num_args:int=-1) -> list[str]:
    if r is None:
        raise Exception("reader is none")
    if property == "":
        raise Exception("empty property")
    for line in r:
        if line.find("//"):
            line = line.split("//")[0]
        line = line.strip()
        if line == "":
            continue
        records = shlex.split(line)
        if len(records) == 0:
            raise Exception("%s: empty records (%s)" % (property, line))
        if records[0] != property:
            raise Exception("%s: expected property %s got %s" % (property, property, records[0]))
        if num_args != -1 and len(records)-1 != num_args:
            raise Exception("%s: expected %d arguments, got %d" % (property, len(records)-1, num_args))
        return records
