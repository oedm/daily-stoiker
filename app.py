#!/usr/bin/env python3

import aws_cdk as cdk

from DailyStoikerStack.daily_stoiker_stack import DailyStoikerStack

env_EU = cdk.Environment(region="eu-west-1")

app = cdk.App()

DailyStoikerProduction = DailyStoikerStack(app, "daily-stoiker-prod", env=env_EU)
cdk.Tags.of(DailyStoikerProduction).add("Project", "DailyStoiker")

DailyStoikerDevelopment = DailyStoikerStack(app, "daily-stoiker-dev", env=env_EU)
cdk.Tags.of(DailyStoikerDevelopment).add("Project", "DailyStoiker")


app.synth()
