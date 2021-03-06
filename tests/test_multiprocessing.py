import dill
import math
import logging
import multiprocessing
from concurrent import futures
from pysparkling import Context


def test_multiprocessing():
    p = multiprocessing.Pool(4)
    c = Context(pool=p, serializer=dill.dumps, deserializer=dill.loads)
    my_rdd = c.parallelize([1, 3, 4])
    r = my_rdd.map(lambda x: x*x).collect()
    print(r)
    assert 16 in r


def test_concurrent():
    with futures.ThreadPoolExecutor(4) as p:
        my_rdd = Context(pool=p).parallelize([1, 3, 4])
        r = my_rdd.map(math.sqrt).collect()
        print(r)
        assert 2 in r


def test_first_mp():
    p = multiprocessing.Pool(4)
    c = Context(pool=p, serializer=dill.dumps, deserializer=dill.loads)
    my_rdd = c.parallelize([1, 2, 2, 4, 1, 3, 5, 9], 3)
    print(my_rdd.first())
    assert my_rdd.first() == 1


INDENT_WAS_EXECUTED = False


def indent_line(l):
    global INDENT_WAS_EXECUTED
    INDENT_WAS_EXECUTED = True
    return '--- '+l


def test_lazy_execution():
    r = Context().textFile('tests/test_multiprocessing.py')
    r = r.map(indent_line)
    exec_before_collect = INDENT_WAS_EXECUTED
    # at this point, no map() or foreach() should have been executed
    r.collect()
    exec_after_collect = INDENT_WAS_EXECUTED
    assert not exec_before_collect and exec_after_collect


def test_lazy_execution_threadpool():
    with futures.ThreadPoolExecutor(4) as p:
        r = Context(pool=p).textFile('tests/test_multiprocessing.py')
        r = r.map(indent_line)
        r = r.map(indent_line)
        r = r.collect()
        # ThreadPool is not lazy although it returns generators.
        print(r)
        assert '--- --- from pysparkling import Context' in r


def test_lazy_execution_processpool():
    with futures.ProcessPoolExecutor(4) as p:
        r = Context(
            pool=p,
            serializer=dill.dumps,
            deserializer=dill.loads,
        ).textFile('tests/test_multiprocessing.py')
        r = r.map(indent_line).cache()
        r.collect()
        r = r.map(indent_line)
        r = r.collect()
        # ProcessPool is not lazy although it returns generators.
        print(r)
        assert '--- --- from pysparkling import Context' in r


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_lazy_execution_processpool()
