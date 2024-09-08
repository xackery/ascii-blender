import time, io

import parse.wce as wce

def test_wce_paunrse():
    e = wce.wce()
    path = "../quail/test/globalelf_chr/_root.wce"
    file_reader = open(path, "r")
    data = file_reader.read()
    r = io.StringIO(data)
    e.parse_definitions(path, r)
    print("Done")
