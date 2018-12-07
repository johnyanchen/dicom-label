import struct, scipy
from scipy import misc
from math import sqrt

def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())

def read_NIM_CT_data(fname, PRJ=True):
    fp = open(fname, 'rb')
    data = fp.read()
    fp.close()
    # where to find the matrix width/height
    w, h = struct.unpack("<II", data[-3 * 4:-1 * 4])
    # determine the data type
    if PRJ:
        fmt = "<" + "I" * (w * h)
    else:
        fmt = "<" + "f" * (w * h)
    data_matrix = scipy.array(struct.unpack(fmt, data[:-512]))
    data_matrix.shape = (h, w)
    return data_matrix


def Pos2Lineseg(p, a, b):
    ap = p - a
    ab = b -a
    if dot(ap, ab)<=0:
        return distance(ap)
    if dot(ap, ab)>=distance(ab)*distance(ab):
        return distance(ab)
    return dot(ap, ab) / distance(ab)

def dot(a, b):
    return a.x()*b.x() + a.y()*b.y()

def isPosInPolygon(p, shape):
    x = [point.x() for point in shape.points]
    y = [point.y() for point in shape.points]
    if p.x()<min(x) or p.x()>max(x) or p.y()<min(y) or p.y()>max(y):
        return False
    a = False
    i = 0
    j = len(shape)-1
    while(i<len(shape)):
        if (shape[j].y()>p.y()) != (shape[i].y()>p.y()) and  \
                (shape[i].x()-shape[j].x())*(p.y()-shape[j].y())/(shape[i].y()-shape[j].y())+shape[j].x()>p.x():
            a = not a
        j, i = i, i+1
    return a






