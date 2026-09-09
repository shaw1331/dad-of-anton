from app.stock_analyser.analysis.factory import AnalysisFactory
from app.stock_analyser.analysis.prompts.momentum import MomentumStrategy
from app.stock_analyser.analysis.prompts.value_investing import ValueInvestingStrategy
from app.stock_analyser.analysis.prompts.swing_momentum import SwingMomentumStrategy

AnalysisFactory.register("value_investing", ValueInvestingStrategy)
AnalysisFactory.register("momentum", MomentumStrategy)
AnalysisFactory.register("swing_momentum", SwingMomentumStrategy)
