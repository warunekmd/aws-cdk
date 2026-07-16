#Import necessary AWS CDK modules and constructs
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class ProductionVpcStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "ProductionVpc",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ],
            #Creates 1 NAT Gateway per AZ
            nat_gateways=2 
        )

        #Output the VPC ID for visibility
        cdk.CfnOutput(
            self, "VpcIdOutput",
            value=self.vpc.vpc_id,
            description="The ID of the production VPC"
        )

app = cdk.App()
ProductionVpcStack(
    app, "ProductionVpcStack",
    env=cdk.Environment(region="us-east-1")
)
app.synth()
