########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import json
from cloudify import ctx
from cloudify.decorators import operation
from vnfm_cfy.interface import WebClient


rest_client = WebClient()

def get_node_type(node):
    node_type_ = str(node.type)
    node_type = str.split(node_type_, '.')[-1]
    return node_type

def is_filled(value):
    if type(value) is dict:
        for item in value:
            if value[item]:
                return True
            else:
                pass
    if type(value) is list:
        for item in value:
            if item:
                return True
            else:
                pass
    return False

def convert_to_dict(variable):
    dict_ = {}
    if type(variable) is list:
        variable = ','.join(variable)
    var = str(variable)
    items_ = var.split(',')
    _ids = 1
    for item in items_:
        if 'None' not in item:
            if ':' in item:
                k,v = item.split(':')
                dict_[_ids] = v
            else:
                if item:
                    v = item
                    dict_[_ids] = v
            _ids += 1
    return dict_

def fill_cls(dict_obj, fields, node_properties):
    for prop,value in node_properties.items():
        if prop in fields and value:
            if prop not in dict_obj:
                dict_obj[prop] = value

def create_flow(node):
    fields = ['priority']
    flow = {}
    matches = {}
    actions = {}

    fill_cls(flow, fields, node.properties)
    if is_filled(node.properties['match']):
        fields = [
            "in_port", "dl_src", "dl_dst", "nw_src", "nw_dst",
            "ipv6_src", "ipv6_dst", "nw_proto", "tp_src" , "tp_dst", "ip_dscp"
        ]
        fill_cls(matches, fields, node.properties['match'])

    if is_filled(node.properties['actions']):
        fields = ["mark", "meter", "queue", "output"]
        fill_cls(actions, fields, node.properties['actions'])

    if "tag" in node.properties['actions']:

        tag_action = node.properties['actions']["tag"]
        tag_id = node.properties['match']["dl_vlan"]
        if tag_action == 'push':
            # match = {
            #     'dl_type': 'IPv4'
            # }
            # matches.update(match)

            action = {
                'push_vlan': 'VLAN',
                'set_field': {
                    'field': 'vlan_vid',
                    'value': tag_id
                },
            }
            actions.update(action)


        elif tag_action == 'match':
            match = {
                # 'dl_type': 'VLAN',
                'vlan_vid': tag_id
            }
            matches.update(match)

        elif tag_action == 'pop':
            match = {
                # 'dl_type': 'VLAN',
                'vlan_vid': tag_id
            }
            matches.update(match)

            action = {
                'pop_vlan': 'IPv4',
            }
            actions.update(action)

    flow['match'] = matches
    flow['actions'] = actions
    return flow

def create_port(node):
    fields = ["id", "name", "port_type", "capability", "sap"]
    port = {}
    fill_cls(port, fields, node.properties)
    return port

def create_queue(node):
    fields = ["port_name", "type", "max_rate", "queues"]
    queue = {}
    fill_cls(queue, fields, node.properties)
    return queue

def create_meter(node):
    fields = ["meter_id"]
    meter = {}
    fill_cls(meter, fields, node.properties)
    return meter

def create_band(node):
    fields = ["action", "flag", "burst_size", "rate", "prec_level"]
    band = {}
    fill_cls(band, fields, node.properties)
    return band

def create_obj(node):
    obj = None
    node_type = get_node_type(node)
    if node_type == 'switch':
        pass
    elif node_type == 'flow':
        obj = create_flow(node)
    elif node_type == 'port':
        obj = create_port(node)
    elif node_type == 'queue':
        obj = create_queue(node)
    elif node_type == 'meter':
        obj = create_meter(node)
    elif node_type == 'band':
        obj = create_band(node)
    else:
        pass
        # ctx.logger.info('unknown node type to create obj: {0}'.format(node_type))
    return node_type, obj


def add_flow(source_obj, target_obj):
    pass

def add_queue(source_obj, target_obj):
    pass

def add_meter(source_obj, target_obj):
    pass

def add_band(source_obj, target_obj):
    if 'bands' not in source_obj:
        source_obj['bands'] = []
    source_obj['bands'].append(target_obj)


def fill_relationships(relationship_type, source_obj, target_obj):
    if relationship_type == 'flow':
        add_flow(source_obj, target_obj)
    elif relationship_type == 'queue':
        add_queue(source_obj, target_obj)
    elif relationship_type == 'meter':
        add_meter(source_obj, target_obj)
    elif relationship_type == 'band':
        add_band(source_obj, target_obj)
    else:
        pass

def build_target(node):
    # if node.name in built_nodes:
    #     target_obj = built_nodes[node.name]
    # else:
    target_type, target_obj = create_obj(node)
        # built_nodes[node.name] = target_obj
    return target_type, target_obj

def build_relationships(source_instance, node, instance):
    for rel in instance.relationships:
        _,target_obj = build_target(rel.target.node)
        relationship_type = get_node_type(rel)
        fill_relationships(relationship_type, source_instance, target_obj)
        # build_relationships(target_obj, rel.target.node, rel.target.instance)


def build(node, instance):
    node_type, node_dict = create_obj(node)
    build_relationships(node_dict, node, instance)
    ctx.instance.runtime_properties['dict'] = node_dict
    return node_type, node_dict

def get_url_path(node_type, switch_id):
    path = None
    prefix = '/qos'
    if node_type == 'meter':
        path = prefix + '/' + node_type + '/' + switch_id
    if node_type == 'queue':
        path = prefix + '/' + node_type + '/' + switch_id
    if node_type == 'flow':
        path = prefix + '/' + 'rules' + '/' + switch_id
    return path

def send_cfg(url, switch_id, node_type, op, data):
    rest_client.set_logger(ctx.logger)
    path = get_url_path(node_type, switch_id)
    url_path = url + path
    reply = rest_client.send_msg(op, url_path, data)
    return reply

def get_deploy(node, instance):
    url, switch_id = None, None
    for rel in instance.relationships:
        target_type = get_node_type(rel.target.node)
        relationship_type = get_node_type(rel)
        if relationship_type in ['flow', 'meter', 'queue']:
            if target_type == 'switch':
                url = rel.target.node.properties['url']
                switch_id = rel.target.node.properties['id']
                break
    return url, switch_id

def parse_reply(node_type, reply):
    ctx.logger.info("reply %s", reply)
    reply_acks = []
    for ack in reply:
        cmd_result = ack.get('command_result', [])
        if node_type in ['meter', 'flow']:
            for result in cmd_result:
                msg = result.get('result')
                if msg == "success":
                    reply_acks.append(True)
                else:
                    reply_acks.append(False)
        elif node_type in ['queue',]:
            if type(cmd_result) is dict:
                msg = cmd_result.get('result', None)
            else:
                msg = cmd_result
            if msg == "success":
                reply_acks.append(True)
            else:
                reply_acks.append(False)
    final_ack = all(reply_acks)
    return final_ack

@operation
def vnfm_create(**kwargs):
    op = 'post'
    node_type, dict_obj = build(ctx.node, ctx.instance)
    if node_type in ['meter', 'queue', 'flow']:
        url, switch_id = get_deploy(ctx.node, ctx.instance)
        data = json.dumps(dict_obj)
        ctx.logger.info("create %s - data %s", node_type, data)
        ctx.logger.info("send to url %s - switch_id %s", url, switch_id)
        ack = send_cfg(url, switch_id, node_type, op, data)
        ctx.logger.info("reply %s", ack)
        if ack:
            ack_dict = json.loads(ack)
            ack = parse_reply(node_type, ack_dict)
            ctx.instance.runtime_properties['ack'] = ack
        else:
            ctx.instance.runtime_properties['ack'] = False


@operation
def vnfm_delete(**kwargs):
    op = 'delete'
    node_type, dict_obj = build(ctx.node, ctx.instance)
    if node_type in ['meter', 'queue', 'flow']:
        url, switch_id = get_deploy(ctx.node, ctx.instance)
        data = json.dumps(dict_obj)
        ctx.logger.info("create %s - data %s", node_type, data)
        ctx.logger.info("send to url %s - switch_id %s", url, switch_id)
        ack = send_cfg(url, switch_id, node_type, op, data)
        ctx.logger.info("reply %s", ack)
        if ack:
            ack_dict = json.loads(ack)
            ack = parse_reply(node_type, ack_dict)
            ctx.instance.runtime_properties['ack'] = ack
        else:
            ctx.instance.runtime_properties['ack'] = False


@operation
def vnfm_update(**kwargs):
    pass

@operation
def vnfm_start(**kwargs):
    pass

@operation
def vnfm_stop(**kwargs):
    pass
