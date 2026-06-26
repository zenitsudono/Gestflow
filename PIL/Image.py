# Dummy PIL Image module for mocking
class Image:
    @staticmethod
    def open(*args, **kwargs):
        return Image()
    
    def save(self, *args, **kwargs):
        pass
        
    def resize(self, *args, **kwargs):
        return self
