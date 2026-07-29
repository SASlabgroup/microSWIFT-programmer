from dataclasses import dataclass


@dataclass
class CTConfig:
    ct_enabled: bool
    temperature_enabled: bool


@dataclass
class LightConfig:
    enabled: bool
    num_samples: int
    gain_index: int


@dataclass
class TurbidityConfig:
    enabled: bool
    num_samples: int
    serial_number: int


@dataclass
class IridiumConfig:
    tx_time: int
    v3f: bool


@dataclass
class GNSSConfig:
    num_samples: int
    high_performance_mode: bool
    sample_rate: int


@dataclass
class TimingConfig:
    duty_cycle: int
    gnss_max_acquisition_time: int
    tracking_number: int

@dataclass
class AccelerometerConfig:
    enabled: bool
    continuous: bool
