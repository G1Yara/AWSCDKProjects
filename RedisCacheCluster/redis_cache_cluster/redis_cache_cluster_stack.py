from aws_cdk import core as cdk
from aws_cdk import aws_ec2 as ec2
import aws_cdk.aws_elasticache as _elastic_cache

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class RedisCacheClusterStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, stage: str,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # look up for existing vpc
        vpc = ec2.Vpc.from_lookup(self, id="vpc",
                                  vpc_id=self.node.try_get_context(stage)["vpc_id"])

        elastic_cache_security_group_ids = list()
        security_group_name = self.node.try_get_context(stage)["security_group_name"]

        # create new security group
        security_group = ec2.SecurityGroup(self,
                                           id=security_group_name,
                                           security_group_name=security_group_name,
                                           vpc=vpc)
        elastic_cache_security_group_ids.append(security_group.security_group_id)

        # get elastic cache properties from cdk.json file
        elastic_cluster_name = self.node.try_get_context(stage)["elastic_cache_cluster_name"]
        elastic_cache_node_type = self.node.try_get_context(stage)["elastic_cache_node_type"]
        elastic_cache_engine = self.node.try_get_context(stage)["elastic_cache_engine"]
        elastic_cache_nodes = self.node.try_get_context(stage)["elastic_cache_nodes"]
        elastic_redis_port = self.node.try_get_context(stage)["elastic_redis_port"]
        elastic_cache_subnet_name = self.node.try_get_context(stage)["elastic_cache_subnet_name"]

        # create elastic cache with redis engine
        _elastic_cache.CfnCacheCluster(self,
                                       id=elastic_cluster_name,
                                       cache_node_type=elastic_cache_node_type,
                                       num_cache_nodes=elastic_cache_nodes,
                                       engine=elastic_cache_engine,
                                       cluster_name=elastic_cluster_name,
                                       port=elastic_redis_port,
                                       cache_subnet_group_name=elastic_cache_subnet_name,
                                       vpc_security_group_ids=elastic_cache_security_group_ids,
                                       )
