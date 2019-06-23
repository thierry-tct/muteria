
class Lib(object):
    def __init__(self):
        pass
    def compute(self, a, b):
        """
        Example:
        >>> l = Lib()
        >>> l.compute(1, 2)
        3
        """
        oddtotal = self.get_odd_total(a,b)
        eventotal = self.get_even_total(a,b)
        if oddtotal < -100000:
            oddtotal = 0
        return oddtotal + eventotal

    def get_even_total(self, a, b):
        t = 0
        for v in (a,b):
            if v % 2 == 0:
                t += v
        return t

    def get_odd_total(self, a, b):
        t = 0
        if a % 2 != 0:
            t += a
        if b % 2 != 0:
            t += b
        return t
