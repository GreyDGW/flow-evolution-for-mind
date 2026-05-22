"""Signal gain factor calculation (PRD 4.3)."""

from .flow_models import FlowSignalInput


def _validate_signal_score(value: int, name: str) -> None:
    if value < 0 or value > 3:
        raise ValueError(f"{name} must be in [0, 3], got {value}")


def calculate_signal_gain_factor(signal: FlowSignalInput) -> float:
    """
    PRD formula:
    signal_raw = sum(scores) / 15
    gain = 1.0 + signal_raw * 0.6
    if rebellion == 3: gain += 0.2
    """
    _validate_signal_score(signal.rebellion, "rebellion")
    _validate_signal_score(signal.followup, "followup")
    _validate_signal_score(signal.correction, "correction")
    _validate_signal_score(signal.time_depth, "time_depth")
    _validate_signal_score(signal.meta_cognition, "meta_cognition")

    total = (
        signal.rebellion
        + signal.followup
        + signal.correction
        + signal.time_depth
        + signal.meta_cognition
    )
    signal_raw = total / 15.0
    gain = 1.0 + signal_raw * 0.6
    if signal.rebellion == 3:
        gain += 0.2
    return min(gain, 1.8)


class FlowSignal:
    """心流信号分析器"""
    
    def __init__(self):
        pass
    
    def analyze(self, text: str) -> FlowSignalInput:
        """分析文本内容，计算信号维度得分"""
        rebellion = self._calculate_rebellion(text)
        followup = self._calculate_followup(text)
        correction = self._calculate_correction(text)
        time_depth = self._calculate_time_depth(text)
        meta_cognition = self._calculate_meta_cognition(text)
        
        return FlowSignalInput(
            rebellion=rebellion,
            followup=followup,
            correction=correction,
            time_depth=time_depth,
            meta_cognition=meta_cognition
        )
    
    def _calculate_rebellion(self, text: str) -> int:
        """计算反叛度"""
        score = 0
        if '不对' in text or '不是' in text:
            score += 1
        if '但是' in text or '然而' in text:
            score += 1
        if '质疑' in text or '挑战' in text:
            score += 1
        return min(score, 3)
    
    def _calculate_followup(self, text: str) -> int:
        """计算跟进度"""
        score = 0
        if '然后' in text or '接下来' in text:
            score += 1
        if '继续' in text or '接着' in text:
            score += 1
        if '跟进' in text or '后续' in text:
            score += 1
        return min(score, 3)
    
    def _calculate_correction(self, text: str) -> int:
        """计算校正度"""
        score = 0
        if '修正' in text or '调整' in text:
            score += 1
        if '改进' in text or '优化' in text:
            score += 1
        if '修复' in text or '解决' in text:
            score += 1
        return min(score, 3)
    
    def _calculate_time_depth(self, text: str) -> int:
        """计算时间深度"""
        score = 0
        if '之前' in text or '以后' in text:
            score += 1
        if '过去' in text or '未来' in text:
            score += 1
        if '长期' in text or '短期' in text:
            score += 1
        return min(score, 3)
    
    def _calculate_meta_cognition(self, text: str) -> int:
        """计算元认知"""
        score = 0
        if '思考' in text or '反思' in text:
            score += 1
        if '分析' in text or '总结' in text:
            score += 1
        if '理解' in text or '认知' in text:
            score += 1
        return min(score, 3)