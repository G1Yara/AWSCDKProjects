from aws_cdk import core as cdk
from aws_cdk import aws_emr as _emr
from aws_cdk import aws_ec2 as _ec2

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class EmrClusterWithHbaseStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Setting up EMR Cluster
        # look up for existing default vpc
        vpc = _ec2.Vpc.from_lookup(self,
                                   id="vpc",
                                   vpc_id=self.node.try_get_context(stage)["vpc_id"])

        security_group_name = self.node.try_get_context(stage)["security_group_name"]

        # creating new security group for emr cluster
        emr_security_group = _ec2.SecurityGroup(self,
                                                id=security_group_name,
                                                security_group_name=security_group_name,
                                                vpc=vpc)

        acadia_services_sg = self.node.try_get_context(stage)["acadia_services_security_groups"]

        # look up for existing acadia services security group
        launch_wizard_sg = _ec2.SecurityGroup.from_lookup(self,
                                                          id=acadia_services_sg[0],
                                                          security_group_id=acadia_services_sg[0])

        # add existing acadia services security group as inbound rule to emr security group
        emr_security_group.add_ingress_rule(peer=launch_wizard_sg,
                                            connection=_ec2.Port.all_traffic(),
                                            description="existing services sg")

        # creating emr cluster instance type
        # setting up instance type & count
        # setting up storage size
        # setting up storage type

        master_instance_group = _emr.CfnCluster.InstanceGroupConfigProperty(
            instance_count=self.node.try_get_context(stage)["emr_cluster_instance_count"],
            instance_type=self.node.try_get_context(stage)["emr_cluster_instance_type"],
            name=self.node.try_get_context(stage)["emr_cluster_instance_name"],
            ebs_configuration=_emr.CfnCluster.EbsConfigurationProperty(
                ebs_block_device_configs=[_emr.CfnCluster.EbsBlockDeviceConfigProperty(
                    volume_specification=_emr.CfnCluster.VolumeSpecificationProperty(
                        size_in_gb=self.node.try_get_context(stage)["emr_cluster_instance_size_in_gbs"],
                        volume_type=self.node.try_get_context(stage)["emr_cluster_instance_volume_type"]))]
            )
        )

        # creating job flow config
        # setting up subnet
        # setting up pem key name
        # setting up hadoop version
        # setting up security group id
        emr_instance = _emr.CfnCluster.JobFlowInstancesConfigProperty(
            master_instance_group=master_instance_group,
            additional_master_security_groups=[emr_security_group.security_group_id],
            additional_slave_security_groups=[emr_security_group.security_group_id],
            core_instance_group=master_instance_group,
            ec2_subnet_id=self.node.try_get_context(stage)["default_vpc_subnets"][0],
            ec2_key_name=self.node.try_get_context(stage)["ec2_key_name"],
            hadoop_version=self.node.try_get_context(stage)["hadoop_version"]
        )

        # creating required application list
        # required applications are zookeeper, hbase, etc
        emr_required_apps_list = list()
        for app in self.node.try_get_context(stage)["emr_cluster_required_applications"]:
            app_property = _emr.CfnCluster.ApplicationProperty(
                name=app
            )
            emr_required_apps_list.append(app_property)

        emr_cluster_name = self.node.try_get_context(stage)["emr_cluster_name"]

        configurations_list = list()
        config_property = _emr.CfnCluster.ConfigurationProperty(
            classification="hbase",
            configuration_properties={"hbase.emr.storageMode": self.node.try_get_context(stage)["emr_cluster_hbase_storage"]}
        )
        config_property_1 = _emr.CfnCluster.ConfigurationProperty(
            classification="hbase-site",
            configuration_properties={"hbase.rootdir": self.node.try_get_context(stage)["emr_cluster_hbase_s3_path"]}
        )
        configurations_list.append(config_property)
        configurations_list.append(config_property_1)

        # creating emr cluster
        _emr.CfnCluster(self,
                        id=emr_cluster_name + stage,
                        name=emr_cluster_name,
                        instances=emr_instance,
                        release_label=self.node.try_get_context(stage)["emr_cluster_version"],
                        job_flow_role=self.node.try_get_context(stage)["emr_cluster_job_role"],
                        service_role=self.node.try_get_context(stage)["emr_cluster_service_role"],
                        visible_to_all_users=True,
                        ebs_root_volume_size=self.node.try_get_context(stage)["emr_cluster_volume_size"],
                        applications=emr_required_apps_list,
                        log_uri=self.node.try_get_context(stage)["emr_cluster_log_s3_bucket"],
                        configurations=configurations_list
                        )
