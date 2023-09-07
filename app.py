#!/usr/bin/env python3

import aws_cdk as cdk

from DailyStoikerStack.daily_stoiker_stack import DailyStoikerStack

env_EU = cdk.Environment(region="eu-west-1")

app = cdk.App()

DailyStoikerStack = DailyStoikerStack(app, "daily-stoiker", env=env_EU)
cdk.Tags.of(DailyStoikerStack).add("Project", "DailyStoiker")

app.synth()
