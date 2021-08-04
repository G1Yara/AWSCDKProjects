from aws_cdk import core as _cdk
from aws_cdk import aws_s3 as _s3

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class S3WithGlacierStack(_cdk.Stack):

    def __init__(self, scope: _cdk.Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        s3_bucket_name = self.node.try_get_context(stage)["s3_bucket_name"]

        transition = _s3.Transition(storage_class=_s3.StorageClass.GLACIER,
                                    transition_after=_cdk.Duration.days(90)
                                    )

        s3_lifecyle_rule = _s3.LifecycleRule(id="lifecycle rule",
                                             transitions=[transition])
        cdp_s3_glacier = _s3.Bucket(self,
                                    id=s3_bucket_name,
                                    bucket_name=s3_bucket_name,
                                    removal_policy=_cdk.RemovalPolicy.DESTROY,
                                    lifecycle_rules=[s3_lifecyle_rule]
                                    )
