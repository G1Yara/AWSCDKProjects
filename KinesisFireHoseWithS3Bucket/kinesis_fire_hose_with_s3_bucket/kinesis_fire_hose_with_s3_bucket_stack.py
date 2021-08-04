from aws_cdk import core as _cdk
import aws_cdk.aws_kinesisfirehose as _firehouse
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_s3 as _s3

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class KinesisFireHoseWithS3BucketStack(_cdk.Stack):

    def __init__(self, scope: _cdk.Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        fire_hose_role_arn = self.node.try_get_context(stage)["firehose_role_arn"]

        firehose_role = _iam.Role.from_role_arn(self,
                                                id="firehose-role",
                                                role_arn=fire_hose_role_arn
                                                )

        s3_bucket_name = self.node.try_get_context(stage)["s3_bucket_name"]

        s3_bucket = _s3.Bucket(self,
                               id=s3_bucket_name,
                               bucket_name=s3_bucket_name,
                               removal_policy=_cdk.RemovalPolicy.DESTROY
                               )

        s3_bucket.grant_read_write(identity=firehose_role)

        firehose_delivery_stream_name = self.node.try_get_context(stage)["firehose_name"]

        fire_hose_delivery_stream = _firehouse.CfnDeliveryStream(self,
                                                                 id=firehose_delivery_stream_name,
                                                                 delivery_stream_name=firehose_delivery_stream_name,
                                                                 s3_destination_configuration=_firehouse.CfnDeliveryStream
                                                                 .S3DestinationConfigurationProperty(
                                                                     bucket_arn=s3_bucket.bucket_arn,
                                                                     role_arn=fire_hose_role_arn,
                                                                     prefix="firehose/myTest/timestamp=!{timestamp:YYYYMMdd}/",
                                                                     error_output_prefix="firehose/errors/myTest/!{firehose:random-string}/!{firehose:error-output-type}/timestamp=!{timestamp:YYYYMMdd}/",
                                                                     buffering_hints=_firehouse.CfnDeliveryStream.BufferingHintsProperty(
                                                                         interval_in_seconds=900,
                                                                         size_in_m_bs=128
                                                                     )
                                                                 ))
