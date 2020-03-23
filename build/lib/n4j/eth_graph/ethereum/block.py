from datetime import datetime
# from typing import List

__author__ = 'Sander'


class Transaction():
    def __init__(self):
        pass

    @property
    def from_address(self):
        pass

    @property
    def to_address(self):
        pass

    @property
    def value(self):
        pass

    @property
    def __hash__(self):
        pass


class Block():
    def __init__(self):
        pass

    @property
    def transactions(self):
        pass

    @property
    def timestamp(self):
        pass

    @property
    def hash(self):
        pass

    @property
    def parent_hash(self):
        pass

    @property
    def number(self):
        pass


class GethBlock(Block):
    def __init__(self, block_data):
        Block.__init__(self)
        self.block_data = block_data

    @property
    def transactions(self):
        return [GethTransaction(trans) for trans in self.block_data['transactions']]

    @property
    def timestamp(self):
        return datetime.fromtimestamp(int(self.block_data['timestamp'], 16))

    @property
    def hash(self):
        return self.block_data['hash']

    @property
    def parent_hash(self):
        return self.block_data['parentHash']

    @property
    def number(self):
        return int(self.block_data['number'], 16)


class GethTransaction(Transaction):
    def __init__(self, trans_data):
        Transaction.__init__(self)
        self.trans_data = trans_data

    @property
    def from_address(self):
        return self.trans_data['from']

    @property
    def value(self):
        return int(self.trans_data['value'], 16) / 1e18

    @property
    def to_address(self):
        return self.trans_data['to']

    @property
    def hash(self):
        return self.trans_data['hash']
