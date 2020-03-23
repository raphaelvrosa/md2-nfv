import logging
import random
from datetime import datetime, timedelta
from collections import deque, namedtuple

logger = logging.getLogger(__name__)

from exchange.common.content import Content

MESSAGE_IDS = 900

class Time(Content):
    def __init__(self):
        Content.__init__(self)
        self.timestamp = self.when_to_str(datetime.now())
        self.when = None
        self.duration = None
        self.repeat = 0
        self.every = 0
        self._keys = ['timestamp']

    def past_now(self, when):
        t_now = datetime.now()
        t = datetime.strptime(when, '%a, %d %b %Y %H:%M:%S')
        return t_now >= t

    def when_to_str(self, when):
        if isinstance(when, datetime):
            self.when = when.strftime("%a, %d %b %Y %H:%M:%S")
            return self.when
        return None

    def when_from_str(self, when):
        if isinstance(when, str):
            self.when = datetime.strptime(when, '%a, %d %b %Y %H:%M:%S')
            return self.when
        return None

    def now_after(self, hours=None, mins=None, secs=None):
        t_now = datetime.now()
        diff = timedelta(hours=hours, minutes=mins, seconds=secs)
        ahead = t_now + diff
        return ahead


class Message(Content):
    def __init__(self, id=None, type='external', event=None, from_address=None, params=None,
                 to_address=None, prefix=None, call=None, data='',
                 reply=False):
        Content.__init__(self)
        self.id = self.create_msg_id() if not id else id
        self.type = type
        self.time = Time().items(filter_keys=True)
        self.event = event
        self.params = params if params else {}
        self.from_address = from_address
        self.to_address = to_address
        self.prefix = prefix
        self.call = call
        self.data = data
        self._reply = reply
        self.wait_reply = False

    def get_id(self):
        return self.id

    def reply(self):
        return self._reply

    def create_msg_id(self):
        global MESSAGE_IDS
        _id = random.randint(1, random.randint(100, 10000))
        return str(_id)
        # _id = MESSAGE_IDS
        # MESSAGE_IDS += 1
        # return str(_id)

    def wait_reply(self):
        return self.wait_reply


class Tasks:
    def __init__(self):
        self.queue = deque()
        self.waiting = {}
        self.tasks_tree = {}
        self.finished = {}

    def enqueue(self, entrypoint, tasks):
        entry_id = entrypoint.get('id')
        if entry_id not in self.tasks_tree:
            self.queue.append(entry_id)
            self.waiting[entry_id] = deque()
            self.tasks_tree[entry_id] = deque()
            self.finished[entry_id] = {}
            for task in tasks:
                (prefix, output) = task
                self.waiting[entry_id].append(task)
                self.tasks_tree[entry_id].append(output.get('id'))

    def get_next(self, entry_id, finished_task):
        if entry_id in self.tasks_tree:
            task_id = finished_task.get('id')
            if task_id in self.tasks_tree[entry_id]:
                self.finished[entry_id][task_id] = finished_task
                index_task = list(self.tasks_tree[entry_id]).index(task_id)
                if index_task <= len(self.tasks_tree[entry_id]):
                    next_index = index_task + 1
                    next_task = self.waiting[entry_id][next_index]
                    return next_task
        return None

    def is_finished(self, entry_id):
        if entry_id in self.tasks_tree:
            waiting_ids = self.tasks_tree[entry_id]
            finished_ids = self.finished[entry_id].keys()
            acks = all([ True if task_id in finished_ids else False for task_id in waiting_ids ])
            return acks
        return True

    def clear_batch(self, entry_id):
        if entry_id in self.tasks_tree:
            self.queue.remove(entry_id)
            del self.waiting[entry_id]
            del self.tasks_tree[entry_id]

    def has_entry(self, entrypoint_id):
        if entrypoint_id in self.tasks_tree:
            return True
        return False


class Mailing(Tasks):
    def __init__(self):
        Tasks.__init__(self)
        self.msg = namedtuple('msg', 'prefix data waiting ack')
        self.msgs = {}

    def create_msg(self, prefix):
        msg = self.msg(prefix=prefix, data={}, waiting={}, ack={})
        return msg

    def add_recvd(self, data, prefix):
        _id = data.get_id()
        msg = self.create_msg(prefix)
        msg.data[_id] = data
        self.msgs[_id] = msg

    def add_ack(self, data, prefix):
        msg_id = self.get_ack_id(data, prefix)
        data_id = data.get_id()
        if msg_id:
            msg = self.msgs[msg_id]
            msg.ack[(prefix, data_id)] = data
            self.msgs[msg_id] = msg
            logger.debug('msg %s added ack %s', msg_id, data_id)
            return True
        # logger.debug('msg %s NOT added ack', data_id)
        return False

    def add_waiting(self, msg_id, data, prefix):
        data_id = data.get_id()
        if msg_id in self.msgs:
            msg = self.msgs[msg_id]
            msg.waiting[(prefix, data_id)] = data
            self.msgs[msg_id] = msg
            logger.debug('msg %s added waiting %s', msg_id, data_id)
            return True
        # logger.debug('msg %s NOT added waiting', data_id)
        return False

    def get_ack_id(self, data, prefix):
        data_id = data.get_id()
        for msg_id in self.msgs.keys():
            msg = self.msgs[msg_id]
            if (prefix, data_id) in msg.waiting.keys():
                # logger.debug('msg_id %s is in waiting of msg', msg_id)
                return msg_id
        # logger.debug('msg_id %s is NOT in waiting of any msg', data.get_id())
        return None

    def check(self, msg_id):
        if msg_id in self.msgs.keys():
            msg = self.msgs[msg_id]
            sents = msg.waiting.keys()
            recvds = msg.ack.keys()
            if len(sents) == len(recvds):
                # sents.sort()
                # recvds.sort()
                # ids = zip(sents, recvds)
                sort_sents = sorted(sents)
                sort_recvds = sorted(recvds)
                ids = zip(sort_sents, sort_recvds)
                return all([True if _id[0] == _id[-1] else False for _id in ids])
        return False

    def get_acks(self, data, prefix):
        msg_id = self.get_ack_id(data, prefix)
        if msg_id:
            # logger.debug('msg %s has ack waiting', msg_id)
            if self.check(msg_id):
                logger.debug('msg %s has all acks == waiting', msg_id)
                msg = self.msgs[msg_id]
                acks = msg.ack.values()
                msg_data = msg.data[msg_id]
                acks_list = list(acks)
                return msg_data, acks_list
            else:
                pass
                logger.debug('msg %s does not have all acks == waiting', msg_id)
        return None

    def acks(self, data, prefix):
        msg_id = self.get_ack_id(data, prefix)
        if msg_id:
            msg = self.msgs[msg_id]
            acks = msg.ack.keys()
            waitings = msg.waiting.keys()
            return (waitings, acks)
        return []

    def get_prefix(self, msg_id):
        if msg_id in self.msgs.keys():
            msg = self.msgs[msg_id]
            return msg.prefix
        return None

    def clear_recvd(self, data):
        data_id = data.get_id()
        if data_id in self.msgs.keys():
            del self.msgs[data_id]

    def input(self, msg):
        logger.debug("input_mail")
        prefix = msg.get('prefix')
        acks = False
        if msg.reply():
            # logger.debug("add_ack %s", msg.get_id())
            self.add_ack(msg, prefix)
            # logger.debug("acks so far %s", self.acks(msg, prefix))
            if self.get_acks(msg, prefix):
                acks = True
        else:
            # logger.debug("add_recvd %s", msg.get_id())
            self.add_recvd(msg, prefix)
        return acks

    def get_reply(self, msg):
        prefix = msg.get('prefix')
        entrypoint_id = self.get_ack_id(msg, prefix)
        acks = self.get_acks(msg, prefix)
        self.clear_batch(entrypoint_id)
        return acks

    def output(self, msg, outputs, model='parallel'):
        logger.debug("output_mail")
        entry_id = msg.get('id')
        if not self.has_entry(entry_id):
            if model is 'parallel':
                dispatches = self.out_parallel(msg, outputs)
            elif model is 'serial':
                dispatches = self.out_serial(msg, outputs)
            else:
                dispatches = []
                logger.debug("unkown outputs model %s", model)
        else:
            dispatches = outputs
        return dispatches

    def out_parallel(self, msg, outputs):
        dispatches = []
        msg_id = msg.get('id')
        for output_pack in outputs:
            (prefix, output) = output_pack
            reply = output.reply()
            if reply:
                # output.set('id', msg_id)
                msg_prefix = self.get_prefix(output.get_id())
                logger.debug("out_parallel clear_recvd %s - output reply %s", msg_id, output.get_id())
                self.clear_recvd(msg)
                dispatches.append(output)
            else:
                logger.debug("out_parallel add_waiting %s - output %s", msg_id, output.get_id())
                self.add_waiting(msg_id, output, prefix)
                dispatches.append(output)
        return dispatches

    def out_serial(self, msg, outputs):
        dispatches = []
        messages = outputs.get('messages')
        reply = outputs.get('reply')
        messages.reverse()
        for output_pack in messages:
            (prefix, output) = output_pack
            if reply:
                self.clear_recvd(output)
            else:
                msg_id = msg.get_id()
                self.add_waiting(msg_id, output, prefix)
        output_initial = messages[0]
        (prefix_initial, output_initial) = output_initial
        dispatches.append((prefix_initial, output_initial))
        self.enqueue(msg, messages)
        return dispatches

    def has_next(self, msg):
        prefix = msg.get('prefix')
        entrypoint_id = self.get_ack_id(msg, prefix)
        if self.has_entry(entrypoint_id):
            if not self.is_finished(entrypoint_id):
                return True
        return False

    def get_next_outputs(self, msg):
        outputs = []
        prefix = msg.get('prefix')
        entrypoint_id = self.get_ack_id(msg, prefix)
        next_msg = self.get_next(entrypoint_id, msg)
        msg.set('id', entrypoint_id)
        # logger.info('next_msg %s', next_msg)
        outputs.append(next_msg)
        return outputs




if __name__ == "__main__":
    t = Time()
    print(t.items(filter_keys=True))
    m = Message(msg_type='peer')
    print(m.to_json())