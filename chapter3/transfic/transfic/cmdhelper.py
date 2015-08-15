import os

from bgcore import logging as bglogging

from fannsdb.cmdhelper import Command, PredictorsTrait, TransformsTrait

DefaultCommandHelper = Command.withtraits(PredictorsTrait, TransformsTrait)