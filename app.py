#Import necessary AWS CDK modules and constructs
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
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


class RdsStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc,
                 instance_type: str, allocated_storage: int, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Security group allowing Postgres traffic from within the VPC
        db_sg = ec2.SecurityGroup(
            self, "DbSecurityGroup",
            vpc=vpc,
            description="Allow PostgreSQL access from within the VPC",
            allow_all_outbound=False,
        )
        db_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL from VPC CIDR",
        )

        #RDS PostgreSQL instance with credentials managed by Secrets Manager
        db_instance = rds.DatabaseInstance(
            self, "PostgresInstance",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_4,
            ),
            instance_type=ec2.InstanceType(instance_type),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[db_sg],
            allocated_storage=allocated_storage,
            max_allocated_storage=allocated_storage * 2,
            database_name="appdb",
            credentials=rds.Credentials.from_generated_secret("postgres"),
            removal_policy=cdk.RemovalPolicy.DESTROY,
            deletion_protection=False,
        )

        #Outputs
        cdk.CfnOutput(
            self, "DbEndpoint",
            value=db_instance.db_instance_endpoint_address,
            description="RDS PostgreSQL endpoint",
        )
        cdk.CfnOutput(
            self, "DbSecretArn",
            value=db_instance.secret.secret_arn,
            description="ARN of the Secrets Manager secret holding DB credentials",
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
        "rds_stack_name": "DevRdsStack",
        "rds_instance_type": "t3.micro",
        "rds_allocated_storage": 20,
    },
    "prod": {
        "stack_name": "ProdVpcStack",
        "cidr": "10.0.0.0/16",
        "nat_gateways": 2,
        "rds_stack_name": "ProdRdsStack",
        "rds_instance_type": "t3.small",
        "rds_allocated_storage": 50,
    },
}

config = env_config[target_env]

vpc_stack = VpcStack(
    app, config["stack_name"],
    cidr=config["cidr"],
    nat_gateways=config["nat_gateways"],
    env=cdk.Environment(region="us-east-1"),
)

RdsStack(
    app, config["rds_stack_name"],
    vpc=vpc_stack.vpc,
    instance_type=config["rds_instance_type"],
    allocated_storage=config["rds_allocated_storage"],
    env=cdk.Environment(region="us-east-1"),
)

app.synth()
