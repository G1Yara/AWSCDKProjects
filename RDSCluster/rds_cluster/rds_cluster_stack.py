import aws_cdk.aws_rds as rds
from aws_cdk import aws_ec2 as ec2
from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.


class RdsClusterStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, id="vpc", vpc_id="vpc-bec12345")

        security_group_name = "mySecurityGroup"

        # create new security group
        security_group = ec2.SecurityGroup(self,
                                           id=security_group_name,
                                           security_group_name=security_group_name,
                                           vpc=vpc)
        # create new rds db instance
        rds.ServerlessCluster(self,
                              "rds-database",
                              engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
                              vpc=vpc,
                              scaling=rds.ServerlessScalingOptions(
                                  min_capacity=rds.AuroraCapacityUnit.ACU_1,
                                  max_capacity=rds.AuroraCapacityUnit.ACU_1
                              ),
                              # below statement creates new secret manger with name "myTestSecret"
                              # and generates auto generated password and stores along with other details
                              credentials=rds.Credentials.from_generated_secret(username="root",
                                                                                secret_name="myTestSecret"),
                              security_groups=[security_group],
                              vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                              default_database_name="myTestRdsDB",
                              cluster_identifier="myTestRdsDB",
                              removal_policy=cdk.RemovalPolicy.DESTROY,
                              subnet_group=vpc
                              )
