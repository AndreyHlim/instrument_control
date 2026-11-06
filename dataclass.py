from dataclasses import dataclass, field


@dataclass
class DeviceState:
    """Снимок состояния анализатора для обновления формы."""
    freqs: list = field(default_factory=list)   # список частот экрана
    levels: list = field(default_factory=list)  # список амплитуд экрана

    # RBW, VBW
    rbw_type: str | None = None
    rbw: float | None = None
    rbw_unit: str | None = None
    vbw: float | None = None          # в кГц
    vbw_auto: bool | None = None
    rbw_auto: bool | None = None

    # частоты
    span: float | None = None
    center: float | None = None
    cfstep: float | None = None

    # Амплитуды
    reflevel: float | None = None
    amp_unit: str | None = None
    atten: int | None = None
    range_val: float | None = None
    preamp: str | None = None
    transducer: str | None = None

    # Sweep
    det: str | None = None
    trace_acc: str | None = None
    sweep_single: bool | None = None
    sweep_count: int | None = None

    # Маркеры
    marker_level: float | None = None
