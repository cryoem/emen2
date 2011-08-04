import contextlib

class RegisteredObj(object):
	def __init__(self, name, *args):
		self.name = name

def make_ctxt_manager():
	@contextlib.contextmanager
	def _inner(self, name, *args):
		obj = self.registry.get(name) if name in self.registry else self.child_class(name, *args)
		yield obj
		if obj.name not in self.registry:
			self.register(obj)
	return _inner

class Registry(object):
	registry = {}
	child_class = None

	@staticmethod
	def setUp(cls):
		setattr(cls, cls.child_class.__name__.lower(), make_ctxt_manager())
		return cls

	def register(self, obj):
		self.registry[obj.name] = obj
		return obj

class DataObj(RegisteredObj):
	def __init__(self, name, a):
		RegisteredObj.__init__(self, name)
		self.a = a
		self.b = None
		self.c = None

@Registry.setUp
class DataObjRegistry(Registry):
	child_class = DataObj

if __name__ == '__main__':
	#Demo code

	registry = DataObjRegistry()
	with registry.dataobj('first_obj', 1) as obj1:
		obj1.b = 2

	with registry.dataobj('second_obj', 2) as obj2:
		obj2.b = 3
		obj2.c = 4

	with registry.dataobj('third_obj', 3) as obj3:
		obj1.b = 4

	import random
	def shuffled(lis):
		lis = lis[:]
		random.shuffle(lis)
		return iter(lis)


	for obj_name in shuffled(['first_obj', 'second_obj', 'third_obj']):
		with registry.dataobj(obj_name) as obj:
			print '%s - a: %s, b: %s, c: %s' % (obj.name, obj.a, obj.b, obj.c)
