##
# Class implementing a sparse list optimized for iteration and random-access
#
# Insertions are linear in complexity
class splist(object):
	def __init__(self, items=None):
		self._head, self._index = None, {}
		items = [] if items is None else items
		for (i, value) in zip(range(len(items)), items):
			self[i] = value

	def __iter__(self):
		item = self._head
		while item is not None:
			yield item.value
			item = item.next

	def __getitem__(self, i):
		return self._index[i].value if i in self._index else None

	@staticmethod
	def _insert(list, index, i, value):
		if list is not None and list.i < i:
			next, index = splist._insert(list.next, index, i, value)
			return splist.Entry(list.i, list.value, next), index
		else:
			next = list.next if list is not None and list.i == i else list
			entry = splist.Entry(i, value, next)
			return entry, dict(index.items() + { i: entry }.items())

	def __setitem__(self, i, value):
		self._head, self._index = self._insert(self._head, self._index, i, value)

	class Entry(object):
		def __init__(self, i, value, next=None):
			self.i = i
			self.value = value
			self.next = next
