import struct
import sys

def getBytes(fs, pos, numBytes):
  fs.seek(pos)
  byte = fs.read(numBytes)
  if (numBytes == 2):
    formatString = "H"
  elif (numBytes == 1):
    formatString = "B"
  elif (numBytes == 4):
    formatString = "i"
  else:
    raise Exception("Not implemented")
  return struct.unpack("<"+formatString, byte)[0]

def getString(fs, pos, numBytes):
  fs.seek(pos)
  raw = fs.read(numBytes)
  return struct.unpack(str(numBytes)+"s", raw)[0]

def bytesPerSector(fs):
  return getBytes(fs,11,2)

def sectorsPerCluster(fs):
  return getBytes(fs,13,1)

def reservedSectorCount(fs):
  return getBytes(fs,14,2)

def numberOfFATs(fs):
  return getBytes(fs,16,1)

def rootEntCount(fs):
  return getBytes(fs,17,2)

def FATStart(fs, numFat):
  return reservedSectorCount(fs) * bytesPerSector(fs)

def TotSec32(fs):
  return getBytes(fs, 32, 4)

def FATSize(fs):
  return getBytes(fs, 36, 4)

def rootStart(fs):
  return FATStart(fs,1) + (FATSize(fs) * numberOfFATs(fs) * bytesPerSector(fs))

def countOfClusters(fs):
    resvd_sec_cnt = reservedSectorCount(fs)
    num_fats = numberOfFATs(fs)
    fat_sz = FATSize(fs)
    tot_sec = TotSec32(fs)
    bytes_per_sec = bytesPerSector(fs)

    root_dir_sectors = ((rootEntCount(fs) * 32) + (bytes_per_sec - 1)) / bytes_per_sec

    data_sec = tot_sec - (resvd_sec_cnt + (num_fats * fat_sz) + root_dir_sectors)

    return int(data_sec / sectorsPerCluster(fs))

def getDirTableEntry(fs):
    offset = rootStart(fs)
    fs.seek(offset)
    while True:
        try:
            entry = DirEntry(fs.read(32))
            yield entry
        except InvalidDirEntryException:
            pass

def ppNum(num):
  return "%s (%s)" % (hex(num), num)

def parseFATTable(fs):
    # First cluster is #2
    offset = FATStart(fs, numberOfFATs(fs)) + 8

    max_cluster_num = countOfClusters(fs)
    fat_size = FATSize(fs)

    print("MAX = {}".format(max_cluster_num))

    clusters = []
    for i in range(2, max_cluster_num):
        fat_entry = getBytes(fs, offset, 4)

        if fat_entry == 0x0:
            print("{}: EMPTY".format(i))
        elif fat_entry >= 0x2 and fat_entry <= max_cluster_num:
            print("{}: Next cluster is {}".format(i, fat_entry))
        elif fat_entry >= max_cluster_num and fat_entry <= 0xFFFFFF6:
            pass
            #print("{}: Reserved".format(i))
        elif fat_entry == 0xFFFFFF7:
            pass
            #print("{}: DEFECTIVE".format(i))
        elif fat_entry >= 0xFFFFFF8 and fat_entry <= 0xFFFFFFE:
            pass
            #print("{}: Reserved".format(i))
        elif fat_entry == 0xFFFFFFFF:
            print("{}: FINAL CLUSTER".format(i))
            break

        offset += 4


def getSector(fs, sector_num):
    sector_size = bytesPerSector(fs)
    root = rootStart(fs)

    fs.seek(root + (sector_size * sector_num))
    return fs.read(sector_size)

class InvalidDirEntryException(Exception):
    pass

class Sector(object):
    def __init__(self, fs, sector_num):
        self.data = getSector(fs, sector_num)

        self.entries = []
        for offset in range(0, len(self.data), 32):
            try:
                self.entries.append(DirEntry(self.data[offset:offset+32]))
            except InvalidDirEntryException:
                self.entries.append(None)

class DirEntry(object):
    def __init__(self, dir_entry):
        dir_entry = bytes(dir_entry)
        self.dir_entry = dir_entry

        self.name = struct.unpack("11s", dir_entry[:11])[0].strip()
        self.ntres = dir_entry[12]

        if self.name[0] == 0 or self.ntres != 0:
            raise InvalidDirEntryException()

        self.attr = dir_entry[11]
        self.fst_clus_lo = struct.unpack("H", dir_entry[26:28])[0]

    @property
    def is_directory(self):
        return self.attr & 0x10

    def __repr__(self):
        if self.is_directory:
            return "<DIR: {}>".format(self.name.decode("utf-8"))
        else:
            return "<FILE: {}>".format(self.name.decode("utf-8"))

    def __hash__(self):
        return hash(self.dir_entry)

def sectors_containing_offset(secs, lo):
    results = []
    lo += 2
    for num, sec in enumerate(secs):
        for entry in sec.entries:
            if entry is not None and entry.fst_clus_lo == lo:
                results.append((num, entry))
    return results

def sectors_containing_filename(secs, filename):
    results = []
    for num, sec in enumerate(secs):
        for entry in sec.entries:
            if entry is not None and entry.name == filename:
                results.append((num, entry))
    return results

def find_dir_start(secs, sec_num, entry):
    current_start = sec_num
    seen_entry = False

    # Check if it's the current section
    for sec_entry in secs[sec_num].entries:
        if entry in secs[sec_num].entries and sec_entry is None and not seen_entry:
            return sec_num
        elif sec_entry is entry:
            seen_entry = True

    # Go back until we hit a section will None in
    while True:
        sec_num -= 1
        if None in secs[sec_num].entries:
            if secs[sec_num].entries[-1] is None:
                sec_num += 1
            return sec_num

def find_dirs_containing_entry(secs, filename):
    sectors = []
    for sec_num, entry in sectors_containing_filename(secs, filename):
        sectors.append((find_dir_start(secs, sec_num, entry), entry))
    return sectors

def find_dirs_containing_link(secs, offset):
    sectors = []
    for sec_num, entry in sectors_containing_offset(secs, offset):
        sectors.append((find_dir_start(secs, sec_num, entry), entry))
    return sectors

def go_deeper(secs, offset, entry, stem):
    for offset, entry in find_dirs_containing_link(secs, offset):
        current = "{}{}".format(entry.name.decode("utf-8"), stem)
        print(current)
        if current.lower().startswith("pctf"):
            return True

        if go_deeper(secs, offset, entry, current):
            return True

def tryit():
    fs = open("strcmp.fat32", "rb")
    secs = [Sector(fs, i) for i in range(1842)]

    final = find_dirs_containing_entry(secs, b"MATCH")

    for offset, entry in final:
        if go_deeper(secs, offset, entry, ""):
            break

if __name__ == "__main__":
    tryit()
