from cloudify.decorators import workflow


# @workflow
# def create(ctx, **kwargs):
#     """vnfm create workflow"""
#     graph = ctx.graph_mode()
#     for node in ctx.nodes:
#         for instance in node.instances:
#             graph.add_task(instance.execute_operation('cloudify.interfaces.lifecycle.create',
#                                                       kwargs=kwargs))
#     graph.execute()

@workflow
def start(ctx, **kwargs):
    """vnfm start workflow"""
    graph = ctx.graph_mode()
    for node in ctx.nodes:
        if node.type == 'cloudify.vnfm_cfy.virtualizer':
            for instance in node.instances:
                graph.add_task(instance.execute_operation('cloudify.interfaces.lifecycle.start',
                                                          kwargs=kwargs))
    graph.execute()

@workflow
def stop(ctx, **kwargs):
    """vnfm stop workflow"""
    graph = ctx.graph_mode()
    for node in ctx.nodes:
        if node.type == 'cloudify.vnfm_cfy.virtualizer':
            for instance in node.instances:
                graph.add_task(instance.execute_operation('cloudify.interfaces.lifecycle.stop',
                                                          kwargs=kwargs))
    graph.execute()

@workflow
def delete(ctx, **kwargs):
    """vnfm delete workflow"""
    graph = ctx.graph_mode()
    for node in ctx.nodes:
        if node.type == 'cloudify.vnfm_cfy.virtualizer':
            for instance in node.instances:
                graph.add_task(instance.execute_operation('cloudify.interfaces.lifecycle.delete',
                                                          kwargs=kwargs))
    graph.execute()

# @workflow
# def migrate(ctx, **kwargs):
#     """vnfm migrate workflow"""
#     check_built()
#     vnf_id = kwargs['vnf_id']
#     graph = ctx.graph_mode()
#     for node in ctx.nodes:
#         if node.type == 'cloudify.vnfm_cfy.nf':
#             if node.properties['id'] == vnf_id:
#                 for instance in node.instances:
#                     graph.add_task(instance.execute_operation('cloudify.interfaces.lifecycle.vnfm_migrate',
#                                    kwargs=kwargs))
#     graph.execute()
#

@workflow
def create(ctx, **kwargs):
    graph = ctx.graph_mode()
    for node in ctx.nodes:
        for instance in node.instances:
            graph.add_task(instance.execute_operation('cloudify.interfaces.lifecycle.create'))
    graph.execute()

    for node in ctx.nodes:
        for instance in node.instances:
            # ctx.logger.info('edit_config node: {0}'.format(dir(instance)))
            for relationship in instance.relationships:
                graph.add_task(
                    relationship.execute_target_operation('cloudify.interfaces.relationship_lifecycle.establish'))
                graph.add_task(
                    relationship.execute_source_operation('cloudify.interfaces.relationship_lifecycle.establish'))
    graph.execute()
