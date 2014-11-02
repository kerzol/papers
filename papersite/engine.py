#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Papers
    ~~~~~~

    Discuss scientific papers!

    :author: Sergey Kirgizov
    :license: public domain or CC0
"""
from __future__ import print_function

import hashlib, os, string
from math import ceil
from datetime import timedelta
from werkzeug import secure_filename
from flask import (Flask, render_template, url_for,
                   request, redirect, flash, escape, abort)







