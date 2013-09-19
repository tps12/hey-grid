class Provider(object):
    def __getitem__(self, face):
        return tuple([(c + 1)/2.0 for c in face])
