from gevent import queue, wait
import gevent


def sleepy(time, queue):
    num = 2
    while True:
        print("done like a good script")
        num_str = "Ok-" + str(num)
        queue.put(num_str)
        num += 2
        gevent.sleep(time)

if __name__ == '__main__':
    q = queue.Queue()
    g = gevent.spawn(sleepy,3, q)
    g.start()
    # g.join()
    print(g.started)
    print(g.ready())
    ok_num = q.get(block=True, timeout=2)
    # gevent.kill(g)
    g.kill()
    print(g.dead)
    print(ok_num)
    # print("if this is the only log line, then join didn't work")