class Provider(object):
    name = u'RGB color space'

    def __getitem__(self, face):
        return tuple([(c + 1)/2.0 for c in face])
