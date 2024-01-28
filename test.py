    
class Database(dict):
  # def __init__(self, *args):
  #   UserDict.__init__(self, args)
  
  def __init__(self,*arg,**kw):
    super(Database, self).__init__(*arg, **kw)
    print('init!!!')

  def __setitem__(self, item, value):
    print("You are changing the value of %s to %s!!", item, value)
    super(Database, self).__setitem__(item, value)

  # def __init__(self, *args, **kwargs):
  #     self.update(*args, **kwargs)

  # def __getitem__(self, key):
  #     val = dict.__getitem__(self, key)
  #     print('GET', key)
  #     return val

  # def __setitem__(self, key, val):
  #     print('SET', key, val)
  #     dict.__setitem__(self, key, val)

  # def __repr__(self):
  #     dictrepr = dict.__repr__(self)
  #     return '%s(%s)' % (type(self).__name__, dictrepr)
      
  # def update(self, *args, **kwargs):
  #     print('update', args, kwargs)
  #     for k, v in dict(*args, **kwargs).items():
  #         self[k] = v
    

global d
d = Database({
  'foo': 'bar'
})


def some_func():
  d['baz'] = 'wow'
  print(d)

some_func()