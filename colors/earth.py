from math import atan2, pi, sqrt
from os.path import dirname, realpath

from numpy import memmap

class Provider(object):
    name = u'Earth elevation'

    file = dirname(realpath(__file__)) + '/etopo.bin'
    dtype = 'float32'
    res = 60 # 1 arc-minute
    lats = 180 * res + 1
    lons = 360 * res + 1

    def __init__(self):
        self.data = memmap(self.file, self.dtype, mode='r')

    def __del__(self):
        del self.data

    @staticmethod
    def _color(elevation):
        snowline = 4500.0
        oversnow = elevation - snowline
        if oversnow >= 0:
            value = oversnow/(8500.0 - snowline)/2 + 0.5
            return (value, value, value)
        if elevation >= 0:
            value = elevation/snowline/2 + 0.5
            return (0, value, 0)
        value = elevation/11000.0/2 + 0.5
        return (0, 0, value)

    def __getitem__(self, face):
        x, z, y = face
        lat = atan2(z, sqrt(x*x + y*y)) * 180/pi
        lon = atan2(y, x) * 180/pi
        index = int(lat * self.res + self.lats/2) * self.lons + int(lon * self.res + self.lons/2)
        elevation = self.data[index]
        return self.__class__._color(elevation)

    # compile ETOPO xyz file, like:
    #
    #   lat, lon, elevation
    #
    # to a file with a flat array of binary floats
    #
    # input file is ordered by latitude, 90 to -90, with latitudes -180 to 180
    # for each latitude
    @classmethod
    def compile(cls, xyzfile):
        hs = []
        with open(xyzfile, 'r') as f:
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                _, _, h = line.split()
                hs.append(float(h))

        m = memmap(cls.file, dtype=cls.dtype, mode='w+', shape=(len(hs),))
        m[:] = hs[:]
        del m
