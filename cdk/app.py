#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import aws_cdk as cdk
from colnews_stack import ColnewsStack

app = cdk.App()
ColnewsStack(app, "ColnewsStack")
app.synth()
