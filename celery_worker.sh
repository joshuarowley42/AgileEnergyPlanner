#!/bin/bash

celery -A tasks.tasks worker --loglevel=INFO -B
