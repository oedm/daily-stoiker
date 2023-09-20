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
from aws_cdk.aws_lambda_python_alpha import PythonFunction


class DailyStoikerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for storing newsletter subscribers
        table = aws_dynamodb.Table(self, "stoiker_newsletter",
            partition_key=aws_dynamodb.Attribute(name="email", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Lambda function to send daily newsletter
        lambdaFn = PythonFunction(
            self, "Mailer",
            entry="./lambda/mailer", 
            handler="main",
            index="lambda_handler.py",
            timeout=Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            architecture=aws_lambda.Architecture.ARM_64,
            environment={
                "NEWSLETTER_TABLE": table.table_name
            },
            initial_policy=[
                aws_iam.PolicyStatement(
                    actions=["ses:SendEmail"],
                    resources=["*"],
                    conditions={
                        "StringEquals": {"ses:FromAddress": "stoiker@moed.cc"}
                    }
                ),
                aws_iam.PolicyStatement(
                    sid="ListandDescribe",
                    actions=[
                        "dynamodb:List*",
                        "dynamodb:DescribeReservedCapacity*",
                        "dynamodb:DescribeLimits",
                        "dynamodb:DescribeTimeToLive"
                    ],
                    resources=["*"],
                ),
                aws_iam.PolicyStatement(
                    sid="NewsletterTable",
                    actions=[
                        "dynamodb:BatchGet*",
                        "dynamodb:DescribeStream",
                        "dynamodb:DescribeTable",
                        "dynamodb:Get*",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchWrite*",
                        "dynamodb:CreateTable",
                        "dynamodb:Delete*",
                        "dynamodb:Update*",
                        "dynamodb:PutItem"
                    ],
                    resources=[f"arn:aws:dynamodb:*:*:table/{table.table_name}"],
                ),
                ]
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

        

        