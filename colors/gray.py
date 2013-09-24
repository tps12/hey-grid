class Provider(object):
    name = u'Grayscale gradient'

    def __getitem__(self, face):
        return tuple(3 * [0.5 + sum(face)/6.0])
