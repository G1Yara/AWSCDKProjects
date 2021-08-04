from aws_cdk import core as cdk
from aws_cdk import aws_msk as msk
from aws_cdk import aws_logs as logs

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class MskClusterStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Setting up MSK cluster
        # read required properties from cdk.json
        msk_cluster_name = self.node.try_get_context(stage)["msk_cluster_name"]
        msk_nodes = self.node.try_get_context(stage)["msk_nodes"]
        msk_instance_type = self.node.try_get_context(stage)["msk_instance_type"]
        default_security_groups = self.node.try_get_context(stage)["default_security_groups"]
        default_vpc_subnets = self.node.try_get_context(stage)["default_vpc_subnets"]
        msk_log_group_name = self.node.try_get_context(stage)["log_group_name"]
        kafka_version = self.node.try_get_context(stage)["kafka_version"]
        msk_storage_volume = self.node.try_get_context(stage)["msk_storage_volume"]

        # Create log group
        log_group = logs.LogGroup(self,
                                  id=msk_log_group_name,
                                  log_group_name=msk_log_group_name,
                                  removal_policy=cdk.RemovalPolicy.DESTROY)

        # Create broker node
        # Set vpc subnets
        # Set security groups
        # Set instance type
        # Set storage type
        broker_node_group = msk.CfnCluster.BrokerNodeGroupInfoProperty(client_subnets=default_vpc_subnets,
                                                                       instance_type=msk_instance_type,
                                                                       storage_info=msk.CfnCluster.StorageInfoProperty(
                                                                           ebs_storage_info=msk.CfnCluster.EBSStorageInfoProperty(
                                                                               volume_size=msk_storage_volume)),
                                                                       security_groups=default_security_groups)

        # enable both TLS & Plain text
        transit_encryption = msk.CfnCluster.EncryptionInTransitProperty(in_cluster=True,
                                                                        client_broker="TLS_PLAINTEXT"
                                                                        )

        # Create MSK Cluster
        msk_cluster = msk.CfnCluster(self,
                                     id=msk_cluster_name,
                                     broker_node_group_info=broker_node_group,
                                     cluster_name=msk_cluster_name,
                                     kafka_version=kafka_version,
                                     number_of_broker_nodes=msk_nodes,
                                     logging_info=msk.CfnCluster.LoggingInfoProperty(
                                         broker_logs=msk.CfnCluster.BrokerLogsProperty(
                                             cloud_watch_logs=msk.CfnCluster.CloudWatchLogsProperty(enabled=True,
                                                                                                    log_group=log_group.log_group_name))),
                                     encryption_info=msk.CfnCluster.EncryptionInfoProperty(
                                         encryption_in_transit=transit_encryption)
                                     )
