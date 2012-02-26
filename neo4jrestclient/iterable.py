# -*- coding: utf-8 -*-


class Iterable(list):
    """
    Class to iterate among returned objects.
    """

    def __init__(self, cls, lst, attr=None):
        self._list = lst
        self._index = len(lst)
        self._class = cls
        self._attribute = attr
        super(Iterable, self).__init__(lst)

    def __getslice__(self, *args, **kwargs):
        eltos = super(Iterable, self).__getslice__(*args, **kwargs)
        if self._attribute:
            return [self._class(elto[self._attribute], update_dict=elto)
                                for elto in eltos]
        else:
            return [self._class(elto) for elto in eltos]

    def __getitem__(self, index):
        elto = super(Iterable, self).__getitem__(index)
        if self._attribute:
            return self._class(elto[self._attribute], update_dict=elto)
        else:
            return self._class(elto)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__,
                                    self._class.__name__)

    def __contains__(self, value):
        # TODO: Find a better way to check if value is instance of Base
        #       avoiding a circualr loop of imports
        # if isinstance(value, Base) and hasattr(value, "url"):
        if (hasattr(value, "url") and hasattr(value, "id")
            and hasattr(value, "_dic")):
            if self._attribute:
                return value.url in [elto[self._attribute]
                                     for elto in self._list]
            else:
                return value.url in self._list
        return False

    def __iter__(self):
        return self

    @property
    def single(self):
        try:
            return self[0]
        except KeyError:
            return None

    def next(self):
        if self._index == 0:
            raise StopIteration
        self._index = self._index - 1
        return self.__getitem__(self._index)
