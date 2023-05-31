from numba import jit


class MyClass:
    def __init__(self):
        self.k = 1

    def calculation(self):
        k = self.k
        return self.complicated([1, 2, 3], k)

    @staticmethod
    @jit(nopython=True)
    def complicated(x, k):
        res = []
        for a in x:
            res.append(a**2. + a**3. + k)
        return res


myclass = MyClass()
print(myclass.calculation())
