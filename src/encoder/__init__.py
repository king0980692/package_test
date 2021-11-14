class label_encoder:
    def __init__(self, offset=0, shared=False):
        self.share_idx = shared
        self.idx = offset
        self.data = None

    def _unique(self):
        self.data = set(self.data)

    def _map_to_int(self):
        # if shared_idx flag is opened, those unseen label will be encoded the same id as "null"
        if self.share_idx == True:
            self.data.add('null')

        # make sure every time the encode is unique
        self.data = sorted(self.data)

        self.table = {val: i + self.idx for i, val in enumerate(self.data)}

        self.inverse_table = {val: i for i, val in self.table.items()}
        #return [table[v] for v in values]

    def _encode(self):
        return self._map_to_int()

    def fit(self, data, offset=0):
        if self.idx == None:
            self.idx =offset
        self.data = data
        self._encode()
        return self

    def transform(self, key):
        if self.data is None:
            raise

        if isinstance(key, list):
            output = []
            for k in key:
                if k in self.table:
                    output.append(self.table[k])
                else:
                    if self.share_idx:
                        output.append(self.table['null'])
                    else:
                        raise
            
            return output
        else:
            if key in self.table:
                return self.table[key]
            else:
                if self.share_idx:
                  return self.table['null']
                else:
                  raise


class num_encoder:
    def __init__(self, offset=0):
        self.idx = offset
        self.data = None

    def _map_to_int(self):
        self.table = {val: i + self.idx for i, val in enumerate(self.data)}

        self.inverse_table = {val: i for i, val in self.table.items()}
        #return [table[v] for v in values]        
        
    def _encode(self):
        return self._map_to_int()
    
    def fit(self, data, offset=0):
      self.idx =offset
      self.data = data
      self._encode()
      return self

    def transform(self, key):
      if self.data is None:
          raise
      if isinstance(key, list):
          output = []
          for k in key:
              if k in self.table:
                  output.append(self.table[k])
              else:
                  raise
          
          return output
      else:
          if key in self.table:
              return self.table[key]
          else:
              return self.table['null']
      