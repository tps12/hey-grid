from noise._simplex import noise3

class Provider(object):
    name = u'Simplex noise'

    def __getitem__(self, face):
        x, y, z = face
        elevation = noise3(x, y, z, 8, 0.75, 10)
        snowline = 0.5
        oversnow = elevation - snowline
        if oversnow >= 0:
            value = oversnow/(1.0 - snowline)/2 + 0.5
            return (value, value, value)
        if elevation >= 0:
            value = elevation/snowline/2 + 0.5
            return (0, value, 0)
        value = elevation/2 + 0.5
        return (0, 0, value)
