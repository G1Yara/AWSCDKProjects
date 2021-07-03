from aws_cdk import core as cdk
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
import aws_cdk.aws_globalaccelerator as globalaccelerator
import aws_cdk.aws_globalaccelerator_endpoints as ga_endpoints
import aws_cdk.aws_logs as logs

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class EcsClusterWithAlbStack(cdk.Stack):

    def create_farget_task(self, task_name: str, role: iam.Role):
        task_definition = ecs.TaskDefinition(self,
                                             id=task_name,
                                             family=task_name,
                                             cpu="512", memory_mib="1024",
                                             compatibility=ecs.Compatibility.FARGATE,
                                             execution_role=role,
                                             task_role=role,
                                             )
        return task_definition

    def create_fargate_service(self, name: str, cluster: ecs.Cluster, task_definition: ecs.TaskDefinition,
                               securityGroup: [ec2.SecurityGroup]):
        service = ecs.FargateService(self,
                                     id=name,
                                     service_name=name,
                                     cluster=cluster,
                                     task_definition=task_definition,
                                     desired_count=1,
                                     assign_public_ip=True,
                                     health_check_grace_period=cdk.Duration.seconds(483),
                                     security_groups=securityGroup
                                     )
        return service

    def get_repository(self, name: str):
        repository = ecr.Repository.from_repository_name(self, id=name, repository_name=name)
        return repository

    def get_container_image_from_repository(self, repository: ecr.Repository, tag: str):
        image = ecs.ContainerImage.from_ecr_repository(repository=repository, tag=tag)
        return image

    def create_target_group(self, port: int, path_pattern: str, priority: int, name: str, container: ecs.TaskDefinition,
                            service: ecs.FargateService, listener: elbv2.IApplicationListener):
        target_group = listener.add_targets(id=name,
                                            port=port,
                                            protocol=elbv2.ApplicationProtocol.HTTP,
                                            target_group_name=name,
                                            deregistration_delay=cdk.Duration.seconds(60),
                                            targets=[service.load_balancer_target(
                                                container_name=container.container_name,
                                            )],
                                            path_pattern=path_pattern,
                                            priority=priority
                                            )
        return target_group

    def add_health_checks(self, path: str, target_group: elbv2.ApplicationTargetGroup):
        target_group.configure_health_check(path=path,
                                            protocol=elbv2.Protocol.HTTP,
                                            interval=cdk.Duration.seconds(300),
                                            unhealthy_threshold_count=5,
                                            healthy_threshold_count=2,
                                            healthy_http_codes="200",
                                            )

    def __init__(self, scope: cdk.Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # look for existing VPC
        vpc = ec2.Vpc.from_lookup(self, id="vpc",
                                  vpc_id=self.node.try_get_context(stage)["vpc_id"])

        security_group_name = self.node.try_get_context(stage)["security_group_name"]

        # create new security group
        security_group = ec2.SecurityGroup(self,
                                           id=security_group_name,
                                           security_group_name=security_group_name,
                                           vpc=vpc)

        # create ecs cluster
        cluster = ecs.Cluster(self,
                              id=self.node.try_get_context(stage)["cluster_name"],
                              cluster_name=self.node.try_get_context(stage)["cluster_name"],
                              vpc=vpc)
        # look for existing Iam role
        role = iam.Role.from_role_arn(self,
                                      id="task-role"+"-"+stage,
                                      role_arn=self.node.try_get_context(stage)["role_arn"]
                                      )
        cdk.CfnOutput(self, id="role"+"-"+stage, description="role"+"-"+stage, value=f'{role.role_name}', export_name="role"+"-"+stage)

        # create task definition
        task_definition = self.create_farget_task(task_name=self.node.try_get_context(stage)["task_name"],
                                                  role=role)

        # ecr repository name
        ecr_repository = self.get_repository(self.node.try_get_context(stage)["repository_name"])

        # ecr portal repository name
        cdk.CfnOutput(self, "api repository arn", description="api repository arn",
                      value=f'{ecr_repository.repository_arn}')

        # get image from ecr repository
        docker_image = self.get_container_image_from_repository(repository=ecr_repository,
                                                                tag=self.node.try_get_context(stage)["tag"])

        cdk.CfnOutput(self, "api image name", description="api docker image name", value=f'{docker_image.image_name}')

        log_group_name = self.node.try_get_context(stage)["log_group_name"]

        log_group = logs.LogGroup(self, id=log_group_name, log_group_name=log_group_name,
                                  removal_policy=cdk.RemovalPolicy.DESTROY)

        # container
        container = task_definition.add_container(id="api-container",
                                                  image=docker_image,
                                                  container_name=self.node.try_get_context(stage)["container_name"],
                                                  environment={
                                                    "spring.datasource.username": self.node.try_get_context(stage)["db_user_name"],
                                                    "spring.datasource.password": self.node.try_get_context(stage)["db_password"],
                                                    "spring.datasource.url": self.node.try_get_context(stage)["spring_datasource_url"],
                                                    "server.port": self.node.try_get_context(stage)["server_port"],
                                                    "aws.secretsmanager.secretname": "",
                                                          },
                                                  logging=ecs.LogDriver.aws_logs(stream_prefix="ecs",
                                                                                 log_group=log_group),
                                                          )

        container.add_port_mappings(
            ecs.PortMapping(container_port=int(self.node.try_get_context(stage)["server_port"]),
                            host_port=int(self.node.try_get_context(stage)["server_port"])))

        # getting existing load balancer
        load_balancer = elbv2.ApplicationLoadBalancer.from_lookup(self,
                                                                  id="load-balancer",
                                                                  load_balancer_arn=self.node.try_get_context(stage)[
                                                                      "load_balancer_arn"]
                                                                  )

        target_group_port = self.node.try_get_context(stage)["target_group_port"]

        #  lister to load balancer
        load_balancer_listener_port = self.node.try_get_context(stage)["loadbalancer_listner_port"]

        certificate_arn = self.node.try_get_context(stage)["certificate_arn"]

        load_balancer_listener = load_balancer.add_listener(id="alb_listener", port=load_balancer_listener_port, open=True,
                                                            protocol=elbv2.ApplicationProtocol.HTTPS,
                                                            certificate_arns=[certificate_arn],
                                                            default_action=elbv2.ListenerAction.fixed_response(status_code=404,
                                                                                                               message_body="not found"))

        # creating api fargate service
        farget_service = self.create_fargate_service(name=self.node.try_get_context(stage)["service_name"],
                                                     cluster=cluster,
                                                     task_definition=task_definition,
                                                     securityGroup=[security_group])

        # adding target group to api listener of load balancer
        target_group = self.create_target_group(port=target_group_port,
                                                path_pattern=self.node.try_get_context(stage)["api_pattern"],
                                                priority=1,
                                                name=self.node.try_get_context(stage)["target_group_name"],
                                                container=container,
                                                service=farget_service,
                                                listener=load_balancer_listener)

        # adding api health check to the target group
        self.add_health_checks(path=self.node.try_get_context(stage)["health_check_api"],
                               target_group=target_group)

        is_accelerated_required = self.node.try_get_context(stage)["is_accelerator_required"]
        if is_accelerated_required:
            # Create an Accelerator
            accelerator_name = self.node.try_get_context(stage)["alb_accelerator_name"]
            accelerator = globalaccelerator.Accelerator(self, id=accelerator_name, enabled=True)

            # Create a Listener for accelerator
            accelerator_listener = accelerator.add_listener("accelerator-listener",
                                                            port_ranges=[
                                                                globalaccelerator.PortRange(from_port=target_group_port)
                                                            ]
                                                            )
            # Create end point for accelerator
            endpoint_group = accelerator_listener.add_endpoint_group("accelerator-end-group",
                                                                     endpoints=[
                                                                         ga_endpoints.ApplicationLoadBalancerEndpoint(
                                                                             load_balancer=load_balancer,
                                                                             preserve_client_ip=True
                                                                         )
                                                                     ]
                                                                     )
            # accelerator security group
            accelerator_security_group = endpoint_group.connections_peer(id="accelerator-security-group", vpc=vpc)

            # Allow connections from the accelerator security group to the ALB
            load_balancer.connections.allow_from(accelerator_security_group, port_range=ec2.Port.tcp(target_group_port))
