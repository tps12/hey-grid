from unittest import TestCase

from sparselist import splist

class SparseListTest(TestCase):
	def test_constructor(self):
		splist()

	def test_list_constructor(self):
		splist([1,2,3])

	def test_set_constructor(self):
		splist({'a',2,'iii'})

	def test_string_constructor(self):
		splist('hello')

	def test_iterator(self):
		self.assertEqual([1,2,3], [item for item in splist([1,2,3])])

	def test_randomget(self):
		self.assertEqual('b', splist('abc')[1])

	def test_randomset(self):
		l = splist('abc')
		l[1] = 5
		self.assertEqual(5, l[1])

	def test_iterateafterrandomset(self):
		l = splist('abc')
		l[1] = 5
		self.assertEqual(['a',5,'c'], [item for item in l])

	def test_default(self):
		self.assertIsNone(splist([])[3])

	def test_setoutofrange(self):
		l = splist()
		l[1] = 5
		self.assertEqual(5, l[1])

	def test_addatend(self):
		l = splist(['a','b'])
		l[2] = 'c'
		self.assertEqual(['a','b','c'], [item for item in l])

	def test_insertinorder(self):
		l = splist()
		l[0] = 'a'
		l[1] = 'b'
		l[2] = 'c'
		self.assertEqual(['a','b','c'], [item for item in l])

	def test_insertoutoforder(self):
		l = splist()
		l[2] = 'c'
		l[1] = 'b'
		l[0] = 'a'
		self.assertEqual(['a','b','c'], [item for item in l])

	def test_memoryusage(self):
		from sys import getsizeof
		def usage(obj):
			#return sum([getsizeof(v) for v in obj.__dict__.itervalues()])
			try:
				return sum([usage(v) for v in obj.__dict__.itervalues()])
			except AttributeError:
				return getsizeof(obj)

		# sanity check
		self.assertGreater(usage(splist([1,2,3])), usage(splist()))

		# sparseness shouldn't affect the size
		l1, l2 = [splist() for _ in range(2)]
		l1[100] = 17
		l2[100000] = 17
		self.assertEqual(usage(l1), usage(l2))
