# signals/__init__.py
# Import all signal modules to trigger @register_signal decorators
from signals.technical import regime_gate  # noqa: F401 (side-effect import)
from signals.technical import rsi_confluence  # noqa: F401
from signals.technical import breakout_confluence  # noqa: F401
from signals.technical import intraday_momentum  # noqa: F401
from signals.quant import mean_reversion  # noqa: F401
from signals.fundamental import earnings_alert  # noqa: F401
