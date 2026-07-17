#Import necessary AWS CDK modules and constructs
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class VpcStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, cidr: str, nat_gateways: int, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr(cidr),
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
            nat_gateways=nat_gateways
        )

        #Output the VPC ID for visibility
        cdk.CfnOutput(
            self, "VpcIdOutput",
            value=self.vpc.vpc_id,
            description=f"The ID of the {construct_id} VPC"
        )


app = cdk.App()

#Retrieve the target environment from CDK context (-c env=dev|prod)
target_env = app.node.try_get_context("env") or "dev"

#Environment configs — same account, different CIDRs and cost profiles
env_config = {
    "dev": {
        "stack_name": "DevVpcStack",
        "cidr": "10.1.0.0/16",
        "nat_gateways": 1,
    },
    "prod": {
        "stack_name": "ProdVpcStack",
        "cidr": "10.0.0.0/16",
        "nat_gateways": 2,
    },
}

config = env_config[target_env]

VpcStack(
    app, config["stack_name"],
    cidr=config["cidr"],
    nat_gateways=config["nat_gateways"],
    env=cdk.Environment(region="us-east-1"),
)

app.synth()
