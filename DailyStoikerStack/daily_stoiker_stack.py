from constructs import Construct
from aws_cdk import (
    Duration, Stack,
    aws_iam,
    aws_events,
    aws_lambda,
    aws_events_targets,
    aws_dynamodb,
    RemovalPolicy,
)


class DailyStoikerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda function to send daily newsletter
        lambdaFn = aws_lambda.Function(
            self, "Mailer",
            code=aws_lambda.Code.from_asset('./lambda/mailer'), 
            handler="lambda_handler.main",
            timeout=Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            architecture=aws_lambda.Architecture.ARM_64,
            initial_policy=[
                aws_iam.PolicyStatement(
                    actions=["ses:SendEmail"],
                    resources=["*"],
                    conditions={
                        "StringEquals": {"ses:FromAddress": "stoiker@moed.cc"}
                    }
                )]
        )

        assert lambdaFn.role is not None
        lambdaFn.role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaDynamoDBExecutionRole")
        )

        # Run every day at 04:00 AM
        rule = aws_events.Rule(
            self, "Rule",
            schedule=aws_events.Schedule.cron(
                minute="0",
                hour="4",
                month="*",
                week_day="*",
                year="*",
            ),
        )
        rule.add_target(aws_events_targets.LambdaFunction(lambdaFn))

        

        # DynamoDB table for storing newsletter subscribers
        table = aws_dynamodb.Table(self, "stoiker_newletter",
            partition_key=aws_dynamodb.Attribute(name="email", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="stoiker_newletter",
            removal_policy=RemovalPolicy.DESTROY,
        )