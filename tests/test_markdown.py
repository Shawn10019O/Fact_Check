from core.models import results_to_markdown, SlideResult, SuspiciousClaim
from pytest_regressions.data_regression import DataRegressionFixture

def test_markdown(data_regression: DataRegressionFixture):
    slide = SlideResult(1, "raw", "clean", "REFUTED", "bad", [SuspiciousClaim("oops")])
    md = results_to_markdown([slide])
    data_regression.check(md)
